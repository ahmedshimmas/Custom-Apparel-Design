from rest_framework import serializers
from rest_framework.validators import ValidationError
from app import models
from app.tasks import send_welcome_otp
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone
# from django.contrib.auth.hashers import check_password
# from django.utils import timezone

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = [
            'role',
            'first_name',
            'last_name',
            'phone_number',
            'email',
            # 'username',
            'password',
            'confirm_password',
            'consent'
                ]
        extra_kwargs = {
                'password': {'write_only': True},
            }

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise ValidationError({'confirm_password': 'passwords do not match'})
    
        if attrs.get('consent') == False:
            raise ValidationError({'consent': 'You must accept terms and conditions to continue.'})
        
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('confirm_password')
        user = User(**validated_data)
        user.set_password(password)
        user.username = user.email
        user.is_active = False
        if user.role == 'admin':
            user.is_staff = True
        user.save()
        send_welcome_otp.delay(user.id)
        return user
    


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self, **kwargs):
        email = self.validated_data['email']
        try:
            user = User.objects.get(email=email)
            user.otp = ''
            user.otp_expiry = None
            send_welcome_otp.delay(user.id)
        except User.DoesNotExist:
            raise ValidationError(
                {'email': 'user with this email does not exist'},
                code='user_not_found'
                )
    


class VerifyOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'otp']



class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()



class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()



class ChangePasswordSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    class Meta:
        model = User
        fields = [
            'current_password',
            'new_password',
            'confirm_password',
            ]
    
    def validate(self, attrs):

        user = self.instance
        
        if not user.check_password(attrs['current_password']):
            raise ValidationError({'current_password': 'current password is incorrect'})
        
        if attrs['new_password'] != attrs['confirm_password']:
            raise ValidationError({'confirm_password': 'passwords do not match'})

        return attrs
    
    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance



class PatchUserProfileSerializer(serializers.ModelSerializer):

    new_email = serializers.EmailField(required = False)
    new_phone_number = serializers.CharField(required = False)
    shipping_address = serializers.SerializerMethodField()
    # billing_address = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'profile_picture',
            'first_name',
            'last_name',
            'new_email',
            'new_phone_number',
            'country',
            'shipping_address',
            # 'billing_address'
        ]

    def get_shipping_address(self, instance):

        default = models.ShippingAddress.objects.filter(user=self.context['request'].user, is_default=True).first() #returns an instance or None
        
        if default:
            return {
                'full_name': default.full_name,
                'phone_number': default.phone_number,
                'email': default.email,
                'street_address': default.street_address,
                'city': default.city,
                'postal_code': default.postal_code,
                'province_state': default.province_state,
                'country': default.country
            }
        return None
    

    # def get_billing_address(self, instance):

    #     default = models.BillingAddress.objects.filter(user=self.context['request'].user, is_default=True).first() #returns an instance or None

    #     if default:
    #         return {
    #             'full_name': default.full_name,
    #             'phone_number': default.phone_number,
    #             'email': default.email,
    #             'street_address': default.street_address,
    #             'city': default.city,
    #             'postal_code': default.postal_code,
    #             'province_state': default.province_state,
    #             'country': default.country
    #         }
    #     return None


    def update(self, instance, validated_data):

        updatable_fields = {
            'profile_picture': 'profile_picture',
            'first_name': 'first_name',
            'last_name': 'last_name',
            'country': 'country',
            'new_email': 'email',
            'new_phone_number': 'phone_number'
        }
        for new_fields, model_fields in updatable_fields.items():
            new_value = validated_data.pop(new_fields, None)
            if new_value is not None:
                setattr(instance, model_fields, new_value)

        instance.save()
        
        return super().update(instance, validated_data)



class PatchUserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'order_confirmation_email',
            'payment_success_notification',
            'shipping_delivery_updates',
            'AI_design_approvals_alerts',
            'account_activity_alerts'
        ]

class ApparelProductSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.ApparelProduct
        fields = [
            'id',
            'product_name',
            'sizes_available',
            'color_options',
            'print_methods_supported',
            'description',
            'upload_image',
            'is_active',
            'created_at'
        ]
    
    def to_representation(self, instance):
        data = super().to_representation(instance) #instance is a serialized dict now
        data['sizes_available'] = [
            str(name) for name in instance.sizes_available.all()
        ]
        return data

class PricingRuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.PricingRules
        fields = [
            'id',
            'product_name',
            'base_price',
            'print_cost',
            'ai_design_cost',
            'custom_design_upload_cost'
        ]



class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Size
        fields = '__all__'
        ordering = ['name']



class UserDesignSerializer(serializers.ModelSerializer):

    # quantity = serializers.IntegerField()

    class Meta:
        model = models.UserDesign
        fields = [
            'user', 
            'apparel',
            'design_type',
            'prompt',
            'image',
            'font',
            'style',
            'shirt_size',
            'color',
            'calculate_price',
            'created_at',
            'is_draft',
            # 'quantity'
            ]
        read_only_fields = [
            'user', 
            'created_at', 
            ]
    
    def create(self, validated_data):
        
        user = self.context['request'].user
        validated_data['user'] = user

        if not validated_data.get('is_draft', True):
            if not hasattr(user, 'shipping_address'):
                raise serializers.ValidationError({'detail': 'Shipping address not found for this user.'})

        # quantity = validated_data.pop('quantity')

        # Save the design
        design = super().create(validated_data)

        # If it's not a draft, auto-create an order
        if not design.is_draft:
            models.Order.objects.create(
                user=user,
                user_design=design,
                shipping_address=user.shipping_address,
                design_type=design.design_type,
                apparel=design.apparel,
                color=design.color,
                print_method=design.style,
                # quantity=quantity,
                estimated_delivery_date=timezone.now() + timedelta(days=5),
                subtotal=0,  # Will be calculated in save()
                total_amount=0,
            )

        return design



class ShippingAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ShippingAddress
        fields = '__all__'
        read_only_fields = ['user']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)



class BillingAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BillingAddress
        fields = '__all__'
        read_only_fields = ['user']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)



class OrderCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Order
        fields = [
            'user',
            'user_design',
            'shipping_address',
            'order_id',
            'design_type',
            'apparel',
            'color',
            'print_method',
            'quantity',
            'date',
            'payment',
            'order_status',
            'order_tracking_status',
            'subtotal',
            'discount_applied',
            'shipping_fee',
            'total_amount',
            'created_at',
            'estimated_delivery_date'
        ]
        read_only_fields = [
            'user',
            'order_id',
            'design_type',
            'color',
            'print_method',
            'subtotal',
            'discount_applied',
            'shipping_fee',
            'total_amount'
        ]
    
    
    def create(self, validated_data):

        user = self.context['request'].user
        user_design = validated_data.get('user_design')
        apparel = validated_data.get('apparel')

        validated_data['user'] = user
        validated_data['design_type'] = user_design.design_type
        validated_data['color'] = apparel.color_options
        validated_data['print_method'] = apparel.print_method
        validated_data['estimated_delivery_date'] = timezone.now().date() + timedelta(days=5)

        return models.Order.objects.create(**validated_data)



class OrderListSerializer(serializers.ModelSerializer):
    
    class Meta:
        models = models.Order
        fields = '__all__'