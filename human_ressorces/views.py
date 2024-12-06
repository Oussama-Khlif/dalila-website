from decimal import Decimal, ROUND_DOWN
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import formset_factory
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from .forms import AccountDeletionForm, ApplyRemiseForm, CustomAuthenticationForm, CustomUserForm, GroupForm, LiveStreamForm, MarkPresenceForm, NoteForm, VerificationCodeForm
from pages.views import SpecialEvent
from human_ressorces.utils import send_email
from django.template.loader import render_to_string
from .models import Atelier_Facture, LiveStream, Notification, PaymentHistory, Profile, Absence, Atelier, Profit_stat, VerificationCode, VisitorIP
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import json
from .models import Profile, Group
from django.db.models import Sum
from datetime import timedelta
from django.shortcuts import render
from .models import Profile, Atelier, Absence, FinancialStats, Profit_stat
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.core.cache import cache
from .forms import ForgotPasswordRequestForm, ResetPasswordForm
from .models import CustomUser
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import re
from django.utils.text import slugify
from .forms import (
    AbsenceSearchForm,
    AtelierForm,
    ProfilePresenceForm,
    AbsenceAlertForm,
    RattrappageForm,
    ProfileForm,
    CustomUserCreationForm,
    ProfileUpdateForm,
    UsernameUpdateForm,
    CustomPasswordChangeForm
)

def admin_only(user):
    return user.is_superuser or user.username == 'admin'

@login_required
def myaccount(request):
    events = SpecialEvent.objects.all()

    profile_form = None
    username_form = None
    password_form = None
    deletion_form = AccountDeletionForm()  

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Photo de profil mise à jour avec succès.')
                return redirect('myaccount')

        elif 'update_username' in request.POST:
            username_form = UsernameUpdateForm(request.POST)
            if username_form.is_valid():
                if request.user.check_password(username_form.cleaned_data['password']):
                    request.user.username = username_form.cleaned_data['username']
                    request.user.save()
                    messages.success(request, 'Nom d’utilisateur mis à jour avec succès.')
                    return redirect('myaccount')
                else:
                    messages.error(request, 'Mot de passe incorrect. Veuillez réessayer.')

        elif 'update_password' in request.POST:
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  
                messages.success(request, 'Mot de passe changé avec succès.')
                return redirect('myaccount')

            else:
                if password_form.errors.get('old_password'):
                    messages.error(request, "L'ancien mot de passe est incorrect. Veuillez réessayer.")
                if password_form.errors.get('new_password2'):
                    messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")

        elif 'delete_profile_picture' in request.POST:
            user = request.user
            if user.profile_picture:  
                user.profile_picture.delete()
                user.save()
                messages.success(request, 'Photo de profil supprimée avec succès.')
            return redirect('myaccount')

        elif 'delete_account' in request.POST:  
            deletion_form = AccountDeletionForm(request.POST)
            if deletion_form.is_valid():
                username = deletion_form.cleaned_data['username']
                password = deletion_form.cleaned_data['password']

                if username == request.user.username and request.user.check_password(password):
                    request.user.delete()  
                    messages.success(request, 'Votre compte a été supprimé avec succès.')
                    return redirect('index')  
                else:
                    messages.error(request, 'Nom d’utilisateur ou mot de passe incorrect.')

    if profile_form is None:
        profile_form = ProfileUpdateForm(instance=request.user)
    if username_form is None:
        username_form = UsernameUpdateForm()
    if password_form is None:
        password_form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'pages/myaccount.html', {
        'profile_form': profile_form,
        'username_form': username_form,
        'password_form': password_form,
        'deletion_form': deletion_form,  
        'events': events
    })

def check_user_image(request):
    username = request.GET.get('username')
    try:
        user = CustomUser.objects.get(username=username)
        if user.profile_picture:
            return JsonResponse({'image_url': user.profile_picture.url})
    except CustomUser.DoesNotExist:
        pass
    return JsonResponse({'image_url': None})

def custom_login_view(request):
    events = SpecialEvent.objects.all()
    form = CustomAuthenticationForm(request, data=request.POST or None)
    verification_form = VerificationCodeForm()

    if request.method == 'POST':
        if 'verification_code' in request.POST:
            verification_code = request.POST.get('verification_code')
            username = request.POST.get('inactive_username')

            if not username:
                messages.error(request, "Nom d'utilisateur non trouvé.")
                return redirect('login')

            try:
                user = CustomUser.objects.get(username=username, is_active=False)
                verification = VerificationCode.objects.filter(user=user).first()

                if verification and verification.code == verification_code and verification.is_valid():
                    user.is_active = True
                    user.save()

                    verification.delete()  
                    login(request, user)
                    messages.success(request, f"Bienvenue, {username} !")
                    return redirect('index')
                else:
                    messages.error(request, "Le code de vérification est incorrect ou expiré.")
                    return render(request, 'pages/login.html', {
                        'form': form,
                        'events': events,
                        'verification_form': verification_form,
                        'inactive_user': user  
                    })

            except CustomUser.DoesNotExist:
                messages.error(request, "Utilisateur non trouvé.")
                return redirect('login')

        username = form.data.get('username')
        password = form.data.get('password')

        if not username:
            messages.error(request, "Veuillez entrer votre nom d'utilisateur.")
            return render(request, 'pages/login.html', {'form': form, 'events': events})

        cache_key = f"failed_login_{username.replace(' ', '_')}"
        suspension_key = f"suspend_{username.replace(' ', '_')}"

        is_suspended = cache.get_or_set(suspension_key, False, 3600)
        if is_suspended:
            messages.error(request, "Votre compte est temporairement suspendu. Veuillez réessayer dans 1 heure.")
            return render(request, 'pages/login.html', {
                'form': form, 
                'events': events, 
                'verification_form': verification_form
            })

        try:
            user = CustomUser.objects.get(username=username)
            if not user.is_active:
                verification_code = get_random_string(length=6, allowed_chars='0123456789')
                expiration_time = timezone.now() + timedelta(minutes=10)

                VerificationCode.objects.update_or_create(
                    user=user,
                    defaults={
                        'code': verification_code,
                        'expires_at': expiration_time
                    }
                )

                try:
                    subject = "Vérification de votre compte"
                    context = {
                        'name': user.username,
                        'message_body': f"Votre code de vérification est : {verification_code}",
                        'signature': "Chromarium"
                    }
                    message = render_to_string('pages/email_template.html', context)
                    send_email(user.email, subject, message)

                    messages.info(request, "Votre compte n'est pas encore activé. Un code de vérification a été envoyé à votre adresse e-mail.")
                except Exception as e:
                    messages.error(request, "Une erreur s'est produite lors de l'envoi du code de vérification. Veuillez réessayer.")

                return render(request, 'pages/login.html', {
                    'form': form,
                    'events': events,
                    'verification_form': verification_form,
                    'inactive_user': user  
                })

        except CustomUser.DoesNotExist:
            user = None

        if user is None or not authenticate(username=username, password=password):
            if not cache.get(cache_key):
                cache.add(cache_key, 0, 3600)
            attempts = cache.incr(cache_key)

            if attempts > 4:
                cache.set(suspension_key, True, 3600)
                messages.error(request, "Votre compte a été suspendu pour 1 heure en raison de plusieurs tentatives de connexion échouées.")
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
            return render(request, 'pages/login.html', {
                'form': form, 
                'events': events, 
                'verification_form': verification_form
            })

        cache.delete_many([cache_key, suspension_key])
        login(request, user)
        messages.success(request, f'Bienvenue, {username} !')
        return redirect('index')

    return render(request, 'pages/login.html', {
        'form': form, 
        'events': events, 
        'verification_form': verification_form
    })

def sanitize_filename(filename):
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)  
    filename = filename.replace(" ", "_")  
    return filename

def register(request):
    events = SpecialEvent.objects.all()
    verification_code_sent = False

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)

        if form.is_valid():
            email = form.cleaned_data['email']
            profile_picture = request.FILES.get('profile_picture')
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']

            temp_user = CustomUser(
                username=username,
                email=email,
                is_active=False,
            )

            temp_user.set_password(password)

            temp_user.save()

            verification_code = get_random_string(length=6, allowed_chars='0123456789')
            expiration_time = timezone.now() + timedelta(minutes=10)

            VerificationCode.objects.create(
                user=temp_user,
                code=verification_code,
                expires_at=expiration_time
            )

            if profile_picture:

                sanitized_filename = f"{slugify(username)}_{slugify(profile_picture.name)}"
                fs = FileSystemStorage(location=settings.MEDIA_ROOT)
                filename = fs.save(sanitized_filename, profile_picture)

                temp_user.profile_picture = filename  
                temp_user.save()

            try:
                subject = "Vérification de votre compte"
                context = {
                    'name': username,
                    'message_body': f"Votre code de vérification est : {verification_code}",
                    'signature': "Chromarium"
                }
                message = render_to_string('pages/email_template.html', context)
                send_email(email, subject, message)

                messages.success(request, "Un email de vérification a été envoyé à votre adresse email.")
                verification_code_sent = True

            except Exception as e:
                temp_user.delete()  
                messages.error(request, "Une erreur s'est produite lors de l'envoi de l'email de vérification. Veuillez réessayer.")

            return render(request, 'pages/register.html', {
                'form': form,
                'events': events,
                'verification_code_sent': verification_code_sent,
                'username': username,
            })

    else:
        form = CustomUserCreationForm()

    if request.method == 'POST' and 'verification_code' in request.POST:
        username = request.POST.get('username')
        entered_code = request.POST.get('verification_code')

        user = get_object_or_404(CustomUser, username=username, is_active=False)
        verification = VerificationCode.objects.filter(user=user).first()

        if verification is None or not verification.is_valid():
            messages.error(request, "Le code de vérification a expiré ou est invalide. Veuillez demander un nouveau code.")
            return render(request, 'pages/register.html', {
                'form': form,
                'events': events,
                'verification_code_sent': verification_code_sent,
                'username': username,
            })

        if entered_code == verification.code:
            user.is_active = True
            user.save()  

            login(request, user)  
            messages.success(request, f'Bienvenue, {username} !')  

            verification.delete()  

            return redirect('index')  
        else:
            messages.error(request, "Le code de vérification est incorrect.")

    return render(request, 'pages/register.html', {
        'form': form,
        'events': events,
        'verification_code_sent': False
    })

@login_required
@user_passes_test(admin_only)
def myclients(request):

    events = SpecialEvent.objects.all() 

    profiles = Profile.objects.prefetch_related('ateliers').order_by('name')

    for profile in profiles:

        profile_extra_time_emoji = ""
        profile_facture_emoji = ""
        profile_rattrappage_emoji = ""
        profile_alert_emoji = ""

        if check_extratime(profile):
            profile_extra_time_emoji = "🕒"  

        if profile.absence_alert:
            profile_alert_emoji = "⚠️"  

        total_absences_count_teacher = Absence.objects.filter(profile=profile, is_calculated=False, is_present=True).count()

        if profile.role != 'teacher':
            if Atelier_Facture.objects.filter(profile=profile).exists():
                profile_facture_emoji = "💵"
        else: 
            if total_absences_count_teacher >= 1:
                profile_facture_emoji = "💵" 

        if profile.rattrappage:
            profile_rattrappage_emoji = "📅"  

        profile.extra_time_emoji = profile_extra_time_emoji
        profile.facture_emoji = profile_facture_emoji
        profile.rattrappage_emoji = profile_rattrappage_emoji
        profile.alert_emoji = profile_alert_emoji

    return render(request, 'pages/myclients.html', {
        'profiles': profiles,
        'events': events,  
    })

@login_required
@user_passes_test(admin_only)
def addprofile(request):
    creation_message = None
    message_type = None  
    ateliers = Atelier.objects.all()

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES)

        if Profile.objects.filter(email=profile_form.data.get('email')).exists():
            creation_message = "Erreur : L'email existe déjà dans un autre profil."
            message_type = 'error'
        elif profile_form.is_valid():
            profile = profile_form.save(commit=False)

            if profile.role == 'teacher':
                if profile_form.cleaned_data['ateliers'].count() > 1:
                    creation_message = "Un enseignant ne peut être lié qu'à un seul atelier."
                    message_type = 'error'
                elif profile.registration_type != 'none':
                    creation_message = "Un enseignant ne peut pas avoir un type d'inscription."
                    message_type = 'error'
                else:
                    profile.registration_type = 'none'
                    profile.save()
                    profile_form.save_m2m()
                    creation_message = "Profil enseignant créé avec succès."
                    message_type = 'success'

                    send_welcome_email(profile)

                    profile_form = ProfileForm()
            else:
                profile.save()
                profile_form.save_m2m()
                creation_message = "Profil créé avec succès."
                message_type = 'success'

                send_welcome_email(profile)
                profile_form = ProfileForm()
        else:
            if 'ateliers' in profile_form.errors:
                creation_message = "Erreur : Le profil doit être inscrit à au moins un atelier."
            else:
                creation_message = "Erreur lors de la création du profil."
            message_type = 'error'

        return render(request, 'pages/addprofile.html', {
            'profile_form': profile_form,
            'creation_message': creation_message,
            'message_type': message_type,  
            'ateliers': ateliers,
        })

    else:
        profile_form = ProfileForm()

    return render(request, 'pages/addprofile.html', {
        'profile_form': profile_form,
        'ateliers': ateliers,
    })

def send_welcome_email(profile):
    subject = 'Bienvenue sur notre plateforme!'

    context = {
        'name': profile.name,
        'last_name': profile.last_name,
        'matricule': profile.matricule,  
        'message_body': f"Nous sommes ravis de vous accueillir sur notre plateforme, Votre matricule est: {profile.matricule}",
        'signature': "Chromarium"
    }

    message = render_to_string('pages/email_template.html', context)

    to_email = profile.email

    send_email(to_email, subject, message)

@login_required
@user_passes_test(admin_only)
def profile_details(request, matricule):
    events = SpecialEvent.objects.all() 

    profile = get_object_or_404(Profile, matricule=matricule)

    if request.method == 'POST' and 'delete_absence' in request.POST:

        profile.absence_alert = None
        profile.atelier_absent = None
        profile.upcoming_absence_date = None
        profile.save()

        messages.success(request, "Les informations d'absence ont été supprimées avec succès.")
        return redirect('profile_details', matricule=matricule)  

    presence_count = Absence.objects.filter(profile=profile, is_present=True, is_calculated=False).count()
    total_absences_count = Absence.objects.filter(profile=profile, is_calculated=False).count()
    total_absences_count_teacher = Absence.objects.filter(profile=profile, is_calculated=False, is_present=True).count()

    last_absence = Absence.objects.filter(profile=profile).order_by('-date_from').first()

    extra_time = check_extratime(profile)

    if profile.rattrappage and last_absence:
        rattrappage_date = profile.rattrappage.date()  
        absence_date = last_absence.date_from.date()  

        if absence_date >= rattrappage_date:
            profile.rattrappage = None
            profile.save()

    facture_message = None
    if profile.role != 'teacher':
        if Atelier_Facture.objects.filter(profile=profile).exists():
            facture_message = "💵 Facture disponible"
    else:
        if total_absences_count_teacher >= 1:
            facture_message = "💵 Facture disponible"

    rattrappage_message = None
    if profile.rattrappage:
        rattrappage_message = f"📅 Rattrappage est fixé le {profile.rattrappage.strftime('%d-%m-%Y')}."

    return render(request, 'pages/details.html', {
        'profile': profile,
        'presence_count': presence_count,
        'total_absences_count': total_absences_count,
        'extra_time': extra_time,
        'facture_message': facture_message,
        'rattrappage_message': rattrappage_message,
        'events': events
    })

def check_extratime(profile):
    if profile.role == 'teacher':

        last_absence = Absence.objects.filter(
            profile=profile,
            is_absent=True,
            is_calculated=False  
        ).order_by('-date_from').first()  

        if last_absence:

            subsequent_records = Absence.objects.filter(
                profile=profile,
                date_from__gt=last_absence.date_from,  
                is_calculated=False  
            ).order_by('date_from')[:2]  

            if len(subsequent_records) < 2:
                return "Les deux prochaines leçons auront du temps supplémentaire +30min"
            elif len(subsequent_records) == 2 and all(record.is_present for record in subsequent_records):
                return ""
            else:
                return "Les deux prochaines leçons auront du temps supplémentaire +30min"

    return None

@login_required
@user_passes_test(admin_only)
def delete_profile(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)

    if request.method == 'POST':
        profile.delete()
        messages.success(request, f"Le profil {matricule} a été supprimé avec succès.")
        return redirect('myclients')  

    return render(request, 'pages/details.html', {
        'profile': profile,
    })

@login_required
def absence_alert(request):
    events = SpecialEvent.objects.all() 

    if request.method == 'POST':
        alert_form = AbsenceAlertForm(request.POST)

        if alert_form.is_valid():
            matricule = alert_form.cleaned_data['matricule']
            phone_number = alert_form.cleaned_data['phone_number']
            atelier = alert_form.cleaned_data['atelier']
            upcoming_absence_date = alert_form.cleaned_data['upcoming_absence_date']
            absence_alert_date = timezone.localdate()

            try:
                profile = Profile.objects.get(matricule=matricule)

                profile.absence_alert = absence_alert_date
                profile.atelier_absent = atelier
                profile.upcoming_absence_date = upcoming_absence_date
                profile.save()

                messages.success(request, "L'alerte d'absence a été enregistrée avec succès.")
            except Profile.DoesNotExist:
                messages.error(request, "Profil non trouvé.")

            return redirect('absence_alert')
        else:

            for field, errors in alert_form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")

            alert_form.errors.clear()  

    else:
        alert_form = AbsenceAlertForm()

    return render(request, 'pages/absence_alert.html', {
        'alert_form': alert_form,
        'events':events,
    })

@login_required
@user_passes_test(admin_only)
def clear_absences(request, matricule, atelier_facture_id):
    profile = get_object_or_404(Profile, matricule=matricule)

    atelier_facture = get_object_or_404(Atelier_Facture, id=atelier_facture_id)

    if profile.advance >= atelier_facture.facture:
        profile.advance -= atelier_facture.facture
        profile.save()
    else:
        messages.error(request, "Paiement refusé. Solde insuffisant")
        return redirect('facture_details', matricule=matricule)

    financial_stats, created = FinancialStats.objects.get_or_create(id=1)
    financial_stats.total_fee_student += atelier_facture.facture
    financial_stats.save()
        
    messages.success(request, "Paiement confirmé !")

    PaymentHistory.objects.create(
        profile=profile,
        amount_paid=atelier_facture.facture,
        payment_date=timezone.now(),
        invoice_type="Confirmation"
    )

    absences = Absence.objects.filter(atelier=atelier_facture.atelier, profile=profile, is_payed=False).order_by('date_from')

    absences_to_update = absences[:4]
    
    for absence in absences_to_update:
        absence.is_payed = True
        absence.save()

    atelier_facture.delete()

    return redirect('facture_details', matricule=matricule)

@login_required
@user_passes_test(admin_only)
def rattrappage_view(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)

    if request.method == 'POST':
        rattrappage_form = RattrappageForm(request.POST)

        if rattrappage_form.is_valid():
            rattrappage_datetime = rattrappage_form.cleaned_data.get('rattrappage')
            today = timezone.now()
            if rattrappage_datetime and rattrappage_datetime < today.replace(hour=0, minute=0, second=0, microsecond=0):
                messages.error(request, "La date de rattrapage ne peut pas être antérieure à aujourd'hui.")
                return render(request, 'pages/rattrappage.html', {
                    'form': rattrappage_form,
                    'matricule': matricule,
                    'profile': profile,
                })

            if rattrappage_datetime is not None:
                profile.rattrappage = rattrappage_datetime
            else:
                profile.rattrappage = None

            profile.absence_alert = None
            profile.save()

            if profile.email and rattrappage_datetime is not None:
                subject = 'Avis de rattrappage'
                context = {
                    'name': profile.name,
                    'last_name': profile.last_name,
                    'message_body': f"Votre date de rattrapage sera le {rattrappage_datetime.strftime('%d %B %Y à %H:%M')}.",
                    'signature': "Chromarium"
                }
                message = render_to_string('pages/email_template.html', context)
                to_email = profile.email                
                send_email(to_email, subject, message)

            messages.success(request, "La date de rattrapage a été enregistrée avec succès!")
            return redirect('rattrappage', matricule=matricule)
    else:
        rattrappage_form = RattrappageForm()

    return render(request, 'pages/rattrappage.html', {
        'form': rattrappage_form,
        'matricule': matricule,
        'profile': profile,
    })

@login_required
@user_passes_test(admin_only)
def absences_details(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)
    form = AbsenceSearchForm(initial={'matricule': matricule})
    absences = Absence.objects.filter(profile__matricule=matricule).order_by('-date_from')

    if request.method == 'POST':
        try:

            data = json.loads(request.body)
            if data.get('delete_absence'):
                absence_id = data.get('absence_id')
                absence = get_object_or_404(Absence, id=absence_id)
                absence.delete()
                return JsonResponse({'success': True})

            form = AbsenceSearchForm(request.POST)
            if form.is_valid():
                absences = form.search_absences().order_by('-date_from')

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    context = {
        'form': form,
        'absences': absences,
        'profile': profile,
    }
    return render(request, 'pages/absences_details.html', context)

@login_required
@user_passes_test(admin_only)
def edit_absence(request, absence_id):
    absence = get_object_or_404(Absence, id=absence_id)

    if request.method == 'POST':
        is_present = request.POST.get('is_present') == 'on'
        is_absent = request.POST.get('is_absent') == 'on'
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')

        absence.is_present = is_present
        absence.is_absent = is_absent

        if date_from:
            naive_date_from = timezone.datetime.fromisoformat(date_from)
            absence.date_from = timezone.make_aware(naive_date_from)

        if date_to:
            naive_date_to = timezone.datetime.fromisoformat(date_to)
            absence.date_to = timezone.make_aware(naive_date_to)

        if absence.date_to and absence.date_from and absence.date_to < absence.date_from:
            messages.error(request, "Erreur: La date de fin ne peut pas être antérieure à la date de début")
            return redirect('edit_absence', absence_id=absence.id)

        if absence.date_to and absence.date_from:
            time_difference = absence.date_to - absence.date_from
            if time_difference > timezone.timedelta(hours=3):
                messages.error(request, "Erreur: La différence entre la date de début et la date de fin ne doit pas dépasser 3 heures.")
                return redirect('edit_absence', absence_id=absence.id)

        try:

            absence.save()
            messages.success(request, f"L'absence pour {absence.profile.matricule} a été mise à jour avec succès")
            return redirect('absences_details', matricule=absence.profile.matricule)
        except ValidationError as e:
            for error in e.messages:
                if "A profile cannot be marked both present and absent." in error:
                    messages.error(request, "Erreur: Un profil ne peut pas être marqué à la fois présent et absent")
                else:
                    messages.error(request, f"Erreur lors de la mise à jour de l'absence: {error}")

    context = {
        'absence': absence,
    }
    return render(request, 'pages/edit_absence.html', context)

@login_required
@user_passes_test(admin_only)
def mark_presence(request):
    events = SpecialEvent.objects.all()
    MarkPresenceFormSet = formset_factory(ProfilePresenceForm, extra=0)
    extra_time_messages = []

    if request.method == 'POST':
        form = MarkPresenceForm(request.POST)
        formset = MarkPresenceFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            atelier = form.cleaned_data['atelier']

            if date_to < date_from:
                messages.error(request, "La date de fin ne peut pas être antérieure à la date de début.")
                return redirect('absences')

            time_difference = date_to - date_from

            if time_difference > timedelta(hours=3):
                messages.error(request, "La différence entre les dates ne doit pas dépasser 3 heures.")
                return redirect('absences')

            error_occurred = False

            for profile_form in formset:
                profile = profile_form.cleaned_data.get('profile')
                is_present = profile_form.cleaned_data.get('is_present')
                is_absent = profile_form.cleaned_data.get('is_absent')

                if not is_present and not is_absent:
                    continue

                if profile.rattrappage and profile.rattrappage == date_from and profile.rattrappage == date_to:
                    recent_absence = Absence.objects.filter(profile=profile, is_absent=True).order_by('-date_from').first()
                    if recent_absence:
                        recent_absence.delete()

                if profile:
                    if profile.rattrappage and profile.rattrappage >= date_from and profile.rattrappage <= date_to:
                        profile.rattrappage = None
                        profile.save()

                    try:
                        Absence.objects.create(
                            profile=profile,
                            date_from=date_from,
                            date_to=date_to,
                            atelier=atelier,
                            is_present=is_present,
                            is_absent=is_absent
                        )

                        if profile.role == 'teacher' and is_absent:
                            related_profiles = Profile.objects.filter(ateliers=atelier)

                            for related_profile in related_profiles:
                                if related_profile.email:
                                    subject = "Avis d'absence"
                                    context = {
                                        'name': related_profile.name,
                                        'last_name': related_profile.last_name,
                                        'message_body': f"Nous vous informons que Mr/Mme {profile.name} sera absent(e) le {date_from.strftime('%d %B %Y')}. Les deux prochaines leçons auront 30 minutes de temps supplémentaire.\n\n",
                                        'signature': "Chromarium"
                                    }
                                    message = render_to_string('pages/email_template.html', context)
                                    send_email(related_profile.email, subject, message)

                    except Exception as e:
                        messages.error(request, f"Erreur lors de la création de l'absence pour {profile.name}.")
                        error_occurred = True
                        return redirect('absences')

            if not error_occurred:
                messages.success(request, "Présence marquée avec succès.")

            all_profiles = Profile.objects.all()

            for profile in all_profiles:
                profile.calculateFacture()
                profile.calculateSubscriptionFee()
                total_facture = Atelier_Facture.objects.filter(profile=profile).aggregate(Sum('facture'))['facture__sum'] or 0
                if profile.advance < total_facture and total_facture > 0:
                    subject = "Facture"
                    context = {
                    'name': profile.name,
                    'last_name': profile.last_name,
                    'message_body': f"Nous vous informons votre facture est de {total_facture - profile.advance} DT",
                    'signature': "Chromarium"
                    }
                    message = render_to_string('pages/email_template.html', context)
                    send_email(profile.email, subject, message)
                else:
                    pass

            return redirect('absences')
        else:
            messages.error(request, "Formulaire invalide. Veuillez corriger les erreurs.")
    else:
        form = MarkPresenceForm()
        formset = MarkPresenceFormSet()

    profiles = []
    if request.GET.get('atelier'):
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        atelier = get_object_or_404(Atelier, id=request.GET['atelier'])
        selected_group = request.GET.get('groups')

        if selected_group:
            profiles = Profile.objects.filter(ateliers=atelier, groups__id=selected_group).distinct()
        else:
            profiles = Profile.objects.filter(ateliers=atelier).distinct()

        if not profiles:
            messages.error(request, "Aucun profil trouvé pour l'atelier sélectionné.")

        formset = MarkPresenceFormSet(initial=[{'profile': profile} for profile in profiles])
        form = MarkPresenceForm(initial={'date_from': date_from, 'date_to': date_to, 'atelier': atelier, 'groups': selected_group})

        formset = MarkPresenceFormSet(initial=[{'profile': profile} for profile in profiles])
        form = MarkPresenceForm(initial={'date_from': date_from, 'date_to': date_to, 'atelier': atelier, 'groups': selected_group})

        for profile in profiles:
            if profile.role == 'teacher':
                extra_time_message = check_extratime(profile)
                if extra_time_message:
                    extra_time_messages.append(f"{profile.name}: {extra_time_message}")

    for message in extra_time_messages:
        messages.warning(request, message)

    return render(request, 'pages/absences.html', {
        'form': form,
        'formset': formset,
        'profiles': profiles,
        'events': events
    })

@login_required
def view_absences(request):
    events = SpecialEvent.objects.all() 

    absences = None
    form = AbsenceSearchForm()

    if request.method == 'POST':
        form = AbsenceSearchForm(request.POST)
        if form.is_valid():
            matricule = form.cleaned_data['matricule']
            try:
                profile = Profile.objects.get(matricule=matricule)
                absences = Absence.objects.filter(profile=profile).order_by('-date_from')
            except Profile.DoesNotExist:
                absences = None

    return render(request, 'pages/view_absences.html', {
        'form': form,
        'absences': absences,
        'events': events
    })

@login_required
@user_passes_test(admin_only)
def fee_details(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)
    advance = profile.advance

    ateliers_stats = []
    total_presence_count = 0
    total_absence_count = 0

    # Calculate presence and absence counts per atelier
    for atelier in profile.ateliers.all():
        presence_count = Absence.objects.filter(profile=profile, atelier=atelier, is_present=True, is_payed=False).count()
        absence_count = Absence.objects.filter(profile=profile, atelier=atelier, is_absent=True, is_payed=False).count()
        total_presence_count += presence_count
        total_absence_count += absence_count
        ateliers_stats.append({
            'atelier': atelier.name,
            'presence_count': presence_count,
            'absence_count': absence_count,
            'total': presence_count + absence_count
        })

    total_sessions_count = total_presence_count + total_absence_count

    profile.calculateSubscriptionFee()
    profile.calculateFacture()

    subscription_fee = sum(
        atelier_facture.facture 
        for atelier_facture in Atelier_Facture.objects.filter(profile=profile, facture_type='inscription')
    )
    
    facture = sum(atelier_facture.facture for atelier_facture in Atelier_Facture.objects.filter(profile=profile))
    
    total_sum = subscription_fee + facture

    return render(request, 'pages/fee_details.html', {
        'profile': profile,
        'subscription_fee': subscription_fee,
        'facture': facture,
        'total_sum': total_sum,
        'ateliers_stats': ateliers_stats,
        'total_presence_count': total_presence_count,
        'total_absence_count': total_absence_count,
        'total_sessions_count': total_sessions_count,
        'advance': advance
    })

@login_required
@user_passes_test(admin_only)
def calculate_teacher_fee(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)
    atelier = profile.ateliers
    ateliers = Atelier.objects.filter(profile=profile)
    presence_records = Absence.objects.filter(profile=profile, is_present=True, is_calculated=False)
    total_hours_worked = 0.0

    for record in presence_records:
        if record.date_from and record.date_to:
            duration = record.date_to - record.date_from
            hours = duration.total_seconds() / 3600
            total_hours_worked += hours

    absence_count = Absence.objects.filter(profile=profile, is_absent=True, is_calculated=False).count()

    total_fee = Decimal('0.00')
    fee_per_hour = Decimal('0.00')

    for atelier in ateliers:
        if atelier.price_teacher:
            fee_per_hour = atelier.price_teacher
            total_fee += Decimal(total_hours_worked) * fee_per_hour

    total_fee = total_fee.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    formatted_hours_worked = int(total_hours_worked) if total_hours_worked.is_integer() else total_hours_worked
    total_hours = int(total_hours_worked)
    total_minutes = int((total_hours_worked - total_hours) * 60)
    total_count = presence_records.count() + absence_count

    return render(request, 'pages/teacher_fee.html', {
        'profile': profile,
        'presence_count': presence_records.count(),
        'absence_count': absence_count,
        'total_fee': total_fee,
        'fee_per_hour': fee_per_hour, 
        'total_hours_worked': formatted_hours_worked,
        'total_count': total_count,
        'total_hours': total_hours,
        'total_minutes': total_minutes,
        'atelier': atelier,
    })

@login_required
@user_passes_test(admin_only)
def clear_absences_teacher(request, matricule):

    profile = get_object_or_404(Profile, matricule=matricule)
    absences = Absence.objects.filter(profile=profile)
    presence_records = Absence.objects.filter(profile=profile, is_present=True, is_calculated=False)
    total_hours_worked = 0.0

    for record in presence_records:
        if record.date_from and record.date_to:
            duration = record.date_to - record.date_from
            hours = duration.total_seconds() / 3600
            total_hours_worked += hours

    if all(absence.is_calculated for absence in absences):
        messages.error(request, "Paiement refusé : Pas de présences")
        return redirect('teacher_fee', matricule=matricule)

    financial_stats, created = FinancialStats.objects.get_or_create(id=1)  
    financial_stats.total_fee_teacher += profile.calculate_total_fee(total_hours_worked) 
    financial_stats.save() 

    PaymentHistory.objects.create(
    profile=profile,
    amount_paid=profile.calculate_total_fee(total_hours_worked) ,
    payment_date=timezone.now(),
    invoice_type="Confirmation de Payement")

    absences.update(is_calculated=True)
    profile.save()

    messages.success(request, "Paiement effectué avec succès !")

    return redirect('teacher_fee', matricule=matricule)

@login_required
@user_passes_test(admin_only)
def edit_profile(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)
    old_registration_type = profile.registration_type
    old_role = profile.role

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            new_registration_type = form.cleaned_data['registration_type']
            new_ateliers = set(form.cleaned_data['ateliers'])
            new_role = form.cleaned_data['role']  

            if old_role in ['none', 'student'] and new_role == 'teacher':
                messages.error(request, "Un élève ou une personne ne peut pas être enseignant")
                return render(request, 'pages/editprofile.html', {
                    'form': form,
                    'profile': profile,
                })

            if old_role == 'teacher' and new_role in ['student', 'none']:
                messages.error(request, "Un enseignant ne peut pas devenir élève ou n'avoir aucun rôle")
                return render(request, 'pages/editprofile.html', {
                    'form': form,
                    'profile': profile,
                })

            if old_role == 'teacher':
                if new_registration_type != 'none':
                    messages.error(request, "Un enseignant ne peut pas avoir un type d'inscription")
                    return render(request, 'pages/editprofile.html', {
                        'form': form,
                        'profile': profile,
                    })

            if new_role == 'teacher':
                if len(new_ateliers) > 1:
                    messages.error(request, "Un enseignant ne peut être lié qu'à un seul atelier")
                    return render(request, 'pages/editprofile.html', {
                        'form': form,
                        'profile': profile,
                    })

            if (old_registration_type == 'bimestriel' and new_registration_type == 'none'):
                messages.error(request, "Le changement de type d'inscription n'est pas autorisé")
                return render(request, 'pages/editprofile.html', {
                    'form': form,
                    'profile': profile,
                })

            if (old_registration_type == 'annual' and new_registration_type in ['bimestriel', 'none']):
                messages.error(request, "Le changement de type d'inscription n'est pas autorisé")
                return render(request, 'pages/editprofile.html', {
                    'form': form,
                    'profile': profile,
                })

            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profile_details', matricule=matricule)
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'pages/editprofile.html', {
        'form': form,
        'profile': profile,
    })

def terms_and_conditions(request):
    return render(request, 'terms_and_conditions.html')

@login_required
@user_passes_test(admin_only)
def add_atelier(request):
    if request.method == 'POST':
        form = AtelierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('my_ateliers')  
    else:
        form = AtelierForm()
    return render(request, 'pages/add_atelier.html', {'form': form})

@login_required
@user_passes_test(admin_only)
def my_ateliers(request):
    events = SpecialEvent.objects.all() 

    ateliers = Atelier.objects.all()

    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None  

    return render(request, 'pages/my_ateliers.html', {'ateliers': ateliers, 'events': events})

@login_required
@user_passes_test(admin_only)
def edit_atelier(request, pk):
    atelier = get_object_or_404(Atelier, pk=pk)
    if request.method == 'POST':
        form = AtelierForm(request.POST, instance=atelier)
        if form.is_valid():
            form.save()
            return redirect('my_ateliers')
    else:
        form = AtelierForm(instance=atelier)
    return render(request, 'pages/edit_atelier.html', {'form': form})

@login_required
@user_passes_test(admin_only)
def delete_atelier(request, pk):
    atelier = get_object_or_404(Atelier, pk=pk)

    if atelier.default:
        messages.error(request, "Impossible de supprimer un atelier par défaut.")
        return redirect('my_ateliers')  

    if request.method == 'POST':
        atelier.delete()
        messages.success(request, "Atelier supprimé avec succès.")
        return redirect('my_ateliers')

    return redirect('pages/my_ateliers')  

def forgot_password_request(request):
    events = SpecialEvent.objects.all()
    verification_code_sent = False
    request_form = ForgotPasswordRequestForm()
    reset_form = ResetPasswordForm()

    if request.method == 'POST':
        if 'send_code' in request.POST:
            request_form = ForgotPasswordRequestForm(request.POST)
            if request_form.is_valid():
                username = request_form.cleaned_data['username']
                email = request_form.cleaned_data['email']

                try:
                    user = CustomUser.objects.get(username=username, email=email)

                    attempts_key = f"pwd_reset_attempts_{user.id}"
                    suspension_key = f"pwd_reset_suspend_{user.id}"

                    if cache.get(suspension_key):
                        messages.error(request, "Vous avez dépassé le nombre maximum de tentatives. Veuillez réessayer dans 1 heure.")
                        return render(request, 'pages/forgot_password_request.html', {
                            'request_form': request_form,
                            'reset_form': reset_form,
                            'verification_code_sent': verification_code_sent,
                            'events': events,
                        })

                    if not cache.get(attempts_key):
                        cache.add(attempts_key, 0, 3600)
                    attempts = cache.incr(attempts_key)

                    if attempts > 4:
                        cache.set(suspension_key, True, 3600)
                        messages.error(request, "Vous avez dépassé le nombre maximum de tentatives. Veuillez réessayer dans 1 heure.")
                        return render(request, 'pages/forgot_password_request.html', {
                            'request_form': request_form,
                            'reset_form': reset_form,
                            'verification_code_sent': verification_code_sent,
                            'events': events,
                        })

                    verification_code = get_random_string(length=6, allowed_chars='0123456789')
                    expiration_time = timezone.now() + timedelta(minutes=10)

                    VerificationCode.objects.update_or_create(
                        user=user,
                        defaults={
                            'code': verification_code,
                            'expires_at': expiration_time,
                        }
                    )

                    subject = "Code de vérification pour la réinitialisation du mot de passe"
                    context = {
                        'name': user.username,
                        'message_body': f"Votre code de vérification est : {verification_code}",
                        'signature': "Chromarium"
                    }
                    message = render_to_string('pages/email_template.html', context)
                    send_email(user.email, subject, message)

                    messages.success(request, "Le code de vérification a été envoyé à votre adresse email.")
                    verification_code_sent = True

                except CustomUser.DoesNotExist:
                    messages.error(request, "Aucun utilisateur trouvé avec ce nom d'utilisateur et cet email.")

        elif 'reset_password' in request.POST:
            reset_form = ResetPasswordForm(request.POST)
            if reset_form.is_valid():
                username = request.POST.get('username')
                entered_code = reset_form.cleaned_data['verification_code']

                user = get_object_or_404(CustomUser, username=username)
                verification = VerificationCode.objects.filter(user=user).first()

                if verification:
                    if verification.is_valid() and entered_code == verification.code:
                        new_password = reset_form.cleaned_data['new_password1']
                        user.set_password(new_password)
                        user.save()

                        verification.delete()

                        cache_keys = [
                            f"pwd_reset_attempts_{user.id}",
                            f"pwd_reset_suspend_{user.id}"
                        ]
                        cache.delete_many(cache_keys)

                        messages.success(request, "Le mot de passe a été réinitialisé avec succès.")
                    else:
                        messages.error(request, "Le code de vérification est incorrect ou a expiré.")
                else:
                    messages.error(request, "Aucun code de vérification trouvé.")
            else:
                for field, errors in reset_form.errors.items():
                    messages.error(request, errors[0])

    return render(request, 'pages/forgot_password_request.html', {
        'request_form': request_form,
        'reset_form': reset_form,
        'verification_code_sent': verification_code_sent,
        'events': events,
    })

def is_super_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(admin_only)
def statistics_view(request):
    events = SpecialEvent.objects.all()

    total_profiles = Profile.objects.count()
    total_ateliers = Atelier.objects.count()

    financial_stats, created = FinancialStats.objects.get_or_create(id=1)
    total_student_fee = financial_stats.total_fee_student
    total_teacher_fee = financial_stats.total_fee_teacher
    total_difference = total_student_fee - total_teacher_fee

    profits_queryset = Profit_stat.objects.all().values_list('profit', 'last_updated')
    profits = [float(profit[0]) for profit in profits_queryset]
    dates = [profit[1].strftime('%Y-%m-%d') for profit in profits_queryset]

    dates_json = json.dumps(dates)
    profits_json = json.dumps(profits)

    visitor_ips = VisitorIP.objects.all().order_by('-visit_time')

    visitor_ips_count = VisitorIP.objects.filter(is_me=False).order_by('-visit_time')

    total_visitors = visitor_ips_count.count()

    statistics = {
        'total_profiles': total_profiles,
        'total_ateliers': total_ateliers,
        'total_student_fee': total_student_fee,
        'total_teacher_fee': total_teacher_fee,
        'total_difference': total_difference,
        'total_visitors': total_visitors,
    }

    return render(request, 'pages/statistics.html', {
        'statistics': statistics,
        'dates': dates_json,
        'profits': profits_json,
        'events': events,
        'visitor_ips': visitor_ips,
    })

def live_stream(request):
    events = SpecialEvent.objects.all()
    stream = LiveStream.objects.first()

    if request.method == 'POST':
        form = LiveStreamForm(request.POST, instance=stream)
        if form.is_valid():
            form.save()
            return redirect('live_stream')
    else:
        form = LiveStreamForm(instance=stream)

    video_url = ''
    if stream and stream.video_url:
        youtube_url = stream.video_url
        if "watch?v=" in youtube_url:
            video_id = youtube_url.split('watch?v=')[1].split('&')[0]  
        elif "youtu.be/" in youtube_url:
            video_id = youtube_url.split('youtu.be/')[1]
        elif "embed/" in youtube_url:
            video_id = youtube_url.split('embed/')[1]
        else:
            video_id = youtube_url  

        video_url = f"https://www.youtube.com/embed/{video_id}"

    return render(request, 'pages/live_stream.html', {
        'video_url': video_url,
        'form': form,
        'events': events
    })

@login_required
@user_passes_test(admin_only)
def manage_profiles(request):
    events = SpecialEvent.objects.all() 

    if request.method == 'POST':
        if 'create_group' in request.POST:
            form = GroupForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Groupe créé avec succès.")  
                return redirect('manage_profiles')
        elif 'delete_group' in request.POST:
            group_id = request.POST.get('group_id')
            group = get_object_or_404(Group, id=group_id)
            group.delete()
            messages.success(request, "Groupe supprimé avec succès.")  
            return redirect('manage_profiles')
        elif 'update_group' in request.POST:
            group_id = request.POST.get('group_id')
            new_group_name = request.POST.get('new_group_name')
            group = get_object_or_404(Group, id=group_id)

            if Group.objects.filter(name=new_group_name).exists():
                messages.error(request, "Ce nom de groupe existe déjà. Veuillez en choisir un autre.")
            else:
                group.name = new_group_name
                group.save()
                messages.success(request, "Nom du groupe mis à jour avec succès.")

            return redirect('manage_profiles')
        elif 'add_profiles' in request.POST:
            group_id = request.POST.get('group_id')
            selected_profiles = request.POST.getlist('profiles')
            group = get_object_or_404(Group, id=group_id)

            for matricule in selected_profiles:
                profile = get_object_or_404(Profile, matricule=matricule)
                group.profile_set.add(profile)

            messages.success(request, "Profils ajoutés avec succès au groupe.")
            return redirect('manage_profiles')
        elif 'remove_profile' in request.POST:
            group_id = request.POST.get('group_id')
            matricule = request.POST.get('matricule')
            group = get_object_or_404(Group, id=group_id)
            profile = get_object_or_404(Profile, matricule=matricule)
            group.profile_set.remove(profile)
            messages.success(request, "Profil supprimé du groupe avec succès.")
            return redirect('manage_profiles')

    groups = Group.objects.prefetch_related('profile_set').order_by('name')
    form = GroupForm()

    all_profiles = Profile.objects.all()

    return render(request, 'pages/manage_profiles.html', {
        'groups': groups,
        'form': form,
        'events': events,
        'profiles': all_profiles
    })

@login_required
def clear_notifications(request):
    if request.method == 'POST':
        try:
            notifications = Notification.objects.filter(user=request.user, is_cleared=False)
            notifications.update(is_cleared=True, cleared_at=timezone.now())
            return JsonResponse({'status': 'success', 'message': 'Notifications cleared'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@csrf_exempt
def edit_profile_notes(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)

    if request.method == 'POST':
        try:
            if request.body and request.body.decode('utf-8').strip() == '{"notes": ""}':
                profile.notes = ""  
                profile.save()
                return JsonResponse({'success': True, 'notes': profile.notes})

            form = NoteForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                return JsonResponse({'success': True, 'notes': form.instance.notes})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    form = NoteForm(instance=profile)
    return render(request, 'pages/notes.html', {'form': form, 'profile': profile})

@login_required
@user_passes_test(admin_only)
def update_advance(request):
    if request.method == 'POST':
        matricule = request.POST.get('matricule')
        advance = Decimal(request.POST.get('advance', '0'))
        action = request.POST.get('action')  

        if advance < 0:
            messages.error(request, "Le montant ne peut pas être négatif.")
            return redirect('fee_details', matricule=matricule)
        
        try:
            profile = get_object_or_404(Profile, matricule=matricule)

            if action == 'add':
                profile.advance += advance
                PaymentHistory.objects.create(
                    profile=profile,
                    amount_paid=advance,
                    payment_date=timezone.now(),
                    invoice_type='Payement'
                )
                messages.success(request, f"Le solde de {profile.name} a été augmentée avec succès.")

                subject = "Confirmation de Paiement"
                context = {
                    'name': profile.name,
                    'last_name': profile.last_name,
                    'matricule': profile.matricule,  
                    'message_body': f"Félicitations ! Vous avez confirmé le paiement de {advance} DT",
                    'signature': "Chromarium"
                }
                message = render_to_string('pages/email_template.html', context)
                to_email = profile.email
                send_email(to_email, subject, message)

            elif action == 'subtract':
                if profile.advance >= advance:
                    profile.advance -= advance
                    PaymentHistory.objects.create(
                        profile=profile,
                        amount_paid=-advance,
                        payment_date=timezone.now(),
                        invoice_type='Remboursement'
                    )
                    messages.success(request, f"Le solde pour {profile.name} a été remboursé avec succès.")
                    subject = "Confirmation de Paiement"
                    context = {
                        'name': profile.name,
                        'last_name': profile.last_name,
                        'matricule': profile.matricule,  
                        'message_body': f"Félicitations ! Vous avez reçu un remboursement de {advance} DT",
                        'signature': "Chromarium"
                    }
                    message = render_to_string('pages/email_template.html', context)
                    to_email = profile.email
                    send_email(to_email, subject, message)
                else:
                    messages.error(request, "Le montant à soustraire dépasse l'avance disponible.")
            profile.save()

        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour de l'avance: {str(e)}")

        return redirect('fee_details', matricule=matricule)

@login_required
@user_passes_test(admin_only)
def payment_history(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)
    payments = PaymentHistory.objects.filter(profile=profile).order_by('-payment_date')

    if request.method == 'POST':
        data = json.loads(request.body)
        payment_id = data.get('payment_id')
        if payment_id:
            try:
                payment = PaymentHistory.objects.get(id=payment_id, profile=profile)
                payment.delete()
                return JsonResponse({'success': True})
            except PaymentHistory.DoesNotExist:
                return JsonResponse({'success': False, 'error': "Paiement introuvable."})
    return render(request, 'pages/payment_history.html', {'profile': profile, 'payments': payments})

def facture_details(request, profile_matricule):
    profile = get_object_or_404(Profile, matricule=profile_matricule)

    if request.method == 'POST':
        form = ApplyRemiseForm(request.POST, profile=profile)
        if form.is_valid():
            factures = form.cleaned_data['facture_choices']
            remise = form.cleaned_data['remise']
            
            if remise < 0:
                messages.error(request, 'La remise ne peut pas être un montant négatif.')
            
            elif any(remise > facture.facture for facture in factures):
                messages.error(request, 'La remise ne peut pas être supérieure au montant de la facture.')
            
            elif not messages.get_messages(request):
                for facture in factures:
                    facture.facture -= remise
                    facture.save()
                
                return HttpResponseRedirect(f'/profile/{profile_matricule}/facture_details/')
    else:
        form = ApplyRemiseForm(profile=profile)

    atelier_factures = Atelier_Facture.objects.filter(profile=profile).order_by('-created_at')

    return render(request, 'pages/facture_details.html', {
        'profile': profile,
        'atelier_factures': atelier_factures,
        'form': form
    })

@login_required
@csrf_exempt
def manage_users(request):
    events = SpecialEvent.objects.all()
    if request.method == 'POST':
        if request.content_type == 'application/json':
            import json
            try:
                data = json.loads(request.body)
                user_id = data.get('user_id')
                action = data.get('action')

                user = get_object_or_404(CustomUser, pk=user_id)

                if action == 'ban':
                    user.is_banned = True
                elif action == 'unban':
                    user.is_banned = False

                user.save()
                return JsonResponse({'status': 'success'})
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': 'Expected JSON request body'}, status=400)

    users = CustomUser.objects.all().order_by('username')

    has_banned_users = CustomUser.objects.filter(is_banned=True).exists()

    return render(request, 'pages/manage_users.html', {'events': events, 'users': users, 'has_banned_users': has_banned_users})