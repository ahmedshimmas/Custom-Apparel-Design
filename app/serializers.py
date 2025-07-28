from rest_framework import serializers
from rest_framework.validators import ValidationError
from app import models
from app.tasks import send_welcome_otp, password_reset_otp
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.utils import timezone

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
            'username',
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
        user.is_active = False
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

# class ResetPasswordRequestSerializer(serializers.Serializer):
    
#     email = serializers.EmailField()
    
#     def save(self, **kwargs):
#         email = self.validated_data['email']
#         try:
#             User.objects.get(email=email)
#             password_reset_otp.delay(email)
#         except models.User.DoesNotExist:
#             raise ValidationError({
#                 'email': 'user with this email does not exist'
#             })


    
# class ResetPasswordSerializer(serializers.ModelSerializer):
#     new_password = serializers.CharField()
#     confirm_password = serializers.CharField()
#     class Meta:
#         model = User
#         fields = [
#             'email', 
#             'new_password',
#             'confirm_password'
#             ]
    
#     def validate(self, attrs):
#         if attrs['new_password'] != attrs['confirm_password']:
#             raise ValidationError({'confirm_password': 'passwords do not match'})
#         return super().validate(attrs)
    
#     def update(self, instance, validated_data):
#         instance.set_password(validated_data['new_password'])
#         instance.save()
#         return instance

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
    class Meta:
        model = User
        fields = [
            'profile_picture',
            'first_name',
            'last_name',
            'email',
            'phone_number'
        ]

class PatchUserShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'street_addr',
            'city',
            'postal_code',
            'province_state',
            'country'
        ]

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



class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = [
            'user', 
            'apparel',
            'design_type',
            'text',
            'print_method',
            'size',
            'color',
            ]

class OrderSerializer(serializers.ModelSerializer):
    design_type = serializers.CharField(source='product.design_type', read_only=True)
    apparel = serializers.CharField(source='product.apparel', read_only=True)
    color = serializers.CharField(source='product.color', read_only=True)
    print_method = serializers.CharField(source='product.print_method', read_only=True)

    class Meta:
        model = models.Order
        fields = [
            'customer',
            'product',
            'order_id',
            'quantity',
            'payment',
            'status',
            'order_date',
            'design_type',
            'apparel',
            'color',
            'print_method'
        ]
        read_only_fields = ['order_id']
    
