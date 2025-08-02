from django.db.models import TextChoices


class UserRoleChoices(TextChoices):
    ADMIN = 'admin', 'ADMIN'
    USER = 'user', 'USER'


class ProductSizes(TextChoices):
    SMALL = 'S', 'SMALL' 
    MEDIUM = 'M', 'MEDIUM'
    LARGE = 'L', 'LARGE'
    EXTRA_LARGE = 'XL', 'EXTRA_LARGE'
    EXTRA_EXTRA_LARGE = 'XXL', 'EXTRA_EXTRA_LARGE'
    ONE_SIZE = 'ONE_SIZE', 'ONE_SIZE'

class ProductPrintMethods(TextChoices):
    EMBROIDARY = 'em', 'EMBROIDARY'
    SCREEN_PRINTING = 'spr', 'SCREEN_PRINTING'
    BOTH = 'b', 'BOTH'


class UserDesignType(TextChoices):
    AI_GENERATED =  'ai', 'AI-GENERATED'
    CUSTOM_DESIGN = 'custom', 'CUSTOM-DESIGN'


class OrderStatus(TextChoices):
    PROCESSING = 'Processing', 'PROCESSING'
    COMPLETED = 'Completed', 'COMPLETED'
    CANCELLED = 'Cancelled', 'CANCELLED'


class OrderTrackingStatus(TextChoices):
    ORDER_PLACED = 'placed', 'ORDER_PLACED'
    ORDER_PACKED = 'packed', 'ORDER_PACKED'
    IN_TRANSIT = 'transit', 'IN_TRANSIT'
    OUT_FOR_DELIVERY = 'delivery', 'OUT_FOR_DELIVERY'
    DELIVERED = 'delivered', 'DELIVERED'


class PaymentStatus(TextChoices):
    PAID = 'Paid', 'PAID'
    UNPAID = 'Unpaid', 'UNPAID'


