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


class ProductPrintMethods(TextChoices):
    EMBROIDARY = 'em', 'EMBROIDARY'
    SCREEN_PRINTING = 'pr', 'PRINT'
    BOTH = 'b', 'BOTH'


class UserDesignType(TextChoices):
    AI_GENERATED =  'ai', 'AI-GENERATED'
    CUSTOM_DESIGN = 'custom', 'CUSTOM-DESIGN'


class ApparelType(TextChoices):
    TSHIRT = 'T-SHIRT', 'T-SHIRT'
    POLO_SHIRT = 'POLO', 'POLO'
    SWEAT_SHIRT = 'SHIRT', 'SHIRT'
    CAP = 'CAP', 'CAP'
    HOODIE = 'HOODIE', 'HOODIE'


class PaymentStatus(TextChoices):
    PAID = 'Paid', 'PAID'
    UNPAID = 'Unpaid', 'UNPAID'


class OrderStatus(TextChoices):
    PROCESSING = 'Processing'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'


class DesignType(TextChoices):
    SIMPLE_AI_DESIGN = 'simple_aid', 'SIMPLE_AI_DESIGN'
    COMPLEX_AI_DESIGN = 'complex_aid', 'COMPLEX_AI_DESIGN'
    UPLOAD_VECTOR_FILE = 'upload_vf', 'UPLOAD_VECTOR_FILE'
    UPLOAD_PNG_JPG = 'upload_png', 'UPLOAD_PNG_JPG'
