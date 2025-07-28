from django.db.models import TextChoices


class UserRoleChoices(TextChoices):
    ADMIN = 'admin', 'ADMIN'
    USER = 'user', 'USER'

class ProductSize(TextChoices):
    SMALL = 's', 'SMALL'
    MEDIUM = 'm', 'MEDIUM'
    LARGE = 'l', 'LARGE'
    EXTRA_LARGE = 'xl', 'EXTRA_LARGE'
    EXTRA_EXTRA_LARGE = 'xxl', 'EXTRA_EXTRA_LARGE'

class ProductStyle(TextChoices):
    EMBROIDARY = 'em', 'EMBROIDARY'
    PRINT = 'pr', 'PRINT'

class ApparelType(TextChoices):
    TSHIRT = 'T-SHIRT', 'T-SHIRT'
    POLO_SHIRT = 'POLO', 'POLO'
    SWEAT_SHIRT = 'SHIRT', 'SHIRT'
    CAP = 'CAP', 'CAP'
    HOODIE = 'HOODIE', 'HOODIE'

class ProductDesignType(TextChoices):
    AI_GENERATED =  'AI-GENERATED', 'AI-GENERATED'
    CUSTOM_DESIGN = 'CUSTOM-DESIGN', 'CUSTOM-DESIGN'

class PaymentStatus(TextChoices):
    PAID = 'Paid', 'PAID'
    UNPAID = 'Unpaid', 'UNPAID'

class OrderStatus(TextChoices):
    PROCESSING = 'Processing'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'