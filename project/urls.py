"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from app.views import *

router = DefaultRouter()
router.register(r'user', UserViewset, basename='user-auth')
router.register(r'apparel-products', ApparelProductView, basename='apparel-product')
router.register(r'apparel-sizes', ApparelSizesView, basename='apparel-sizes')
router.register(r'pricing-rules', PricingRulesView, basename='pricing-rules')
router.register(r'user-dashboard', UserDesignView, basename='user-dashboard')
router.register(r'shipping-address', UserDesignView, basename='shipping-address')
router.register(r'billing-address', UserDesignView, basename='billing-address')
router.register(r'orders', OrderView, basename='orders')
# #dashboard routes:
# router.register(r'user-portfolio', UserPortfolioViewset, basename='user-portfolio')
# router.register(r'admin-dashboard', AdminDashboardViewset, basename='dashboard')
# router.register(r'dashboard-order-revenue', AdminDashboardViewset, basename='dashboard-order-revenue')
# router.register(r'dashboard-recent-orders', RecentOrderAdminDashboardView, basename='dashboard-recent-orders')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('user/login/', TokenObtainPairView.as_view()),
    path('user/refresh-token/', TokenRefreshView.as_view()),
    path('user/logout/', TokenBlacklistView.as_view()),
]
