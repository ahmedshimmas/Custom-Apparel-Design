from django.db import models
from django.contrib.auth.models import AbstractUser
from .choices import *
from django.utils import timezone
from datetime import timedelta
import random
import string
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):

    #register model
    role = models.CharField(choices=UserRoleChoices.choices, max_length=6, default=UserRoleChoices.USER)
    email = models.EmailField(_('Email'), unique=True, error_messages={'email': 'email must be unique'})
    password = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=15)
    consent = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)


    #profile model
    profile_picture = models.ImageField(upload_to='resume/profile_pictures', blank=True, null=True)
    full_name = models.CharField(max_length=50, blank=True, null=True)

    #shipping_address
    street_addr = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=128, null=True, blank=True)
    postal_code = models.IntegerField(null=True, blank=True)
    province_state = models.CharField(max_length=128, null=True, blank=True)  
    country = models.CharField(max_length=50, null=True, blank=True)

    #notification settings
    order_confirmation_email = models.BooleanField(default=False, null=True, blank=True)
    payment_success_notification = models.BooleanField(default=False, null=True, blank=True)
    shipping_delivery_updates = models.BooleanField(default=False, null=True, blank=True)
    AI_design_approvals_alerts = models.BooleanField(default=False, null=True, blank=True)
    account_activity_alerts = models.BooleanField(default=False, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    welcome_message = _(
        'Hi, {name}\n'
        'Here is your OTP for registration: {otp}\n'
        'This OTP is valid only for 10 minutes, after that you will need to resent OTP.'
    )

    forget_password_message = _(
        'Hi {name}, you have requested for a password reset for your CAD account.\n'
        'Here is your OTP for password reset: {otp}\n'
        'This OTP is valid only for 10 minutes, after that you will need to resend OTP.'
    )

    def generate_otp(self):
        otp = ''.join(random.choices(string.digits, k=6))
        self.otp = otp
        self.otp_expiry = timezone.now() + timedelta(minutes=10)
        self.save()

    def __str__(self):
        return self.username


class Product(models.Model):

    #ask frontend which fields do we need to save and return

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')

    #upload your art work
    design = models.FileField(upload_to='product/', null=True, blank=True)
    text = models.CharField(blank=True, null=True)
    style = models.CharField(max_length=2, choices=ProductStyle.choices, default=ProductStyle.EMBROIDARY)
    size = models.CharField(max_length=3, choices=ProductSize.choices, default=ProductSize.SMALL)
    color = models.CharField(blank=True, null=True)

    def __str__(self):
        return f'Product {self.id} - User: {self.user.id}'


#ask frontend about My Orders page, what data will he handle, and what we will