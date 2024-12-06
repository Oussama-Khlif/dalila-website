from django import template
from human_ressorces.models import Absence, Atelier_Facture, Profile, Notification  
from django.utils import timezone
from human_ressorces.views import check_extratime  
from datetime import timedelta  

register = template.Library()

def should_reactivate_notification(notification, profile):
    """
    Check if a notification should be reactivated based on its type and current conditions
    """
    message = notification.message

    if "Alerte d'absence" in message:
        return profile.absence_alert

    if "Facture disponible" in message:
        return Atelier_Facture.objects.filter(profile=profile).exists()

    if "temps supplémentaire" in message or "extra time" in message:
        current_extra_time = check_extratime(profile)
        return bool(current_extra_time)

    if "⭐" in message:
        return False

    return False

@register.simple_tag(takes_context=True)
def notifications(context):
    request = context['request']
    user = request.user
    profiles = Profile.objects.all()
    alerts = []

    cleared_notifications = Notification.objects.filter(
        user=user, 
        is_cleared=True,
        cleared_at__lt=timezone.now() - timedelta(days=1)
    )

    for notification in cleared_notifications:
        if "⭐" in notification.message:
            continue

        profile_name = None
        for profile in profiles:
            if f"{profile.name} {profile.last_name}" in notification.message:
                profile_name = profile
                break

        if profile_name and should_reactivate_notification(notification, profile_name):
            notification.is_cleared = False
            notification.cleared_at = None
            notification.save()

    for profile in profiles:

        if profile.absence_alert:
            alert_message = f"⚠️ Alerte d'absence depuis {profile.name} {profile.last_name}"
            alerts.append(alert_message)
            Notification.objects.get_or_create(
                user=user, 
                message=alert_message, 
                defaults={'is_cleared': False}
            )

        profile.calculateSubscriptionFee()  
        profile.calculateFacture() 
        facture_exists = Atelier_Facture.objects.filter(profile=profile).exists()

        if facture_exists:
            facture_message = f"💵 {profile.name} {profile.last_name}: Facture disponible"
            alerts.append(facture_message)
            
            Notification.objects.get_or_create(
                user=user, 
                message=facture_message, 
                defaults={'is_cleared': False}
            )


        if profile.role == 'teacher':  
            total_hours_worked = 0.0
            presence_records = Absence.objects.filter(profile=profile, is_present=True, is_calculated=False)

            for record in presence_records:
                if record.date_from and record.date_to:
                    duration = record.date_to - record.date_from
                    hours = duration.total_seconds() / 3600
                    total_hours_worked += hours

            teacher_facture = profile.calculate_total_fee(total_hours_worked)
            if teacher_facture > 0:
                teacher_facture_message = f"💼 {profile.name} {profile.last_name}: Facture disponible"
                alerts.append(teacher_facture_message)
                Notification.objects.get_or_create(
                    user=user, 
                    message=teacher_facture_message, 
                    defaults={'is_cleared': False}
                )

        extra_time_message = check_extratime(profile)
        if extra_time_message:
            notification_message = f"🕒 {profile.name} {profile.last_name}: {extra_time_message}"
            alerts.append(notification_message)
            Notification.objects.get_or_create(
                user=user, 
                message=notification_message, 
                defaults={'is_cleared': False}
            )

    if user.is_superuser:
        notifications = Notification.objects.filter(user=user, is_cleared=False)
    else:
        notifications = Notification.objects.filter(
            user=user, is_cleared=False, visible_to_admin_only=False
        )    
    return notifications