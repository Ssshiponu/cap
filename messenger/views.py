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

from core.ai import ai_reply
from core.models import FacebookPage, User

from .models import Message, Conversation
from .messenger import Messenger
from .reader import make_readable



logging.basicConfig(level=logging.DEBUG, filename='.log',)
logger = logging.getLogger(__name__)

        
def get_conversation_json(conv):
    """
    Return a json conversation list:
    [{"role": "user" or "assistant", "parts": [{"text": "..."}]}, ...]
    Messages are returned in chronological order (oldest first).
    """

    qs = (
        conv.messages.all()
        .order_by("created_at")
        .values("role", "content", "created_at")  # fetch only needed fields
    )

    conversation = []
    for row in qs:
        conversation.append({
            "role": row.get("role", ""),
            "parts": [{"text": row.get("content", "")}],
        })

    return conversation

def process_event(event: dict):
    sender_id = event.get("sender", {}).get("id")
    recipient_id = event.get("recipient", {}).get("id")
    
    access_token = get_object_or_404(FacebookPage, id=recipient_id).access_token
    api_key = os.environ.get("GENAI_API_KEY")
    
    if not sender_id or not recipient_id:
        return False
    
    messenger = Messenger(access_token, sender_id, recipient_id)
   
    message = event.get("message", {})
    if message.get("is_echo"):
        return False
    
    # get or create conversation
    conversation, _ = Conversation.objects.get_or_create(
        page_id=recipient_id, user_id=sender_id
    )
    # Case 1: User sent a standard message (text, attachment)
    if "message" in event:
        user_text = make_readable(event["message"], role="user", api_key=api_key)
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
    messenger.send_action("mark_seen")

    # --- Generate and Send AI Reply ---
    history = get_conversation_json(conversation)
    h = str(history[-20:])

    messenger.send_action("typing_on")
    reply = ai_reply(h, page_id=recipient_id, api_key = api_key)
    messenger.send_action("typing_off")
    for reply_part in reply:
        sent = messenger.send_reply(reply_part)
        
        if sent and "message_id" in sent:
            Message.objects.create(
                mid = sent['message_id'],
                conversation = conversation,
                role = "assistant",
                content = make_readable(reply_part, role="assistant"),
            )
        else:
            logger.error(f"Failed to send message: {reply_part}. Response: {sent}")
            
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