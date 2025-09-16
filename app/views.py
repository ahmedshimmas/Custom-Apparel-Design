from django.shortcuts import render
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.db.models import Sum, F
from django.db.models.functions import TruncWeek, TruncMonth, TruncQuarter, TruncYear

from app import models, serializers, choices, utils
from app import permissions
from .pagination import CustomPagination
from project import settings

User = get_user_model()

class LoginView(APIView):
    def post(self, request):
        serializer = serializers.LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')

        if not email or not password:
            return Response(
                {"detail": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "No user found with this email"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {"detail": "Incorrect password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {
                    "detail": "User is inactive. Please verify OTP.",
                    "is_active": False,
                    "user_id": user.id,
                },
                status=status.HTTP_403_FORBIDDEN
            )

        tokens = utils.get_tokens_for_user(user)

        shipping = getattr(user, "shipping_address", None)

        return Response({
            **tokens,
            "user": {
                "id": user.id,
                "role": user.role,
                "profile_picture": user.profile_picture.url if user.profile_picture else "",
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
                "email": user.email,
                "consent": user.consent,
                "is_active": user.is_active,
                "shipping_address": {
                    'full_name': shipping.full_name if shipping else "",
                    'phone_number': shipping.phone_number if shipping else "",
                    'email': shipping.email if shipping else "",
                    'street_address': shipping.street_address if shipping else "",
                    'city': shipping.city if shipping else "",
                    'postal_code': shipping.postal_code if shipping else "",
                    'province_state': shipping.province_state if shipping else "",
                    'country': shipping.country if shipping else ""
                },
                "notifications": {
                    'order_confirmation_email': user.order_confirmation_email,
                    'payment_success_notification': user.payment_success_notification,
                    'shipping_delivery_updates': user.shipping_delivery_updates,
                    'AI_design_approvals_alerts': user.AI_design_approvals_alerts,
                    'account_activity_alerts': user.account_activity_alerts
                }
            }
        })


class UserViewset(GenericViewSet, CreateModelMixin):
    queryset = models.User.objects.none()
    serializer_class = serializers.UserSerializer
    http_method_names = ['post']
    permission_classes = []

    @action(
        detail=False,
        methods=['post'],
        serializer_class = serializers.ResendOTPSerializer,
        url_path='resend-otp'
    )
    def resend_otp(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': f'otp sent to {request.data["email"]}. please check your email for otp.'},
            status=status.HTTP_200_OK
        )     

    @action(
        detail=False,
        methods=['post'],
        serializer_class = serializers.VerifyOTPSerializer,
        url_path='verify-otp'
    )
    def verify_otp(self, request):
        user = get_object_or_404(models.User, email=request.data['email'])
        if request.data['otp'] == user.otp and user.otp_expiry > timezone.now():
            user.otp = ''
            user.otp_expiry = None
            user.is_active = True
            user.save()
            return Response({'detail': 'email verified successfully'}, status=status.HTTP_200_OK)
        return Response(
            {'otp': 'otp either invalid or expired'}, 
            status=status.HTTP_403_FORBIDDEN
            )
    
    @action(
        detail=False,
        methods=['post'],
        serializer_class = serializers.PasswordResetSerializer,
        url_path='reset-password-request'
    )
    def reset_password_request(self, request, *args, **kwargs):
        serializer = serializers.PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = models.User.objects.get(email=email)
            except models.User.DoesNotExist:
                return Response(
                    {"error": "User with this email does not exist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_url = f"{settings.frontend_url}/forgot/{uid}/{token}"
            subject = 'PASSWORD RESET REQUESET - CAD'

            message = f"""
                            <html>
                            <body>
                                <p>
                                    Hi {user.username},<br>
                                    Click the following link to reset your <strong>password</strong>:<br>
                                    <a href="{reset_url}">{reset_url}</a>
                                </p>
                                <p>
                                    <strong>Regards,<br>CAD Admin</strong>
                                </p>
                            </body>
                            </html>
            """

            
            email_message = EmailMultiAlternatives(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [email]
            )

            email_message.attach_alternative(message, "text/html")
            email_message.send()

            return Response(
                {"success": "Password reset link sent"}, status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(
        detail=False,
        methods=['post'],
        serializer_class = serializers.PasswordResetConfirmSerializer,
        url_path='reset-password'
    )
    def reset_password(self, request, *args, **kwargs):
        serializer = serializers.PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            uidb64 = serializer.validated_data["uidb64"]
            token = serializer.validated_data["token"]
            new_password = serializer.validated_data["new_password"]

            try:
                uid = force_str(urlsafe_base64_decode(uidb64))
                user = get_user_model().objects.get(pk=uid)
            except (
                TypeError,
                ValueError,
                OverflowError,
                get_user_model().DoesNotExist,
            ):
                return Response(
                    {"error": "Invalid UID"}, status=status.HTTP_400_BAD_REQUEST
                )

            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.is_active = True
                user.save()
                return Response(
                    {"success": "Password reset successful"}, status=status.HTTP_200_OK
                )

            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    @action(
        detail=False,
        methods=['post'],
        serializer_class = serializers.ChangePasswordSerializer,
        permission_classes=[IsAuthenticated],
        url_path='change-password'
    )
    def change_password(self, request):
        user = request.user
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'password changed. please login with your new password'},
            status=status.HTTP_200_OK
            )
    

    @action(
        detail=False,
        methods=['post'],
        serializer_class=serializers.PatchUserProfileSerializer,
        permission_classes=[IsAuthenticated],
        url_path='patch-user-profile'
    )
    def patch_user_profile(self, request):
        user = User.objects.get(id=request.user.id)
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                'detail': 'user profile patched successfully',
                'data': serializer.data
            },
            status = status.HTTP_200_OK
            )
    

    @action(
        detail=False,
        methods=['post'],
        serializer_class=serializers.PatchUserNotificationSerializer,
        permission_classes=[IsAuthenticated],
        url_path='patch-notifications'
    )
    def patch_notifications(self, request):
        user = User.objects.get(id=request.user.id)
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                'detail': 'user shipping patched successfully',
                'data': serializer.data
            },
            status = status.HTTP_200_OK
            )



class ApparelProductView(viewsets.ModelViewSet):
    queryset = models.ApparelProduct.objects.all()
    serializer_class = serializers.ApparelProductSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    



class PricingRulesView(viewsets.ModelViewSet):
    queryset = models.PricingRules.objects.all()
    serializer_class = serializers.PricingRuleSerializer
    permission_classes = [IsAdminUser]


class ApparelSizesView(viewsets.ModelViewSet):
    queryset = models.Size.objects.all()
    serializer_class = serializers.SizeSerializer
    permission_classes = [IsAdminUser]
    


class UserDesignView(viewsets.ModelViewSet):
    queryset = models.UserDesign.objects.all()
    serializer_class = serializers.UserDesignSerializer
    permission_classes = [permissions.IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return models.UserDesign.objects.all()
        return models.UserDesign.objects.filter(user=self.request.user)           




class ShippingAddressView(viewsets.ModelViewSet):
    serializer_class = serializers.ShippingAddressSerializer
    permission_classes = [permissions.IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return models.ShippingAddress.objects.all()
        return models.ShippingAddress.objects.filter(user=self.request.user)



class BillingAddressView(viewsets.ModelViewSet):
    serializer_class = serializers.BillingAddressSerializer
    permission_classes = [permissions.IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return models.BillingAddress.objects.all()
        return models.BillingAddress.objects.filter(user=self.request.user)



class OrderView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return models.Order.objects.all()
        return models.Order.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.OrderCreateSerializer
        return serializers.OrderListSerializer



# class UserDesignViewset(viewsets.ModelViewSet):
#     queryset = models.UserDesign.objects.all()
#     serializer_class = serializers.UserDesignSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         if self.request.user.role == "admin":
#             return super().get_queryset()
#         else:
#             return models.UserDesign.objects.filter(user=self.request.user)
    
#     def perform_create(self, serializer):
#         return serializer.save(user=self.request.user)




# class UserPortfolioViewset(GenericViewSet, ListModelMixin):
#     serializer_class = serializers.UserDesignSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return models.UserDesign.objects.filter(user=self.request.user)




# class OrderViewset(viewsets.ModelViewSet):
#     queryset = models.Order.objects.all()
#     serializer_class = serializers.OrderSerializer

#     def get_queryset(self):
#         if self.request.user.role == "admin":
#             return super().get_queryset()
#         else:
#             return models.Order.objects.filter(user=self.request.user)


# #admin dashboard
# class AdminDashboardViewset(viewsets.ViewSet):
#     permission_classes = [IsAuthenticated, IsAdminUser]
#     http_method_names = ['get']

#     def list(self, request):
#         if not request.user.is_staff:
#             return Response(
#                 {'detail': 'You do not have permission to access this resource.'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         # Calculate monthly revenue
#         monthly_revenue = models.Order.objects.filter(
#             order_date__month=timezone.now().month,
#             order_date__year=timezone.now().year,
#             is_active=True
#             ).aggregate(total = Sum('product__price'))['total'] or 0 #the ['total'] here returns only the value of variable total we declared in aggregate, without this ['total'] the whole dictionary will be returned rather than just the value, etc {'total': 123} will be returned rather than just 123

#         new_apparel_designs = models.Product.objects.filter(created_at__gte=timezone.now().month).count()
#         active_orders = models.Order.objects.filter(is_active=True).count()

#         payments_received = models.Order.objects.filter(
#             status='Completed'
#             ).aggregate(
#                 total_payments = Sum('product__price'))['total_payments'] or 0
        
#         new_customers = models.User.objects.filter(created_at__gte=timezone.now().month).count()
#         cancelled_orders = models.Order.objects.filter(status='Cancelled').count()

#         return Response(
#             {
#             'monthly_revenue': monthly_revenue,
#             'new_apparel_designs': new_apparel_designs,
#             'active_orders': active_orders,
#             'payments_received': payments_received,
#             'new_customers': new_customers,
#             'cancelled_orders': cancelled_orders

#             }, 
#             status=status.HTTP_200_OK
#         )

# #order revenue
# class OrderRevenueAdminDashboardView(viewsets.ViewSet):
#     permission_classes = [IsAuthenticated, IsAdminUser]
#     http_method_names = ['get']

#     def list(self, request):
#         filter = request.query_params.get('filter', '1M')
#         today = timezone.now().date()

#         if filter == '1M':
#             start_date = today - timedelta(days=30)
#         elif filter == '3M':
#             start_date = today - timedelta(days=60)
#         elif filter == '6M':
#             start_date = today - timedelta(days=180)
#         elif filter == '1Y':
#             start_date =  today - timedelta(days=365)
#         else:
#             start_date = None
        
#         query = models.Order.objects.filter(order_date__gte = start_date) if start_date else models.Order.objects.all()
#         revenue = query.aggregate(
#             total = F('product__price') * F('product__quantity')
#         )['total'] or 0
                
#         return Response(
#             {
#                 'order_revenue': revenue
#             }
#         )    


# #recent orders api in dashboard
# class RecentOrderAdminDashboardView(viewsets.ViewSet):
#     permission_classes = [IsAuthenticated, IsAdminUser]
#     http_method_names = ['get']

#     def list(self, request):
#         recent_orders = models.Order.objects.filter(is_active=True).order_by('-order_date')[:5]
#         serializer = serializers.OrderSerializer(recent_orders, many=True)
#         return Response(
#         {
#         'recent_orders': serializer.data,
#         }, 
#         status=status.HTTP_200_OK
#         )

# class PricingRuleViewSet(viewsets.ModelViewSet):
#     queryset = models.PricingRules.objects.all()
#     serializer_class = serializers.PricingRuleSerializer
#     permission_classes = [IsAdminUser]




# -------------------------ADMIN FLOW--------------------------

class AdminDashboardViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    http_method_names = ['get']

    def list(self, request):
        if not request.user.is_superuser:
            return Response(
                {'detail': 'You do not have permission to access this resource.'},
                status=status.HTTP_403_FORBIDDEN
            )
        now = timezone.now()
        monthly_revenue = models.Order.objects.filter(
            created_at__year = now.year,
            created_at__month = now.month  
        ).aggregate(total=Sum(F('total_amount')*F('quantity')))['total'] or 0
        new_apparel_designs = models.UserDesign.objects.filter(created_at__month = now.month).count()
        active_orders  =models.Order.objects.filter(is_active =True).count()
        payments_received = models.Order.objects.filter(order_status = 'Completed').aggregate(amount = Sum('total_amount'))['amount'] or 0
        new_customers = models.User.objects.filter(created_at__month = now.month).count()
        cancelled_orders = models.Order.objects.filter(order_status = 'Cancelled').count()

        # recent_orders = models.Order.objects.filter(is_active=True).order_by('-created_at')[:5]
        # serializer = serializers.UserOrderSerializer(recent_orders, many=True)

        # ---- 1M (weekly revenue for current month) ----
        orders_this_month = models.Order.objects.filter(
            created_at__year=now.year,
            created_at__month=now.month
        ).annotate(week=TruncWeek('created_at')).values('week') \
         .annotate(value=Sum(F('total_amount') * F('quantity'))) \
         .order_by('week')

        one_m = []
        for i, o in enumerate(orders_this_month, start=1):
            one_m.append({"name": f"Week {i}", "value": o["value"] or 0})

        # ---- 3M (monthly revenue, last 3 months) ----
        last_3m = now - timedelta(days=90)
        orders_3m = models.Order.objects.filter(created_at__gte=last_3m) \
            .annotate(month=TruncMonth('created_at')).values('month') \
            .annotate(value=Sum(F('total_amount') * F('quantity'))) \
            .order_by('month')

        three_m = [
            {"name": o["month"].strftime("%b"), "value": o["value"] or 0}
            for o in orders_3m
        ]

        # ---- 6M (two halves: Q1+Q2 and Q3+Q4 style) ----
        last_6m = now - timedelta(days=180)
        orders_6m = models.Order.objects.filter(created_at__gte=last_6m) \
            .annotate(quarter=TruncQuarter('created_at')).values('quarter') \
            .annotate(value=Sum(F('total_amount') * F('quantity'))) \
            .order_by('quarter')

        six_m = []
        for i, o in enumerate(orders_6m, start=1):
            six_m.append({"name": f"Q{i}", "value": o["value"] or 0})

        # ---- 1Y (2 halves: H1 + H2) ----
        start_year = now.replace(month=1, day=1)
        orders_year = models.Order.objects.filter(created_at__gte=start_year) \
            .annotate(month=TruncMonth('created_at')).values('month') \
            .annotate(value=Sum(F('total_amount') * F('quantity'))) \
            .order_by('month')

        h1 = sum(o["value"] or 0 for o in orders_year if o["month"].month <= 6)
        h2 = sum(o["value"] or 0 for o in orders_year if o["month"].month > 6)
        one_y = [{"name": "H1", "value": h1}, {"name": "H2", "value": h2}]

        # ---- ALL (last 4 years) ----
        orders_all = models.Order.objects.annotate(year=TruncYear('created_at')) \
            .values('year') \
            .annotate(value=Sum(F('total_amount') * F('quantity'))) \
            .order_by('year')

        all_data = [
            {"name": o["year"].year, "value": o["value"] or 0}
            for o in orders_all
        ]
                
        return Response(
            {
                'monthly_revenue': monthly_revenue,
                'new_apparel_designs': new_apparel_designs,
                'active_orders': active_orders,
                'payments_received': payments_received,
                'new_customers': new_customers,
                'cancelled_orders': cancelled_orders,
                "1M": one_m,
                "3M": three_m,
                "6M": six_m,
                "1Y": one_y,
                "ALL": all_data,
            },
            status=status.HTTP_200_OK
        )
    

class OrderViewSet(viewsets.ModelViewSet):
    queryset = models.Order.objects.all()
    serializer_class = serializers.OrderCreateSerializer
    permission_classes = [IsAuthenticated]


class PricingRuleViewSet(viewsets.ModelViewSet):
    queryset = models.PricingRules.objects.all()
    serializer_class = serializers.PricingRuleSerializer
    permission_classes = [IsAdminUser]


class ManageOrdersViewset(GenericViewSet , ListModelMixin ):
    permission_classes  = [IsAdminUser]
    
    def list(self, request):
        total_orders = models.Order.objects.all().count()
        delivered_orders = models.Order.objects.filter(order_status = 'completed').count()
        pending_orders = models.Order.objects.filter(order_status = 'processing').count()
        cancelled_orders = models.Order.objects.filter(order_status = 'cancelled').count()

        return Response({
            "Total_Orders":total_orders,
            "Delivered_Orders":delivered_orders,
            "Pending_Orders":pending_orders,
            "Cancelled_orders":cancelled_orders
        },status=status.HTTP_200_OK)
        
        

class ListOrderViewset(GenericViewSet , ListModelMixin):
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination

    def list(self ,request):
        show_orders = models.Order.objects.all().order_by('created_at')
        page = self.paginate_queryset(show_orders)
        if page is not None:
            serializer = serializers.ListOrderSerializer(page , many=True)
            return self.get_paginated_response(serializer.data)        
        serializer = serializers.ListOrderSerializer(show_orders , many=True)
        return Response(serializer.data)

    @action(detail=True , methods=['get'] , url_path='view_orders')
    def view_order(self , request , pk=None):
        query_set = models.Order.objects.all()
        user = get_object_or_404(query_set , pk=pk)
        serializer = serializers.TrackOrderSerializer(user)
        return Response(serializer.data)        
    
    @action(detail=True , methods=['post'] , url_path='cancel_order', permission_classes=[IsAdminUser])
    def canceling_order(self , request , pk=None):
        try:
            order = models.Order.objects.get(id=pk)
        except:
            return Response({'message':'Order with this ID does not exist'})
        if order.is_active == False and order.order_status == choices.OrderStatus.CANCELLED:
            return Response({"message":f"Order {order.order_id} has been already cancelled."})
        
        order.is_active=False
        order.order_status = choices.OrderStatus.CANCELLED  
        order.save()
        return Response({
            "message":f"Order {order.order_id} has been cancelled successfully."
        })
    


     
class UserManagementViewset(GenericViewSet , ListModelMixin):
    permission_classes = [IsAdminUser , IsAuthenticated]

    def list(self , request):
        total_users = User.objects.all().count()
        active_users = User.objects.filter(is_active = True).count()
        suspended_users = User.objects.filter(is_active = False).count()
 
        return Response({
            "totals_users":total_users,
            "active_users":active_users,
            "suspended_user":suspended_users,
        })
    
    
class ListUserViewSet(GenericViewSet , ListModelMixin):
    permission_classes = [IsAdminUser , IsAuthenticated]
    pagination_class = CustomPagination


    def list(self , request):
        list_of_user = User.objects.all().order_by('id')
        page = self.paginate_queryset(list_of_user)
        if page is not None:
            serializer = serializers.ListUserSerializer(page , many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializers.ListUserSerializer(list_of_user , many=True)
        return Response(serializer.data)
    
    @action(detail=True ,methods=['post'] , url_path='suspend-user')
    def suspend_user(self, request, pk=None):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response('User with this ID does not exist')
        if user.is_superuser:
            return Response({'details': 'Cannot suspend a superuser'})
        user.is_active = False
        user.save()
        return Response({
            'details': f'user {pk} suspended'
        })
    
    @action(detail=True , methods=['post'] ,url_path='reactivate-user')
    def reactive_user(self ,request ,pk=None):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response('User with this ID does not exist')

        user.is_active = True
        user.save()
        return Response({'details':f'user {pk} reactivated successfully!'}) 
        

class ViewUserViewSet(GenericViewSet , RetrieveModelMixin):
    queryset = User.objects.all()
    serializer_class = serializers.ViewUserSerializer
    permission_classes = [IsAdminUser ,IsAuthenticated]
   
    def retrieve(self ,request, pk=None):
        try:
            user =  User.objects.get(id=pk)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'details': 'user with this id not found'
            })
        serializer =serializers.ViewUserSerializer(user)
        
        user_orders  = models.Order.objects.filter(user__id=pk)
        total_orders = user_orders.count()
        total_spent = user_orders.aggregate(orders_sum = Sum('total_amount'))['orders_sum'] or 0
        user_orders = models.Order.objects.order_by('created_at')[:6]
        orders = serializers.AdminUserViewOrdersSerializer(user_orders, many=True).data
        
        return Response({
            "total_user_orders":total_orders,
            "total_spent":total_spent,
            "user_details":serializer.data,
            "list_of_recent_orders":orders
            },  status=status.HTTP_200_OK
            )
    
  
# class ProductCatalogViewset(viewsets.ModelViewSet):
#     permission_classes = [IsAdminUser , IsAuthenticated]
#     pagination_class = CustomPagination

#     queryset = models.ApparelProduct.objects.all()
#     serializer_class = serializers.ProductCatalogSerializer

#     @action(detail=False , methods=['post'] , url_path='add_new_product')
#     def add_product(self , request):
#         serializer = serializers.ApparelProductSerializer(data = request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({'message':'Product has been created succesfully','data':serializer.data} , status=status.HTTP_201_CREATED)
#         return Response({'Message':serializer.data} , status=status.HTTP_400_BAD_REQUEST)