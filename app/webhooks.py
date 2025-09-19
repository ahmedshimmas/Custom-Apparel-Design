
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
import stripe
from app import models, choices
print(settings.STRIPE_WEBHOOK_KEY, '------------------')
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event = None 
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_KEY
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        print("babes")
        session = event["data"]["object"]
        # Find the order using session metadata
        order_id = session.get("metadata", {}).get("order_id")
        print("inside babes")
        if order_id:
            print("babes")
            order = models.Order.objects.get(id=order_id)
            print("----------",order.id)
            order.payment = choices.PaymentStatus.PAID
            order.save()
    if event["type"] == "payment_intent.payment_failed":
        print("failed")
        intent = event["data"]["object"]
        order_id = intent.get("metadata", {}).get("order_id")
        if order_id:
            order = models.Order.objects.get(id=order_id)
            order.payment = choices.PaymentStatus.FAILED
            order.save()        

    return HttpResponse(status=200)    