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




class ShippingAdressSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ShippingAddress
        fields = '__all__'




class PatchUserProfileSerializer(serializers.ModelSerializer):

    new_email = serializers.EmailField(write_only=True, required = False)
    new_phone = serializers.CharField(write_only=True, required = False)
    new_first_name = serializers.CharField(write_only=True, required = False)
    new_last_name = serializers.CharField(write_only=True, required = False)
    shipping_address = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'profile_picture',
            'new_first_name',
            'new_last_name',
            'new_email',
            'new_phone'
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


    def update(self, instance, validated_data):

        updatable_fields = {
            'new_first_name': 'first_name',
            'new_last_name': 'last_name',
            'new_email': 'email',
            'new_phone_number': 'phone_number',
            'new_country': 'country'
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




class UserDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = [
            'user', 
            'apparel',
            'design_type',
            'text',
            'print_method',
            'size',
            'color'
            ]
        read_only_fields = ['user']




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




class PricingRulesSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.PricingRules
        fields = '__all__'