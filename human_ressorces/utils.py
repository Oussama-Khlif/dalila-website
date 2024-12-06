from django.core.mail import EmailMessage
from django.conf import settings

def send_email(to_email, subject, message):
    try:
        email = EmailMessage(
            subject,               
            message,               
            settings.EMAIL_HOST_USER,  
            [to_email],            
        )
        email.content_subtype = "html"  
        email.send(fail_silently=False)
        return True
    except Exception as e:
        return False