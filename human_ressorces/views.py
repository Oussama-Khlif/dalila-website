from datetime import timezone
from decimal import Decimal
from django import forms
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import formset_factory
from django.shortcuts import redirect, render, get_object_or_404
from .models import Profile, Absence, Atelier
from pages.views import SpecialEvent
from django.db.models import Max, Prefetch
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.forms import formset_factory
from .forms import MarkPresenceForm, ProfilePresenceForm  # Ensure ProfilePresenceForm is updated as needed
from .models import Absence, Profile, Atelier
from django.shortcuts import render, get_object_or_404
from decimal import Decimal
from .models import Profile, Absence  # Adjust the import based on your project structure
from decimal import Decimal
from decimal import Decimal, ROUND_DOWN
from django.contrib import messages
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib import messages
from .forms import ForgotPasswordForm
from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Atelier
from django.db.models import Q
from .forms import (
    AbsenceSearchForm,
    AtelierForm,
    MarkPresenceForm,
    ProfilePresenceForm,
    AbsenceAlertForm,
    RattrappageForm,
    ProfileForm,
    CustomUserCreationForm,
    ProfileUpdateForm,
    RefundForm,
    RemiseForm,
    UsernameUpdateForm,
    CustomPasswordChangeForm
)

def admin_only(user):
    return user.is_superuser or user.username == 'admin'

@login_required
def myaccount(request):
    # Fetch the latest special event
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None

    # Initialize forms to None
    profile_form = None
    username_form = None
    password_form = None

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Photo de profil mise à jour avec succès.')
                return redirect('myaccount')
        elif 'update_username' in request.POST:
            username_form = UsernameUpdateForm(request.POST)
            if username_form.is_valid() and request.user.check_password(username_form.cleaned_data['password']):
                request.user.username = username_form.cleaned_data['username']
                request.user.save()
                messages.success(request, 'Nom d’utilisateur mis à jour avec succès.')
                return redirect('myaccount')
        elif 'update_password' in request.POST:
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Mot de passe changé avec succès.')
                return redirect('myaccount')
        elif 'delete_profile_picture' in request.POST:
            # Delete profile picture logic
            user = request.user
            if user.profile_picture:  # Assuming 'profile_picture' is the field name
                user.profile_picture.delete()
                user.save()
                messages.success(request, 'Photo de profil supprimée avec succès.')
            return redirect('myaccount')

    # Ensure that forms are initialized if not POST or if certain conditions are not met
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
        'event': event  # Add event context here
    })

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
        else:
            # Handle form errors manually
            if form.errors.get('username'):
                messages.error(request, form.errors['username'][0])
            if form.errors.get('email'):
                messages.error(request, form.errors['email'][0])
            if form.errors.get('password1'):
                messages.error(request, form.errors['password1'][0])
            if form.errors.get('password2'):
                messages.error(request, form.errors['password2'][0])
    
    else:
        form = CustomUserCreationForm()

    return render(request, 'pages/register.html', {'form': form})

@login_required
@user_passes_test(admin_only)
def myclients(request):
    # Fetch the latest special event
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None

    # Fetch profiles ordered by associated atelier name
    profiles = Profile.objects.prefetch_related('ateliers').annotate(
        atelier_name=Max('ateliers__name')  # Use Max to get the associated atelier name
    ).order_by('atelier_name')

    # Initialize emoji variables
    extra_time_emoji = ""
    refund_emoji = ""
    facture_emoji = ""
    rattrappage_emoji = ""
    alert_emoji = ""

    for profile in profiles:
        # Initialize profile-specific emoji variables
        profile_extra_time_emoji = ""
        profile_refund_emoji = ""
        profile_facture_emoji = ""
        profile_rattrappage_emoji = ""
        profile_alert_emoji = ""

        # Check for extra time
        if check_extratime(profile):
            profile_extra_time_emoji = "🕒"  # Replace with appropriate emoji

        if profile.absence_alert:
            profile_alert_emoji = "⚠️"  # Replace with appropriate emoji

        # Check for refund
        if profile.refund and profile.refund > 0:
            profile_refund_emoji = "💸"  # Replace with appropriate emoji

        # Check if facture is available
        total_absences_count = Absence.objects.filter(profile=profile, is_archived=False).count()
        if total_absences_count >= 4 or profile.subscription_fee > 0.0:
            profile_facture_emoji = "💵"  # Replace with appropriate emoji

        # Check for rattrappage message
        if profile.rattrappage:
            profile_rattrappage_emoji = "📅"  # Replace with appropriate emoji

        # Append profile-specific emojis
        profile.extra_time_emoji = profile_extra_time_emoji
        profile.refund_emoji = profile_refund_emoji
        profile.facture_emoji = profile_facture_emoji
        profile.rattrappage_emoji = profile_rattrappage_emoji
        profile.alert_emoji = profile_alert_emoji

    return render(request, 'pages/myclients.html', {
        'profiles': profiles,
        'event': event,  # Add event context here
    })

@login_required
@user_passes_test(admin_only)
def addprofile(request):
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None

    creation_message = None

    if request.method == 'POST':
        if 'addprofile_submit' in request.POST:
            profile_form = ProfileForm(request.POST, request.FILES)
            
            if profile_form.is_valid():
                profile = profile_form.save(commit=False)

                # Check if the profile is a teacher and if more than one atelier is linked
                if profile.role == 'teacher':
                    if profile_form.cleaned_data['ateliers'].count() > 1:
                        creation_message = "Un enseignant ne peut être lié qu'à un seul atelier."
                    elif profile.registration_type != 'none':
                        creation_message = "Un enseignant ne peut pas avoir un type d'inscription."
                    else:
                        # Save teacher profile
                        profile.registration_type = 'none'
                        profile.save()
                        profile_form.save_m2m()
                        creation_message = "Profil enseignant créé avec succès."
                        profile_form = ProfileForm()  # Reset form after successful submission
                else:
                    # Save non-teacher profile
                    profile.save()  # Save the profile with the adjusted subscription fee
                    profile_form.save_m2m()  # Save ManyToMany relationships
                    creation_message = "Profil créé avec succès."
                    profile_form = ProfileForm()  # Reset form after successful submission
            else:
                creation_message = "Erreur lors de la création du profil."

            return render(request, 'pages/addprofile.html', {
                'profile_form': profile_form,
                'creation_message': creation_message,
                'event': event
            })

    else:
        profile_form = ProfileForm()

    return render(request, 'pages/addprofile.html', {
        'profile_form': profile_form,
        'event': event
    })

@login_required
@user_passes_test(admin_only)
def profile_details(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)

    if request.method == 'POST' and 'delete_absence' in request.POST:
        # Clear the absence-related fields
        profile.absence_alert = None
        profile.atelier_absent = None
        profile.upcoming_absence_date = None
        profile.save()

        messages.success(request, "Les informations d'absence ont été supprimées avec succès.")
        return redirect('profile_details', matricule=matricule)  # Redirect to the same profile page after deletion

    # Count the number of presence records
    presence_count = Absence.objects.filter(profile=profile, is_present=True, is_archived=False).count()

    # Total number of absences
    total_absences_count = Absence.objects.filter(profile=profile, is_archived=False).count()

    # Fetch the last absence based on date_from
    last_absence = Absence.objects.filter(profile=profile).order_by('-date_from').first()

    # Check for extra time
    extra_time = check_extratime(profile)

    # Reset the rattrappage if the absence or presence falls on or after the rattrappage day
    if profile.rattrappage and last_absence:
        rattrappage_date = profile.rattrappage.date()  # Extract only the date from DateTimeField
        absence_date = last_absence.date_from.date()  # Extract the date of the absence

        # If absence or presence is on or after the rattrappage date
        if absence_date >= rattrappage_date:
            profile.rattrappage = None
            profile.save()
            messages.info(request, "Le rattrappage a été réinitialisé car une absence/presence est survenue après le jour de rattrappage.")

    # Determine if there is a refund message
    refund_message = None
    if profile.refund and profile.refund > 0:
        refund_message = f"💸 {profile.name} sera remboursé de {profile.refund} DT."

    # Determine if facture is available
    facture_message = None
    if total_absences_count >= 4 or profile.subscription_fee > 0.0:
        facture_message = "💵 Facture disponible"

    # Determine if there is a rattrappage message
    rattrappage_message = None
    if profile.rattrappage:
        rattrappage_message = f"📅 Rattrappage est fixé le {profile.rattrappage.strftime('%d-%m-%Y')}."

    return render(request, 'pages/details.html', {
        'profile': profile,
        'presence_count': presence_count,
        'total_absences_count': total_absences_count,
        'extra_time': extra_time,
        'refund_message': refund_message,
        'facture_message': facture_message,
        'rattrappage_message': rattrappage_message,
    })

def check_extratime(profile):
    if profile.role == 'teacher':
        # Get the most recent absence record
        last_absence = Absence.objects.filter(
            profile=profile,
            is_absent=True,
            is_archived=False  # Exclude archived absences
        ).order_by('-date_from').first()  # Use 'date_from' here
        
        if last_absence:
            # Get the two subsequent records after the last absence
            subsequent_records = Absence.objects.filter(
                profile=profile,
                date_from__gt=last_absence.date_from,  # Filter by 'date_from'
                is_archived=False  # Exclude archived absences
            ).order_by('date_from')[:2]  # Use 'date_from' here
            
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
        return redirect('myclients')  # Redirect to the client list page after deletion

    return render(request, 'pages/details.html', {
        'profile': profile,
    })

@login_required
def absence_alert(request):
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
            # Handle form errors but do not let them render automatically in the form
            for field, errors in alert_form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")

            # Optionally clear the errors in the form
            alert_form.errors.clear()  # Clear the errors to avoid showing unstyled errors

    else:
        alert_form = AbsenceAlertForm()

    return render(request, 'pages/absence_alert.html', {
        'alert_form': alert_form,
    })

@login_required
def calculate_total_sum(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)
    
    # Exclude archived absences
    presence_count = Absence.objects.filter(profile=profile, is_present=True, is_archived=False).count()
    total_absences_count = Absence.objects.filter(profile=profile, is_absent=True, is_archived=False).count()

    # Calculate subscription fee and facture
    profile.calculateSubscriptionFee()
    profile.calculateFacture()

    # Calculate total sum (subscription fee + updated facture)
    total_sum = profile.subscription_fee + profile.facture

    return render(request, 'pages/fee_details.html', {
        'profile': profile,
        'subscription_fee': profile.subscription_fee,
        'facture': profile.facture,
        'total_sum': total_sum,
        'presence_count': presence_count,
        'total_absences_count': total_absences_count,
    })

@login_required
@user_passes_test(admin_only)
def clear_absences(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)

    # Count the number of unchecked absence records for the profile
    unchecked_absences_count = Absence.objects.filter(profile=profile, is_archived=False).count()

    # Deny the request if there are fewer than 4 unchecked absences
    if unchecked_absences_count < 4:
        messages.error(request, "Paiement refusé ! moins de 4 séances disponibles.")
        return redirect('fee_details', matricule=matricule)

    # Fetch the next four oldest unchecked absence records for the profile
    oldest_absences = Absence.objects.filter(profile=profile, is_archived=False).order_by('date_from').values_list('id', flat=True)[:4]

    # Archive these absences by updating is_archived to True
    Absence.objects.filter(id__in=oldest_absences).update(is_archived=True)

    # Reset refund value to 0
    profile.refund = Decimal('0.00')
    profile.remise = Decimal('0')
    profile.save()

    # Add a success message
    messages.success(request, "Paiement de 4 séances confirmé !")

    return redirect('fee_details', matricule=matricule)

@login_required
@user_passes_test(admin_only)
def clear_absences_fee(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)

    # Determine the number of absences to fetch based on the registration type
    if profile.registration_type == 'bimestriel':
        count = 8
        required_absences = 8
    elif profile.registration_type == 'annuel':
        count = 12
        required_absences = 12
    else:
        count = 0  # Default to 0 if the registration type is unknown
        required_absences = 0

    # Check the number of unpaid absences
    unpaid_absences_count = Absence.objects.filter(profile=profile, is_payed=False).count()

    if unpaid_absences_count < required_absences:
        messages.error(request, f"Paiement refusé. Il doit y avoir au moins {required_absences} séances non payées.")
        return redirect('fee_details', matricule=matricule)

    # Fetch the oldest absence records for the profile that are not paid
    oldest_absences = Absence.objects.filter(profile=profile, is_payed=False).order_by('date_from').values_list('id', flat=True)[:count]

    # Update these absences by setting is_payed to True
    Absence.objects.filter(id__in=oldest_absences).update(is_payed=True)

    # Add a success message
    messages.success(request, "Paiement d'inscription confirmé")

    return redirect('fee_details', matricule=matricule)

@login_required
@user_passes_test(admin_only)
def reset_fee_and_facture(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)

    # Reset the subscription fee and facture to 0
    profile.subscription_fee = Decimal('0.00')
    profile.facture = Decimal('0.00')
    profile.save()

    # Add a success message or redirect if necessary
    return redirect('fee_details', matricule=profile.matricule)

@login_required
def rattrappage_view(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)

    if request.method == 'POST':
        rattrappage_form = RattrappageForm(request.POST)
        
        if rattrappage_form.is_valid():
            rattrappage_datetime = rattrappage_form.cleaned_data.get('rattrappage')
            
            # Check if the date is older than today
            today = timezone.now()
            if rattrappage_datetime and rattrappage_datetime < today.replace(hour=0, minute=0, second=0, microsecond=0):
                messages.error(request, "La date de rattrapage ne peut pas être antérieure à aujourd'hui.")
                return render(request, 'pages/rattrappage.html', {
                    'form': rattrappage_form,
                    'matricule': matricule,
                    'profile': profile,
                })

            # Set the rattrappage datetime
            if rattrappage_datetime is not None:
                profile.rattrappage = rattrappage_datetime
            else:
                profile.rattrappage = None

            # Reset the absence_alert date
            profile.absence_alert = None

            # Save the changes
            profile.save()

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
def absences_details(request, matricule):
    # Get the profile object
    profile = get_object_or_404(Profile, matricule=matricule)
    
    form = AbsenceSearchForm(initial={'matricule': matricule})
    
    # Order absences by the most recent date (assuming date_from is the relevant field)
    absences = Absence.objects.filter(profile__matricule=matricule).order_by('-date_from')

    # Handle the form submission
    if request.method == 'POST':
        form = AbsenceSearchForm(request.POST)
        if form.is_valid():
            absences = form.search_absences().order_by('-date_from')

    context = {
        'form': form,
        'absences': absences,
        'profile': profile,
    }
    return render(request, 'pages/absences_details.html', context)

@login_required
@user_passes_test(admin_only)
def mark_presence(request):
    MarkPresenceFormSet = formset_factory(ProfilePresenceForm, extra=0)

    if request.method == 'POST':
        form = MarkPresenceForm(request.POST)
        formset = MarkPresenceFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            atelier = form.cleaned_data['atelier']

            print(f"Date From: {date_from}, Date To: {date_to}, Atelier: {atelier}")

            for profile_form in formset:
                profile = profile_form.cleaned_data.get('profile')
                is_present = profile_form.cleaned_data.get('is_present')
                is_absent = profile_form.cleaned_data.get('is_absent')

                if profile:
                    # Handle rattrappage logic if needed
                    if profile.rattrappage and profile.rattrappage >= date_from and profile.rattrappage <= date_to:
                        profile.rattrappage = None
                        profile.save()

                    # Create Absence record
                    try:
                        Absence.objects.create(
                            profile=profile,
                            date_from=date_from,
                            date_to=date_to,
                            atelier=atelier,
                            is_present=is_present,
                            is_absent=is_absent
                        )
                        print(f"Created absence for {profile.name}")
                    except Exception as e:
                        print(f"Error creating absence: {e}")
                        messages.error(request, f"Erreur lors de la création de l'absence pour {profile.name}.")
                        return redirect('absences')

            messages.success(request, "Présence marquée avec succès.")
            return redirect('absences')
        else:
            print(f"Form errors: {form.errors}, Formset errors: {formset.errors}")
            messages.error(request, "Formulaire invalide. Veuillez corriger les erreurs.")
    else:
        form = MarkPresenceForm()
        formset = MarkPresenceFormSet()

    profiles = []
    if request.GET.get('atelier'):
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        atelier = get_object_or_404(Atelier, id=request.GET['atelier'])
        profiles = Profile.objects.filter(ateliers=atelier)
        formset = MarkPresenceFormSet(initial=[{'profile': profile} for profile in profiles])
        form = MarkPresenceForm(initial={'date_from': date_from, 'date_to': date_to, 'atelier': atelier})

    return render(request, 'pages/absences.html', {
        'form': form,
        'formset': formset,
        'profiles': profiles,
    })

@login_required
def view_absences(request):
    absences = None
    form = AbsenceSearchForm()

    if request.method == 'POST':
        form = AbsenceSearchForm(request.POST)
        if form.is_valid():
            matricule = form.cleaned_data['matricule']
            try:
                profile = Profile.objects.get(matricule=matricule)
                absences = Absence.objects.filter(profile=profile).order_by('-date_from')  # Order by recent date
            except Profile.DoesNotExist:
                absences = None  # Or handle as needed

    return render(request, 'pages/view_absences.html', {
        'form': form,
        'absences': absences
    })

@login_required
def fee_details(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)
    remise_applied = profile.remise > 0

    # Exclude archived absences
    presence_count = Absence.objects.filter(profile=profile, is_present=True, is_archived=False).count()
    total_absences_count = Absence.objects.filter(profile=profile,is_absent=True, is_archived=False).count()  # Total number of non-archived absences

    # Calculate subscription fee and facture
    profile.calculateSubscriptionFee()
    profile.calculateFacture()
    
    # Determine if a refund message should be displayed
    refund_message = ""
    if profile.refund > 0:
        refund_message = "Ce profil sera remboursé lors du prochain paiement."

    # Fetch updated values
    subscription_fee = profile.subscription_fee
    facture = profile.facture
    total_sum = subscription_fee + facture

    # Calculate the total count of absences and presences
    total_presence_absence_count = presence_count + total_absences_count
    
    return render(request, 'pages/fee_details.html', {
        'profile': profile,
        'subscription_fee': subscription_fee,
        'facture': facture,
        'total_sum': total_sum,
        'presence_count': presence_count,  # Pass it here too
        'total_absences_count': total_absences_count,  # Pass total absences count excluding archived ones
        'total_presence_absence_count': total_presence_absence_count,  # Pass the total count of absences and presences
        'refund_message': refund_message,  # Add refund_message to context
        'remise_applied': remise_applied

    })

@login_required
def refund_profile(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)

    if request.method == 'POST':
        if 'reset_refund' in request.POST:
            # Reset the refund value to 0
            profile.refund = 0
            profile.absence_alert = None  # Reset the absence_alert field if needed
            profile.save()
            message = "Le montant de remboursement a été réinitialisé"
            form = RefundForm(instance=profile)
        else:
            form = RefundForm(request.POST, instance=profile)
            if form.is_valid():
                refund_amount = form.cleaned_data['refund']
                profile.refund = refund_amount
                profile.absence_alert = None  # Reset the absence_alert field if needed
                profile.save()
                message = "Le remboursement a été enregistré avec succès."
            else:
                message = "Veuillez corriger les erreurs dans le formulaire."
    else:
        form = RefundForm(instance=profile)
        message = ""

    context = {
        'form': form,
        'profile': profile,
        'message': message,
    }
    return render(request, 'pages/refund_profile.html', context)

@login_required
def calculate_teacher_fee(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)
    atelier = profile.ateliers
    
    # Assuming each profile is associated with one or more Ateliers, we fetch them
    ateliers = Atelier.objects.filter(profile=profile)  # Adjust this according to your relationship

    # Filter presence records with is_present=True and is_archived=False
    presence_records = Absence.objects.filter(profile=profile, is_present=True, is_archived=False)
    
    # Calculate total hours worked manually
    total_hours_worked = 0.0
    for record in presence_records:
        if record.date_from and record.date_to:
            # Calculate the difference in hours
            duration = record.date_to - record.date_from
            hours = duration.total_seconds() / 3600  # Convert seconds to hours
            total_hours_worked += hours  # Add to total hours worked
    
    # Count the total absences with is_archived=False
    absence_count = Absence.objects.filter(profile=profile, is_absent=True, is_archived=False).count()

    # Initialize total fee and fee_per_hour
    total_fee = Decimal('0.00')  # Use Decimal for total fee
    fee_per_hour = Decimal('0.00')  # Default value

    for atelier in ateliers:
        if atelier.price_teacher:  # Only calculate if price_teacher is not None
            fee_per_hour = atelier.price_teacher
            # Convert total_hours_worked to Decimal before multiplication
            total_fee += Decimal(total_hours_worked) * fee_per_hour

    # Round total_fee to 2 decimal places
    total_fee = total_fee.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    # Format hours worked for display
    formatted_hours_worked = int(total_hours_worked) if total_hours_worked.is_integer() else total_hours_worked

    # Convert total_hours_worked to hours and minutes
    total_hours = int(total_hours_worked)  # Get whole hours
    total_minutes = int((total_hours_worked - total_hours) * 60)  # Get remaining minutes

    # New variable: total presence and absence count
    total_count = presence_records.count() + absence_count

    return render(request, 'pages/teacher_fee.html', {
        'profile': profile,
        'presence_count': presence_records.count(),
        'absence_count': absence_count,
        'total_fee': total_fee,  # Pass total fee as Decimal
        'fee_per_hour': fee_per_hour,  # Pass fee per hour to the template
        'total_hours_worked': formatted_hours_worked,
        'total_count': total_count,  # Pass the sum of presence and absence counts
        'total_hours': total_hours,  # Pass total hours to the template
        'total_minutes': total_minutes,  # Pass total minutes to the template
        'atelier': atelier,
    })

@login_required
@user_passes_test(admin_only)
def clear_absences_teacher(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)

    # Get all absences for the profile
    absences = Absence.objects.filter(profile=profile)

    # Check if all absences are archived
    if all(absence.is_archived for absence in absences):
        messages.error(request, "Paiement refusé : Pas de présences")
        return redirect('teacher_fee', matricule=matricule)

    # Archive absences instead of deleting them
    absences.update(is_archived=True)

    # Reset refund value to 0
    profile.refund = Decimal('0.00')
    profile.save()

    # Add success message
    messages.success(request, "Paiement effectué avec succès !")

    return redirect('teacher_fee', matricule=matricule)

@login_required
def edit_profile(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Check if the profile is a teacher
            if profile.role == 'teacher':
                # Restriction on the number of ateliers linked
                if form.cleaned_data['ateliers'].count() > 1:
                    messages.error(request, "Un enseignant ne peut être lié qu'à un seul atelier.")
                    form.add_error('ateliers', "Un enseignant ne peut être lié qu'à un seul atelier.")
                
                # Restriction on registration type
                if form.cleaned_data['registration_type'] != 'none':
                    messages.error(request, "Un enseignant ne peut pas avoir un type d'inscription.")
                    form.add_error('registration_type', "Un enseignant ne peut pas avoir un type d'inscription.")
            
            if not form.errors:  # Only save if there are no errors
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

def add_atelier(request):
    if request.method == 'POST':
        form = AtelierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('my_ateliers')  # Redirect to a page showing the list of ateliers or another page
    else:
        form = AtelierForm()
    return render(request, 'pages/add_atelier.html', {'form': form})

def my_ateliers(request):
    ateliers = Atelier.objects.all()
    return render(request, 'pages/my_ateliers.html', {'ateliers': ateliers})

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

def delete_atelier(request, pk):
    atelier = get_object_or_404(Atelier, pk=pk)

    # Check if the atelier is marked as default
    if atelier.default:
        messages.error(request, "Impossible de supprimer un atelier par défaut.")
        return redirect('my_ateliers')  # Redirect back to the list of ateliers

    if request.method == 'POST':
        atelier.delete()
        messages.success(request, "Atelier supprimé avec succès.")
        return redirect('my_ateliers')

    return redirect('pages/my_ateliers')  # Just in case it's accessed via GET (shouldn't happen)

def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            try:
                form.reset_password()
                messages.success(request, "Le mot de passe a été réinitialisé avec succès.")
                # Reinitialize the form to clear the fields after successful submission
                form = ForgotPasswordForm()
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = ForgotPasswordForm()

    return render(request, 'pages/forgot_password.html', {'form': form})

@login_required
def remise_profile(request, matricule):
    profile = get_object_or_404(Profile, matricule=matricule)

    if request.method == 'POST':
        form = RemiseForm(request.POST)
        if form.is_valid():
            # Get the remise value from the form
            profile.remise = form.cleaned_data['remise']
            profile.save()
            messages.success(request, "La remise a été mise à jour avec succès.")
            return redirect('profile_details', matricule=matricule)
    else:
        form = RemiseForm(initial={'remise': profile.remise})

    return render(request, 'pages/remise_profile.html', {
        'form': form,
        'profile': profile,
    })