from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from project import settings
from celery import shared_task
from app import models

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@shared_task
def send_login_email(user_email):
    subject = "Login Alert - CAD"
    message = "You have successfully logged in to your account."
    sender = settings.EMAIL_HOST_USER
    to_email = [user_email]
    send_mail(
        subject,
        message,
        sender,
        to_email,
        fail_silently=False,
    )

@shared_task
def login_failed_email(user):
    subject = "Login Failed Alert - CAD"
    message = "There was a failed login attempt to your account. If this wasn't you, please reset your password immediately."
    sender = settings.EMAIL_HOST_USER
    to_email = [user.email]
    send_mail(
        subject,
        message,
        sender,
        to_email,
        fail_silently=False,
    )

@shared_task
def send_logout_email(user):
    subject = "Logout Alert - CAD"
    message = "You have successfully logged out of your account."
    sender = settings.EMAIL_HOST_USER
    to_email = [user.email]
    send_mail(
        subject,
        message,
        sender,
        to_email,
        fail_silently=False,
    )

@shared_task
def send_order_confirmation_email(user, order):
    subject = "Order Confirmation - CAD"
    message = f"Thank you for your order #{order.id}. We are processing it and will update you once it's shipped."
    sender = settings.EMAIL_HOST_USER
    to_email = [user.email]
    send_mail(
        subject,
        message,
        sender,
        to_email,
        fail_silently=False,
    )

@shared_task
def payment_success_email(user, order):
    subject = "Payment Successful - CAD"
    message = f"Your payment for order #{order.id} was successful. Thank you for shopping with us!"
    sender = settings.EMAIL_HOST_USER
    to_email = [user.email]
    send_mail(
        subject,
        message,
        sender,
        to_email,
        fail_silently=False,
    )

@shared_task
def shipping_delivery_updated(user, order, status):
    subject = f"Order #{order.id} - {status}"
    message = f"Your order #{order.id} status has been updated to: {status}."
    sender = settings.EMAIL_HOST_USER
    to_email = [user.email]
    send_mail(
        subject,
        message,
        sender,
        to_email,
        fail_silently=False,
    )

@shared_task
def ai_design_alerts(user, design_details):
    subject = "Your AI-Generated Design is Ready - CAD"
    message = f"Hello {user.username}, your AI-generated design is ready! Details: {design_details}"
    sender = settings.EMAIL_HOST_USER
    to_email = [user.email]
    send_mail(
        subject,
        message,
        sender,
        to_email,
        fail_silently=False,
    )