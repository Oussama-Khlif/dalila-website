from django.core.management.base import BaseCommand
from django.utils import timezone
from human_ressorces.models import CustomUser

class Command(BaseCommand):
    help = 'Clears inactive users who were created more than 24 hours ago'

    def handle(self, *args, **options):

        cutoff_time = timezone.now() - timezone.timedelta(hours=24)

        inactive_users = CustomUser.objects.filter(is_active=False, date_joined__lt=cutoff_time)

        count = inactive_users.count()

        inactive_users.delete()

        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} inactive users.'))