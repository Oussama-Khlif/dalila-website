from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from pages.models import Rating
from django.utils import timezone

@receiver(post_save, sender=Rating)
def create_rating_notification(sender, instance, created, **kwargs):
    if created:  
        painting_owner = instance.painting.user
        if painting_owner != instance.user:  
            message = f"⭐ Le tableau '{instance.painting.name}' a reçu une note de {instance.score}/5"
            Notification.objects.create(
                user=painting_owner,
                message=message,
                created_at=timezone.now(),
                is_cleared=False,
                visible_to_admin_only=False  
            )