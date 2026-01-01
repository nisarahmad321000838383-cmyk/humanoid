from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import UserSettings


class Command(BaseCommand):
    help = 'Creates the super admin account'

    def handle(self, *args, **options):
        admin_email = 'fiafghan@gmail.com'
        admin_password = 'Adamfarjawan2050@'
        
        # Check if admin already exists
        if User.objects.filter(email=admin_email).exists():
            admin_user = User.objects.get(email=admin_email)
            admin_user.set_password(admin_password)
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            # Ensure this seeded admin has upload permission disabled per project requirement
            settings_obj, _ = UserSettings.objects.get_or_create(user=admin_user)
            settings_obj.upload_your_files = False
            settings_obj.save()
            self.stdout.write(
                self.style.SUCCESS(f'Admin account with email {admin_email} already exists. Password updated.')
            )
        else:
            # Create new admin user
            admin_user = User.objects.create_user(
                username=admin_email.split('@')[0],  # Use email prefix as username
                email=admin_email,
                password=admin_password,
                is_staff=True,
                is_superuser=True
            )
            # Disable uploads for the seeded admin user
            settings_obj, _ = UserSettings.objects.get_or_create(user=admin_user)
            settings_obj.upload_your_files = False
            settings_obj.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin account with email {admin_email}')
            )
