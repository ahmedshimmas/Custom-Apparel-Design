from django.db import models
from django.contrib.auth.models import AbstractUser
from .choices import *
from django.utils import timezone
from datetime import timedelta
import random
import string
from django.utils.translation import gettext_lazy as _
# import uuid


class User(AbstractUser):

    user_id = models.CharField(max_length=10 , unique=True , null=True ,blank=True)

    #register model
    role = models.CharField(choices=UserRoleChoices.choices, max_length=6, default=UserRoleChoices.USER)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    username = models.CharField(max_length=50, blank=True)
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
    created_at = models.DateTimeField(auto_now_add=True)

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

    def save(self, *args, **kwargs):
        if not self.user_id:
            last_user = User.objects.order_by('-id').first()  

            if last_user and last_user.user_id:
                try:
                    last_id = int(last_user.user_id.split('-')[1])
                except (IndexError, ValueError):
                    last_id = 100
            else:
                last_id = 100

            new_id = last_id + 1
            self.user_id = f'U-{new_id}'

        super().save(*args, **kwargs)  



    def __str__(self):
        return self.username




class ApparelProduct(models.Model):

    product_uid = models.CharField(unique=True, blank=True, null=True)
    product = models.OneToOneField('PricingRules', on_delete=models.CASCADE, blank=True, null=True)
    
    sizes_available = models.ManyToManyField('Size', related_name='apparel_sizes')
    color_options = models.CharField(max_length=100)
    description = models.TextField()
    upload_image = models.ImageField(upload_to='admin/product/thumbnails/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    
    def save(self, *args, **kwargs):
        if not self.product_id:
            last_product = ApparelProduct.objects.order_by('-id').first()  

            if last_product and last_product.product_id:
                try:
                    last_id = int(last_product.product_id.split('-')[1])
                except (IndexError, ValueError):
                    last_id = 100
            else:
                last_id= 100

            new_id = last_id + 1
            self.product_id = f'P-{new_id}'

        super().save(*args, **kwargs)  


    def __str__(self):
        return self.product.get_product_name_display() if self.product else "Unnamed in PricingRules"


class Size(models.Model):

    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class PricingRules(models.Model):

    product_name = models.CharField(choices=ProductChoices)
    base_price = models.DecimalField(max_digits=6, decimal_places=2)
    printing_method = models.CharField(choices=ProductPrintMethods.choices, default=ProductPrintMethods.embroidary)

    ai_design_cost = models.DecimalField(max_digits=6, decimal_places=2, default=2.00)
    custom_design_upload_cost = models.DecimalField(max_digits=6, decimal_places=2, default=1.00)
    print_cost = models.DecimalField(max_digits=6, decimal_places=2, default=8.00)

    class Meta:
        verbose_name = 'Pricing Rule'
        verbose_name_plural = 'Pricing Rules'

    def __str__(self):
        return f'{self.product_name} - {self.base_price}'

  # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     size = instance.sizes_available
    #     data['sizes_available'] = [
    #             {
    #                 'size_id': size.id,
    #                 'size_name': size.name
    #             }
    #             for size in instance.sizes_available.all()
    #         ]
    #     return data


class UserDesign(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='designs')

    #upload your art work
    apparel = models.ForeignKey(ApparelProduct, on_delete=models.CASCADE, related_name='user_designs')
    design_type = models.CharField(max_length=10, choices=UserDesignType.choices, default=UserDesignType.AI_GENERATED)

    prompt = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='user/product-design/images/', null=True, blank=True)

    font = models.CharField(max_length=30, blank=True, null=True)
    style = models.CharField(max_length=20, choices=ProductPrintMethods.choices, default=ProductPrintMethods.embroidary)
    shirt_size = models.CharField(max_length=20, choices=ProductSizes.choices, default=ProductSizes.SMALL)
    color = models.CharField(max_length=30, default='black')

    created_at = models.DateTimeField(auto_now_add=True)
    is_draft = models.BooleanField(default=False)


    @property
    def calculate_price(self):
        
        if not hasattr(self.product, 'pricing_rule') or not self.product.pricing_rule:
            raise ValueError(f"PricingRule not found for product ID {self.product.id}")

        pricing_rule = self.product.pricing_rule
        cost = pricing_rule.base_price + pricing_rule.print_cost
        
        if self.design_type == UserDesignType.AI_GENERATED:
            cost += pricing_rule.ai_design_cost
        else:
            cost += pricing_rule.custom_design_upload_cost
        
        return cost


    def __str__(self):
        return f'Product {self.id} - User: {self.user.id}'




class ShippingAddress(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shipping_address')

    full_name = models.CharField(max_length=69)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    street_address = models.TextField()
    city = models.CharField(max_length=128)
    postal_code = models.CharField(max_length=10)
    province_state = models.CharField(max_length=69)  
    country = models.CharField(max_length=50)


    class Meta:
        verbose_name = 'Shipping Address'
        verbose_name_plural = 'Shipping Addresses'

    
    def __str__(self):
        return f'User {self.user.get_full_name()} Shipping Address'




class BillingAddress(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='billing_address')

    full_name = models.CharField(max_length=69)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    street_address = models.TextField()
    city = models.CharField(max_length=128)
    postal_code = models.CharField(max_length=10)
    province_state = models.CharField(max_length=69)  
    country = models.CharField(max_length=50)



    class Meta:
        verbose_name = 'Billing Address'
        verbose_name_plural = 'Billing Addresses'


    def __str__(self):
        return f'User {self.user.get_full_name()} Billing Address'




class Order(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_orders')
    user_design = models.ForeignKey(UserDesign, on_delete=models.CASCADE, related_name='design_orders')
    shipping_address = models.OneToOneField(ShippingAddress, on_delete=models.SET_NULL, null=True, related_name='shipping_orders')

    order_id = models.CharField(max_length=10, unique=True)

    design_type = models.CharField(max_length=20)
    apparel = models.ForeignKey(ApparelProduct, on_delete=models.SET_NULL, null=True)
    color = models.CharField(max_length=20) 
    print_method = models.CharField(max_length=20) 
    quantity = models.IntegerField(default=1)
    date = models.DateField(auto_now_add=True)
    payment = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)

    order_status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PROCESSING)
    order_tracking_status = models.CharField(max_length=20, choices=OrderTrackingStatus.choices, default=OrderTrackingStatus.ORDER_PLACED)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    from decimal import Decimal
    discount_applied = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    shipping_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('10.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    estimated_delivery_date = models.DateTimeField(default=timezone.now() + timedelta(days=5))

    def calculate_price(self):
        try:
            pricing = self.apparel.product
            base_price = self.apparel.product.base_price if self.apparel.product.base_price else 0
        except PricingRules.DoesNotExist:
            base_price = None

        # base_price = pricing.base_price if pricing else 0
        ai_cost = pricing.ai_design_cost if self.design_type == 'ai' and pricing is not None  else 0
        upload_cost = pricing.custom_design_upload_cost if self.design_type == 'upload' else 0
        print_cost = pricing.print_cost

        # Calculate price for one item
        per_item_price = base_price + ai_cost + upload_cost + print_cost

        self.subtotal = per_item_price * self.quantity
        self.total_amount = self.subtotal - self.discount_applied + self.shipping_fee

    def save(self, *args, **kwargs):

        if not self.order_id:
            last_order = Order.objects.order_by('id').last()
            if last_order and last_order.order_id:
                try:
                    last_id = int(last_order.order_id.split('-')[1])
                except:
                    last_id = 100
            else:
                last_id = 100
            new_id = last_id + 1
            self.order_id = f'A-{new_id}'


        # Auto-update order_status based on tracking status
        if self.order_tracking_status == 'delivered':
            self.order_status = OrderStatus.COMPLETED
        elif self.order_status != OrderStatus.CANCELLED:  # don't override if manually cancelled
            self.order_status = OrderStatus.PROCESSING
        print(self.order_status)
        self.calculate_price()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.pk} - {self.order_status}"