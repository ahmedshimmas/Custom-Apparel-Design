from django.contrib import admin
from app import models
# Register your models here.

admin.site.register(
    [
        models.User,
        models.ApparelProduct,
        models.PricingRules,
        models.UserDesign,
        models.Size,
        models.ShippingAddress,
        models.BillingAddress,
        models.Order
    ]
)