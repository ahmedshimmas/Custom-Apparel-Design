from django.shortcuts import render
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta
from rest_framework import status
from django.contrib.auth import get_user_model
from app.tasks import send_welcome_otp, password_reset_otp
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from project import settings
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.db.models import Sum, F

User = get_user_model()

from app import models, serializers

# Create your views here.

class UserViewset(GenericViewSet, CreateModelMixin):
    queryset = models.User.objects.none()
    serializer_class = serializers.UserSerializer
    http_method_names = ['post']

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

            message = f"""\
                            <html>
                            <body>
                                <p>
                                Hi {user.username},<br>
                                Click the following link to reset your <b>password</b>:<br>
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
            {'detail': 'user profile patched successfully'},
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
            {'detail': 'user shipping patched successfully'},
            status = status.HTTP_200_OK
            )



class UserDashboardViewset(viewsets.ModelViewSet):
    queryset = models.UserDashboard.objects.all()
    serializer_class = serializers.UserDashboardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == "admin":
            return super().get_queryset()
        else:
            return models.UserDashboard.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)




class UserPortfolioViewset(GenericViewSet, ListModelMixin):
    serializer_class = serializers.UserDashboardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return models.UserDashboard.objects.filter(user=self.request.user)




class OrderViewset(viewsets.ModelViewSet):
    queryset = models.Order.objects.all()
    serializer_class = serializers.OrderSerializer

    def get_queryset(self):
        if self.request.user.role == "admin":
            return super().get_queryset()
        else:
            return models.Order.objects.filter(user=self.request.user)


#admin dashboard
class AdminDashboardViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    http_method_names = ['get']

    def list(self, request):
        if not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to access this resource.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate monthly revenue
        monthly_revenue = models.Order.objects.filter(
            order_date__month=timezone.now().month,
            order_date__year=timezone.now().year,
            is_active=True
            ).aggregate(total = Sum('product__price'))['total'] or 0 #the ['total'] here returns only the value of variable total we declared in aggregate, without this ['total'] the whole dictionary will be returned rather than just the value, etc {'total': 123} will be returned rather than just 123

        new_apparel_designs = models.Product.objects.filter(created_at__gte=timezone.now().month).count()
        active_orders = models.Order.objects.filter(is_active=True).count()

        payments_received = models.Order.objects.filter(
            status='Completed'
            ).aggregate(
                total_payments = Sum('product__price'))['total_payments'] or 0
        
        new_customers = models.User.objects.filter(created_at__gte=timezone.now().month).count()
        cancelled_orders = models.Order.objects.filter(status='Cancelled').count()

        return Response(
            {
            'monthly_revenue': monthly_revenue,
            'new_apparel_designs': new_apparel_designs,
            'active_orders': active_orders,
            'payments_received': payments_received,
            'new_customers': new_customers,
            'cancelled_orders': cancelled_orders

            }, 
            status=status.HTTP_200_OK
        )

#order revenue
class OrderRevenueAdminDashboardView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    http_method_names = ['get']

    def list(self, request):
        filter = request.query_params.get('filter', '1M')
        today = timezone.now().date()

        if filter == '1M':
            start_date = today - timedelta(days=30)
        elif filter == '3M':
            start_date = today - timedelta(days=60)
        elif filter == '6M':
            start_date = today - timedelta(days=180)
        elif filter == '1Y':
            start_date =  today - timedelta(days=365)
        else:
            start_date = None
        
        query = models.Order.objects.filter(order_date__gte = start_date) if start_date else models.Order.objects.all()
        revenue = query.aggregate(
            total = F('product__price') * F('product__quantity')
        )['revenue'] or 0
                
        return Response(
            {
                'order_revenue': revenue
            }
        )    


#recent orders api in dashboard
class RecentOrderAdminDashboardView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    http_method_names = ['get']

    def list(self, request):
        recent_orders = models.Order.objects.filter(is_active=True).order_by('-order_date')[:5]
        serializer = serializers.OrderSerializer(recent_orders, many=True)
        return Response(
        {
        'recent_orders': serializer.data,
        }, 
        status=status.HTTP_200_OK
        )

class PricingRuleViewSet(viewsets.ModelViewSet):
    queryset = models.PricingRules.objects.all()
    serializer_class = serializers.PricingRulesSerializer
    permission_classes = [IsAdminUser]

