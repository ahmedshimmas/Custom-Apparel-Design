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

class ProductColor(TextChoices):
    BLACK = 'blck', 'BLACK'
    BROWN = 'brn', 'BROWN'
    PURPLE = 'pp', 'PURPLE'
    BLUE = 'bl', 'BLUE'
    CYAN = 'cy', 'CYAN'
    GREEN = 'gr', 'GREEN'
    RED = 'rd', 'RED'