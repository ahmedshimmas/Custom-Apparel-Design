from rest_framework import serializers
from rest_framework.validators import ValidationError
from app import models
from app.tasks import send_welcome_otp
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from django.contrib.auth.hashers import check_password
# from django.utils import timezone

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom user data to the response
        data['user'] = {
            'id': self.user.id,
            'role': self.user.role,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'phone_number': self.user.phone_number,
            'email': self.user.email,
            'consent': self.user.consent,
            'is_superuser': self.user.is_superuser
        }

        return data

class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = [
            'id',
            'role',
            'first_name',
            'last_name',
            'phone_number',
            'email',
            'password',
            'confirm_password',
            'consent',
            'is_superuser'
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
        user.save()
        if user.is_superuser:
            user.is_active = True
            user.save()
        else:
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

    #shipping fields
    street_address = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    postal_code = serializers.CharField(required=False)
    province_state = serializers.CharField(required=False)


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
            'street_address',
            'city',
            'postal_code',
            'province_state'
        ]


    def get_shipping_address(self, instance):

        default = models.ShippingAddress.objects.filter(user=self.context['request'].user).first() #returns an instance or None
        
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
            'new_phone_number': 'phone_number',
        }
        for new_fields, model_fields in updatable_fields.items():
            new_value = validated_data.pop(new_fields, None)
            if new_value is not None:
                setattr(instance, model_fields, new_value)


        # Extract shipping fields from validated_data if they exist
        shipping_fields = ['street_address', 'city', 'postal_code', 'province_state']
        shipping_data = {field: validated_data.pop(field, None) for field in shipping_fields}

        # If any shipping field is provided, proceed to create/update shipping address, else skip the logic written below
        if any(value is not None for value in shipping_data.values()):
            
            user = instance  # current user

            # shipping_address=models.ShippingAddress.objects.filter(user=user,is_default=True).first() === WILL BE USED IF WE CHANGE RELATION TO FK INSTEAD OF 1TO1
            
            
            shipping_address = getattr(user, 'shipping_address', None)

            if shipping_address:

                for field, value in shipping_data.items():
                    if value is not None:
                        setattr(shipping_address, field, value)

                shipping_address.full_name = f'{user.first_name} {user.last_name}'
                shipping_address.phone_number = user.phone_number
                shipping_address.email = user.email
                shipping_address.country = user.country
                shipping_address.save()
            
            else: 
                models.ShippingAddress.objects.create(
                    user=user,
                    full_name=f'{user.first_name} {user.last_name}',
                    phone_number=user.phone_number,
                    email=user.email,
                    street_address=shipping_data.get('street_address', ''),
                    city=shipping_data.get('city', ''),
                    postal_code=shipping_data.get('postal_code', ''),
                    province_state=shipping_data.get('province_state', ''),
                    country=user.country,
                )

        instance.save()
        return instance



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
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    base_price = serializers.DecimalField(source='product.base_price', max_digits=4, decimal_places=2, read_only=True)
    print_methods = serializers.CharField(source='product.printing_method', read_only=True)
    
    class Meta:
        model = models.ApparelProduct
        fields = [
            'id',
            'product',
            'product_name',
            'base_price',
            'print_methods',
            'sizes_available',
            'color_options',
            'description',
            'upload_image',
            'is_active',
            'created_at'
        ]
    
    def validate(self, attrs):
        print(attrs)
        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        size = instance.sizes_available
        data['sizes_available'] = [
                {
                    'size_id': size.id,
                    'size_name': size.name
                }
                for size in instance.sizes_available.all()
            ]
        return data

class PricingRuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.PricingRules
        fields = [
            'id',
            'product_name',
            'base_price',
            'printing_method',
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

    order_quantity = serializers.IntegerField(write_only=True, required = False)

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
            'order_quantity'
            ]
        read_only_fields = [
            'user', 
            'created_at', 
            ]
    


    def validate(self, attrs):
        
        apparel = self.instance.apparel if self.instance else attrs.get('apparel')
        selected_size = attrs.get('shirt_size')

        if not apparel.sizes_available.filter(name=selected_size).exists():
            raise ValidationError({'detail':'no such size found for this apparel'})
        return attrs
    

    
    def create(self, validated_data):
        
        user = self.context['request'].user 
        validated_data['user'] = user 

        quantity = validated_data.pop('order_quantity', None)

        if not validated_data.get('is_draft', True):
            if not hasattr(user, 'shipping_address'):
                raise serializers.ValidationError({
                    'detail': 'Shipping address not found for this user.'
                    })
            if quantity is None:
                raise serializers.ValidationError({
                    'detail': 'quantity is required when ordering a design'
                })


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
                quantity=quantity,
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
        model = models.Order
        fields = '__all__'


#MS work------------------------------------DASHBOARD APIS----------------------------------------

class UserOrderSerializer(serializers.ModelSerializer):
    profile_picture = serializers.CharField(source = 'user.profile_picture' ,read_only = True)
    full_name = serializers.CharField(source = 'user.get_full_name', read_only=True)
    apparel_name = serializers.CharField(source = 'apparel.product_name' , read_only = True)

    class Meta:
        model = models.Order
        fields = [
            'profile_picture',
            'full_name',
            'design_type',
            'apparel_name',
            'print_method',
            'quantity',
            'created_at',
            'payment',
            'order_status'
        ]

    # def get_full_name(self ,obj):
    #     first = obj.user.first_name or ""
    #     second = obj.user.last_name or ""
    #     return f"{first} {second}".strip()
    

class ListOrderSerializer(serializers.ModelSerializer):
    design_type = serializers.CharField(source = 'product.design_type',read_only=True)
    full_name = serializers.ReadOnlyField(source="user.get_full_name")
    print_method = serializers.CharField(source='product.print_method', read_only=True)
    apparel_name = serializers.CharField(source = 'apparel.product_name' , read_only = True)

    
    class Meta:
        model = models.Order
        fields =[
            'order_id',
            'full_name',
            'design_type',
            'apparel_name',
            'color',
            'print_method',
            'quantity',
            'created_at',
            'payment',
            ]


    
class TrackOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source ='user.first_name' ,read_only = True)
    email = serializers.CharField(source = 'user.email' ,read_only = True)
    phone_no = serializers.CharField(source = 'user.phone_number' ,read_only = True)
    billing_address = serializers.CharField(source ='user.billing_address' , read_only = True)
    is_active = serializers.BooleanField(source = 'user.is_active' , read_only = True)
    apparel_type = serializers.CharField(source = 'user_design.apparel' , read_only = True)
    print_method = serializers.CharField(source ='user_design.style' ,read_only = True)
    color = serializers.CharField(source = 'user_design.color' , read_only = True)
    size = serializers.CharField(source = 'user_design.shirt_size' , read_only = True)

    class Meta:
        model = models.Order
        fields = [
            'order_id',
            'customer_name',
            'email',
            'phone_no',
            'shipping_address',
            'billing_address',
            'is_active',
            'apparel_type',
            'print_method',
            'color',
            'size',
            'quantity',
            'created_at',
            'order_status',
            'payment',
            'subtotal',
            'discount_applied',
            'shipping_fee',
            'total_amount',
            ]
        
    def to_representation(self, instance):

        data = super().to_representation(instance)
        user = instance.shipping_address

        data['shipping_address'] = {
            'full_name': user.full_name,
            'phone_number': user.phone_number,
            'email': user.email,
            'street_address': user.street_address,
            'city': user.city,
            'postal_code': user.postal_code,
            'province_state': user.province_state,
            'country': user.country
        }
        return data
 

class ListUserSerializer(serializers.ModelSerializer):
    design_type = serializers.CharField(source='product.design_type', read_only=True)
    total_orders = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField(source="get_full_name")
    profile_picture = serializers.CharField(source = 'user.profile_picture' ,read_only = True)
    
    class Meta:
        model = models.User
        fields = [
            'id',
            'user_id',
            'full_name',
            'profile_picture',
            'email',
            'is_active',
            'last_login',
            'design_type',
            'total_orders'

        ]
    def get_total_orders(self , obj):
        return obj.user_orders.count()

class ViewUserSerializer(serializers.ModelSerializer):

    total_orders = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = models.User
        fields = [
            'profile_picture',
            'first_name',
            'last_name',
            'user_id',
            'email',
            'phone_number',
            'is_active',
            'total_orders',
            'total_spent',
        ]


# class ProductCatalogSerializer(serializers.ModelSerializer):
#     base_price = serializers.CharField(source = 'pricing_rule.base_price')
#     class Meta:
#         model = models.ApparelProduct
#         fields = [
#             'product_id',
#             'product_name',
#             'sizes_available',
#             'color_options',
#             'base_price',
#             'print_methods_supported',
#             'is_active',
#         ]
    