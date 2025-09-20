from django.contrib.auth.signals import user_logged_in, user_login_failed, user_logged_out
from django.dispatch import receiver
from .utils import send_login_email, login_failed_email, send_logout_email
from .models import User, Order


@receiver(user_logged_in)
def handle_user_logged_in(sender, request, user, **kwargs):
    send_login_email.delay(user.email)


@receiver(user_login_failed)
def handle_user_login_failed(sender, credentials, **kwargs):
    try:
        user = User.objects.get(email=credentials.get('username'))
        login_failed_email.delay(user)
    except User.DoesNotExist:
        pass 


@receiver(user_logged_out)
def handle_user_logged_out(sender, request, user, **kwargs):
    send_logout_email.delay(user)