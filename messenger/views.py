import json
import logging
import os
import hmac
import hashlib
import requests
import mimetypes
from urllib.parse import quote
from woocommerce import API
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, redirect
from django.conf import settings

from core.ai import AI
from core.models import FacebookPage, User, Questions, Order, WebhookLog, Notification, WooConnection

from .models import Message, Conversation
from .messenger import Messenger
from .reader import Reader

from .generater import *

# from core.chroma import ChromaDB
from .utils import generate_conversation, cache_file
from core.utils import days_ago


logging.basicConfig(level=logging.DEBUG, filename='.log',)
logger = logging.getLogger(__name__)


def process_event(event: dict, request):  
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
    if not page.enabled:
        return False
    
    access_token = page.access_token
    
    # initialize tools
    messenger = Messenger(access_token, sender_id, recipient_id)
    ai = AI(page.id, settings.GEMINI_API_KEY)
    reader = Reader(ai)
    
    # wcapi = API(
    #     url="https://dotshirt.kesug.com/",
    #     consumer_key="ck_cc896e64781f95a3cbe14ec4d98789c73dda310d",
    #     consumer_secret="cs_424b72a7555e92d65cbab456fe7383ceff36fae3",
    #     version="wc/v3"
    # )
    woo = WooConnection.objects.filter(facebook_page=page).first()
    has_woo = woo is not None and woo.connected
    
    if has_woo:
        wcapi = API(
            url=page.woo.store_url,
            consumer_key=page.woo.consumer_key,
            consumer_secret=page.woo.consumer_secret,
            version="wc/v3"
        )
    
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
        
        if payload.startswith("BUY_WOOCOMMERCE_PRODUCT_ID:"):
            product_id = payload.split("ID:")[1]
            product = wcapi.get("products/"+product_id).json()
            user_text += str(translate_woocommerce_products([product]))
            
        Message.objects.create(
            mid=event["postback"].get("mid"),
            conversation=conversation,
            role="user",
            content=user_text,
        )        
    
    if not page.user.has_credits(page.credits_per_reply()):
        page.user.notify(
            message=f'You don\'t have enough credits to reply.',
            type='error',
            action_text="Buy more",
            action_url="/buy-credits/",
        )
        logger.info(f"User {page.user} has not enough credits to reply. Skipping...")
        return True
    
    can_reply, reason = conversation.can_reply()
    if not can_reply:
        logger.info(reason)
        return True
    
    history = generate_conversation(conversation)
    
    # chroma = ChromaDB(page)
    # query_text = ai.generate_query_text(history[-8:])
    # print("Q:", query_text)
    # context = chroma.query(query_text, k=5)
    # print("C:", context)
    
    messenger.send_action("mark_seen")
    print("started...")
    
    context = [page.business_context]
    
    reply = ai.reply(history, context)
    print("finished...")

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
    
    i = 0
    while i < len(reply_json):
        reply_part = reply_json[i]
        i += 1
        
        tool = reply_part.get('tool')
        
        # internal tools
        if tool == 'block':
            conversation.blocked = True
            conversation.save()
            logger.info("Blocking conversation...")
            continue
            
        elif tool == 'alert':
            # Questions.objects.get_or_create(
            #     page = page,
            #     question = reply_part.get('question'),
            # )
            #TODO: save alert for admin
            continue
        
        elif tool == 'place_order':
            Order.objects.get_or_create(
                page = page,
                **reply_part.get('params')
            )
            
            #TODO: more logic
            reply_part = generate_receipt(reply_part.get('params'))
            continue
        
        # external tools
        elif tool == 'send_text':
            reply_part = generate_text(reply_part["params"]["text"])
            
        elif tool == 'send_attachment':
            reply_part = generate_attachment(**reply_part["params"])
            
        elif tool == 'send_quick_replies':
            reply_part = generate_quick_replies(**reply_part["params"])
        
        elif tool == 'send_woo_products':
            if not has_woo:
                logger.info("WooCommerce is not connected. Skipping...")
                continue
            params={"per_page": 10}
            if "search_query" in reply_part["params"]:
                params["search"] = reply_part["params"]["search_query"]
                
            p = wcapi.get("products", params=params).json()
            
            reply_part = translate_woocommerce_products(p)
            reply_part = generate_products(reply_part)
        
        elif tool == 'send_products':
            reply_part = generate_products(reply_part["params"]["products"])
        
        # elif tool == 'send_receipt':
        #     reply_part = generate_receipt(receipt=reply_part["receipt"])
        
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
            message='You have low credits.',
            type='warning',
            action_text="Buy more",
            action_url="/buy-credits/",
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
    APP_SECRET = settings.FB_APP_SECRET
    
    if not verify_signature(request, APP_SECRET):
        logger.warning("Signature verification failed.")
        return HttpResponseForbidden("Signature verification failed.")

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
                    if process_event(event, request):
                        return JsonResponse({"success": True})
                except Exception as e:
                    # Catch errors in single event processing to not fail the whole batch
                    logger.error(f"Error processing event: {data}. Exception: {e}", exc_info=True)
                    
        
                    
    return JsonResponse({"success": True})