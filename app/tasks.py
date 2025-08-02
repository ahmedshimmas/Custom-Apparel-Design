from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
# from django.utils import timezone
# from datetime import timedelta
# from rest_framework.response import Response

from app.models import User
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def send_welcome_otp(user_id):
    try:
        user = User.objects.get(id=user_id)
    except Exception as e:
        return "user not found"
    
    user.generate_otp()        

    subject = 'CAD - OTP REQUEST'
    message = user.welcome_message.format(
        name = user.username,
        otp = user.otp
    )
    from_email = settings.EMAIL_HOST_USER
    to_email = [user.email]
    send_mail(
        subject, 
        message, 
        from_email, 
        to_email,
        fail_silently=False
        )


@shared_task
def password_reset_otp(email):
    try:
        user = User.objects.get(email=email)
    except Exception as e:
        return "user not found with this email"

    user.generate_otp()  

    print(user.email, user.username, user.otp, user.otp_expiry)      

    subject = 'CAD - PASSWORD RESET REQUEST'
    message = user.forget_password_message.format(
        name = user.username,
        otp = user.otp
    )
    from_email = settings.EMAIL_HOST_USER
    to_email = [user.email]
    send_mail(
        subject, 
        message, 
        from_email, 
        to_email,
        fail_silently=False
        )