from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "Create the default superuser (only once)"

    def handle(self, *args, **options):
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                email="admin@example.com",
                password="1q2w3e4r",
                username="Super Admin",
                is_superuser=True,
                role = 'admin'
            )                
            self.stdout.write(self.style.SUCCESS("Superuser created."))
        else:
            User.objects.filter(is_superuser=True).update(is_active=True)
            self.stdout.write(self.style.WARNING("Superuser already exists."))