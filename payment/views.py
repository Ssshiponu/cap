import uuid
import json
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from .models import BkashTransaction
from .client import BkashClient

client = BkashClient()

def generate_order_id():
    return str(uuid.uuid4())

def payment(request):
    return render(request, "payment/checkout.html")

def bkash_checkout(request):
    """
    Initiate the payment: create transaction, get bKash create response.
    """
    user = request.user if request.user.is_authenticated else None
    # You might get amount and order from cart, etc.
    amount = 100.00  # example
    order_id = generate_order_id()

    # create transaction record
    tx = BkashTransaction.objects.create(
        order_id=order_id,
        user=user,
        amount=amount,
    )

    # get token
    token_resp = client.get_token()
    if not token_resp.get("id_token"):
        return JsonResponse({"error": "token failure", "details": token_resp}, status=500)
    token = token_resp["id_token"]

    # create payment
    create_resp = client.create_payment(order_id=order_id, amount=amount, token=token)
    # store raw
    tx.raw_request = {"step": "create", "body": create_resp}
    tx.raw_response = create_resp
    tx.save()

    if "paymentID" not in create_resp:
        return JsonResponse({"error": "create failed", "details": create_resp}, status=500)

    payment_id = create_resp["paymentID"]
    tx.payment_id = payment_id
    tx.status = "created"
    tx.save()

    # In some flows, you might get a redirect URL, or instruct frontend to show popup
    return JsonResponse({
        "paymentID": payment_id,
        "bkashUrl": create_resp.get("bkashURL")  # if provided by API
    })

@csrf_exempt
def bkash_execute(request):
    """
    Execute after user confirms payment.
    """
    data = request.json if hasattr(request, "json") else {}  # parse JSON
    payment_id = data.get("paymentID")
    if not payment_id:
        return JsonResponse({"error": "missing paymentID"}, status=400)

    # fetch transaction
    try:
        tx = BkashTransaction.objects.get(payment_id=payment_id)
    except BkashTransaction.DoesNotExist:
        return JsonResponse({"error": "transaction not found"}, status=404)

    token_resp = client.get_token()
    if not token_resp.get("id_token"):
        return JsonResponse({"error": "token failure", "details": token_resp}, status=500)
    token = token_resp["id_token"]

    exec_resp = client.execute_payment(payment_id=payment_id, token=token)
    tx.raw_request = {"step": "execute", "body": exec_resp}
    tx.raw_response = exec_resp

    if exec_resp.get("statusCode") == "0000" or exec_resp.get("status") == "success":
        tx.status = "executed"
    else:
        tx.status = "failed"
    tx.save()

    return JsonResponse({
        "status": tx.status,
        "exec": exec_resp
    })


@csrf_exempt
def bkash_webhook(request):
    """
    Handle webhook / callback from bKash (if they support).
    """
    # parse JSON
    body = None
    try:
        body = json.loads(request.body)
    except:
        return HttpResponse(status=400)

    payment_id = body.get("paymentID")
    # etc. validate signature, then update your record
    # ...
    return HttpResponse(status=200)
