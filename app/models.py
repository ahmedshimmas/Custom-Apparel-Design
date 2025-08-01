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
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(_('Email'), unique=True, error_messages={'email': 'email must be unique'})
    password = models.CharField(max_length=128)
    consent = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)

    #profile model
    profile_picture = models.ImageField(upload_to='user/profile_pictures', blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)

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




class ApparelProduct(models.Model):

    product_name = models.CharField(max_length=50)
    sizes_available = models.CharField(max_length=5, choices=ProductSizes.choices, default=ProductSizes.MEDIUM)
    color_options = models.CharField(max_length=100)
    print_methods_supported = models.CharField(max_length=10, choices=ProductPrintMethods.choices, default=ProductPrintMethods.EMBROIDARY)
    description = models.TextField()
    upload_image = models.ImageField(upload_to='admin/product/thumbnails/')
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product_name




class PricingRules(models.Model):

    product_name = models.OneToOneField(ApparelProduct, on_delete=models.CASCADE, related_name='pricing_rule')
    base_price = models.DecimalField(max_digits=6, decimal_places=2)

    ai_design_cost = models.DecimalField(max_digits=6, decimal_places=2, default=2.00)
    custom_design_upload_cost = models.DecimalField(max_digits=6, decimal_places=2, default=1.00)
    print_cost = models.DecimalField(max_digits=6, decimal_places=2, default=8.00)

    def __str__(self):
        return f'{self.product_name} - {self.base_price}'




class UserDesign(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')

    #upload your art work
    product = models.ForeignKey(ApparelProduct, on_delete=models.CASCADE, related_name='user_designs')
    design_type = models.CharField(max_length=10, choices=UserDesignType.choices, default=UserDesignType.AI_GENERATED)
    prompt = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='user/product-design/images/')
    created_at = models.DateTimeField(auto_now_add=True)

    is_draft = models.BooleanField(default=False)


    def calculate_price(self):

        pricing_rule = self.product.pricing_rule
        cost = pricing_rule.base_price + pricing_rule.print_cost
        
        if self.design_type == 'ai':
            cost += pricing_rule.ai_design_cost
        else:
            cost += pricing_rule.custom_design_upload_cost
        
        return cost


    def __str__(self):
        return f'Product {self.id} - User: {self.user.id}'




class ShippingAddress(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_address')

    full_name = models.CharField(max_length=69)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    street_address = models.TextField()
    city = models.CharField(max_length=128)
    postal_code = models.CharField(max_length=10)
    province_state = models.CharField(max_length=69)  
    country = models.CharField(max_length=50)

    is_default = models.BooleanField(default=False)

    
    def save(self, *args, **kwargs):
        
        #set the first address as default automatically
        if not ShippingAddress.objects.filter(user=self.user).exists():
            self.is_default = True

        #if user sets another address as default, then update the previous default address and change it to is_default=False automatically
        if self.is_default:
            ShippingAddress.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
            #we used .exclude here because without it the current instance we are trying we set as default will also be fetched and updated as false, so we exclude the current object from this query

        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f'User {self.user.get_full_name()} Shipping Address'




class BillingAdress(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='billing_address')

    full_name = models.CharField(max_length=69)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    street_address = models.TextField()
    city = models.CharField(max_length=128)
    postal_code = models.CharField(max_length=10)
    province_state = models.CharField(max_length=69)  
    country = models.CharField(max_length=50)

    is_default = models.BooleanField(default=False)

    
    def save(self, *args, **kwargs):
        
        if not BillingAdress.objects.filter(user=self.user).exists():
            self.is_default = True

        if self.is_default:
            BillingAdress.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)

        return super().save(*args, **kwargs)

    def __str__(self):
        return f'User {self.user.get_full_name()} Billing Address'



#ask frontend about My Orders page, what data will he handle, and what we will

class Order(models.Model):  

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(UserDashboard, on_delete=models.CASCADE, related_name='orders')

    order_id = models.CharField(max_length=8, blank=True, null=True, unique=True)
    payment = models.CharField(max_length=12, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PROCESSING)
    is_active = models.BooleanField(default=True)
    order_date = models.DateField(auto_now_add=True)

    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'Order {self.id} - {self.user.full_name}'

    def save(self, *args, **kwargs):
        if not self.order_id:
            last_order = Order.objects.filter('id').last()
            if last_order and last_order.order_id:
                try:
                    last_id = int(last_order.order_id.split('-')[1])
                except:
                    last_id = 100
            else:
                last_id = 100
            new_id = last_id + 1
            self.order_id = f'A-{new_id}'
        return super().save(*args, **kwargs)

class PricingRules(models.Model):
    
    #price per product
    product_name = models.CharField(max_length=10, choices=ApparelType.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    screen_printing = 5


    def __str__(self):
        return f"{self.product_name} = ${self.price}"   