import json
import logging
import os
import hmac
import hashlib
import requests
import mimetypes

from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.conf import settings

from core.ai import AI
from core.models import FacebookPage, User, WebhookLog, Notification

from .models import Message, Conversation
from .messenger import Messenger
from .reader import Reader
from .utils import generate_conversation
from core.utils import days_ago


logging.basicConfig(level=logging.DEBUG, filename='.log',)
logger = logging.getLogger(__name__)


def process_event(event: dict):  
    message = event.get("message", {})
    
    # ignore echo messages
    if message.get("is_echo"):
        return False
    
    sender_id = event.get("sender", {}).get("id")
    recipient_id = event.get("recipient", {}).get("id")
    
    if not sender_id or not recipient_id:
        return False
    
    # get page
    page = get_object_or_404(FacebookPage, id=recipient_id)
    access_token = page.access_token
    
    # initialize tools
    messenger = Messenger(access_token, sender_id, recipient_id)
    ai = AI(page.id, settings.GEMINI_API_KEY)
    reader = Reader(ai)
    
    # get or create conversation
    conversation, _ = Conversation.objects.get_or_create(
        facebook_page=page, user_id=sender_id, active=True
    )
    
    # Case 1: User sent a standard message (text, attachment)
    if "message" in event:
        # make any action in readable text
        user_text = reader.make_readable(event["message"], role="user")
        Message.objects.create(
            mid=event["message"]["mid"],
            conversation=conversation,
            role="user",
            content=str(user_text),
        )

    # Case 2: User clicked a postback button (from quick replies, etc.)
    elif "postback" in event:
        payload = event["postback"].get("payload", "")
        title = event["postback"].get("title") or payload
        user_text = f'user clicked: "{title}" (payload: {payload})'

        Message.objects.create(
            mid=event["postback"].get("mid"),
            conversation=conversation,
            role="user",
            content=user_text,
        )        
    
    if not page.user.has_credits(page.credits_per_reply()):
        page.user.notify(
            message='No credits left',
            description=f'You have no credits left. Replies will not be sent until you <a class="link" href="/buy-credits">buy more credits</a>.',
            type='error'
        )
        logger.info(f"User {page.user} has not enough credits to reply. Skipping...")
        return True
    
    can_reply, reason = conversation.can_reply()
    if not can_reply:
        logger.info(reason)
        return True
    
    history = generate_conversation(conversation)
    
    messenger.send_action("mark_seen")
    print("started...")
    reply = ai.reply(history)

    if reply is None:
        return True


    conversation.input_tokens = conversation.input_tokens + reply.usage_metadata.prompt_token_count
    conversation.output_tokens = conversation.output_tokens + (reply.usage_metadata.candidates_token_count + reply.usage_metadata.thoughts_token_count)
    print('IN:',reply.usage_metadata.prompt_token_count, 'OUT:', reply.usage_metadata.candidates_token_count + reply.usage_metadata.thoughts_token_count)
    conversation.save()
    
    try:
        reply_json = json.loads(reply.text)
    except Exception as e:
        logger.error(f"Invalid AI response: {reply.text}")
        return True
        
    for reply_part in reply_json:
        if reply_part.get('action') == 'block':
            conversation.blocked = True
            conversation.save()
            logger.info("Blocking conversation...")
            break
        
        sent = messenger.send_reply(reply_part)
        
        if sent and "message_id" in sent:
            Message.objects.create(
                mid = sent['message_id'],
                conversation = conversation,
                role = "assistant",
                content = reader.make_readable(reply_part, role="assistant"),
                credits_used = page.credits_per_reply()
            )
            if not page.user.use_credits(page.credits_per_reply()):
                logger.info(f"User {page.user} has not enough credits to reply")
        else:
            logger.error(f"Failed to send message: {reply_part}. Response: {sent}")
            
    
    if page.user.is_low_credits():
        page.user.notify(
            message='Low credits',
            description=f'You have low credits left. <a class="link" href="/buy-credits">Buy credits</a> to continue using the service.',
            type='warning'
        )
    try:
        avrage_input_tokens = conversation.input_tokens / conversation.messages.filter(role="assistant").count()
        avrage_output_tokens = conversation.output_tokens / conversation.messages.filter(role="assistant").count() 
    except ZeroDivisionError:
        avrage_input_tokens = 0
        avrage_output_tokens = 0
        
    print('AV_IN:',avrage_input_tokens, 'AV_OUT:', avrage_output_tokens)
    
    return True

def verify_signature(request, app_secret) -> bool:
    """Verifies the Facebook webhook signature for security."""
    if not app_secret:
        logger.error("APP_SECRET is not configured. Signature verification failed.")
        return False
        
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    if not sig_header.startswith("sha256="):
        logger.warning(f"Invalid signature header format: {sig_header}")
        return False
        
    provided_signature = sig_header.split("=", 1)[1]
    
    app_secret_bytes = app_secret.encode('utf-8')
    expected_signature = hmac.new(app_secret_bytes, request.body, hashlib.sha256).hexdigest()
    
    return hmac.compare_digest(provided_signature, expected_signature)

@require_http_methods(["GET", "POST"])
@csrf_exempt
def webhook_view(request):
    """Main webhook endpoint for Facebook Messenger."""
    
    VERIFY_TOKEN = settings.FB_VERIFY_TOKEN

    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("Webhook verified successfully.")
            return HttpResponse(challenge, status=200)
        logger.warning(f"Webhook verification failed. Mode: {mode}, Token: {token}")
        return HttpResponseForbidden("Verification failed")

    elif request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in webhook request body.")
            return HttpResponse("Invalid JSON", status=400)

        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                try:
                    if process_event(event):
                        return JsonResponse({"success": True})
                except Exception as e:
                    # Catch errors in single event processing to not fail the whole batch
                    logger.error(f"Error processing event: {data}. Exception: {e}", exc_info=True)
                    
        
                    
    return JsonResponse({"success": True})