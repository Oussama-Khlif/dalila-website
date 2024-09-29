from django.utils import timezone
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Profile, Absence, CustomUser, Atelier
from django import forms
from django.core.exceptions import ValidationError
from .models import Profile, Atelier
from django import forms
from django.contrib.auth.forms import SetPasswordForm
from .models import CustomUser
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password']
        labels = {
            'username': 'Nom d’utilisateur',
            'password': 'Mot de Passe',
        }

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        # Remove help texts and any field-specific error messages if desired
        self.fields['username'].help_text = ''
        self.fields['password'].help_text = ''

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'name', 'last_name', 'parent_number', 'date_of_birth',
            'role', 'ateliers', 'profile_picture', 'registration_type'
        ]
        labels = {
            'name': 'Nom',
            'last_name': 'Prénom',
            'parent_number': 'Numéro des parents',
            'date_of_birth': 'Date de naissance',
            'role': 'Rôle',
            'ateliers': 'Ateliers inscrits',
            'profile_picture': 'Photo de profil',
            'registration_type': 'Type d\'inscription',
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'role': forms.Select(),
            'ateliers': forms.CheckboxSelectMultiple(),
            'registration_type': forms.Select(choices=Profile.REGISTRATION_TYPE_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['ateliers'].queryset = Atelier.objects.all()
        
        # Convert date_of_birth to the correct format for the DateInput widget
        if self.instance.date_of_birth:
            self.initial['date_of_birth'] = self.instance.date_of_birth.strftime('%Y-%m-%d')

class ProfileDeletionForm(forms.Form):
    matricule = forms.CharField(
        max_length=100,
        label='Matricule',
        widget=forms.TextInput(attrs={'placeholder': 'CR0001'})
    )

class AbsenceSearchForm(forms.Form):
    matricule = forms.CharField(max_length=100, label='Matricule')

    def search_absences(self):
        matricule = self.cleaned_data['matricule']
        return Absence.objects.filter(profile__matricule=matricule)

class CustomUserCreationForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False, label='Photo de Profil')

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'profile_picture']
        labels = {
            'username': 'Nom d’utilisateur',
            'email': 'Email',
            'password1': 'Mot de passe',
            'password2': 'Confirmer le mot de passe',
        }
        help_texts = {
            'username': '',
            'email': '',
            'password1': '',  # Removing the default password help text
            'password2': '',  # Removing the default confirmation help text
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set custom error messages or remove help texts
        self.fields['password1'].help_text = ''  # Remove password1 help text
        self.fields['password2'].help_text = ''  # Remove password2 help text

class ProfileUpdateForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, label='Photo de Profil')

    class Meta:
        model = CustomUser
        fields = ['profile_picture']

class UsernameUpdateForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label='Nouveau nom d’utilisateur',
        widget=forms.TextInput(attrs={'placeholder': 'Entrez un nouveau nom d’utilisateur'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Mot de passe actuel'}),
        label='Mot de passe'
    )

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Ancien mot de passe'}),
        label='Ancien mot de passe'
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Nouveau mot de passe'}),
        label='Nouveau mot de passe'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmer le nouveau mot de passe'}),
        label='Confirmer le nouveau mot de passe'
    )

class AbsenceAlertForm(forms.Form):
    matricule = forms.CharField(
        max_length=100,
        label='Matricule',
        widget=forms.TextInput(attrs={'placeholder': 'Entrez votre matricule', 'class': 'form-control'})
    )
    
    upcoming_absence_date = forms.DateField(
        widget=forms.TextInput(attrs={'type': 'date'}),
        label='Date de l\'absence à venir'
    )

    atelier = forms.ModelChoiceField(
        queryset=Atelier.objects.all(),  # This will be filtered in the view
        label='Atelier',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    phone_number = forms.CharField(
        max_length=15,
        label='Numéro de téléphone',
        widget=forms.TextInput(attrs={'placeholder': 'Entrez votre numéro de téléphone', 'class': 'form-control'})
    )

    # Custom validation for matricule
    def clean(self):
        cleaned_data = super().clean()
        matricule = cleaned_data.get('matricule')
        phone_number = cleaned_data.get('phone_number')
        atelier = cleaned_data.get('atelier')
        upcoming_absence_date = cleaned_data.get('upcoming_absence_date')

        # Validate the upcoming absence date
        if upcoming_absence_date and upcoming_absence_date < timezone.localdate():
            raise ValidationError("La date de l'absence à venir ne peut pas être dans le passé.")

        try:
            # Get the profile by matricule
            profile = Profile.objects.get(matricule=matricule)

            # Validate the phone number
            if profile.parent_number != phone_number:
                raise ValidationError("Le numéro de téléphone ne correspond pas à nos enregistrements.")

            # Validate if the atelier is related to the profile
            if atelier not in profile.ateliers.all():
                raise ValidationError("L'atelier ne correspond pas à ceux enregistrés avec ce matricule.")

        except Profile.DoesNotExist:
            raise ValidationError("Aucun profil trouvé avec le matricule donné.")

        return cleaned_data

class RattrappageForm(forms.Form):
    rattrappage = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False,
        help_text="Date et heure pour toute classe ou séance de rattrapage"
    )

class MarkPresenceForm(forms.Form):
    date_from = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Début Séance'
    )
    date_to = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label="Fin Séance"
    )
    atelier = forms.ModelChoiceField(
        queryset=Atelier.objects.all(),
        label='Atelier',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class ProfilePresenceForm(forms.ModelForm):
    class Meta:
        model = Absence
        fields = ['profile', 'is_present', 'is_absent', 'is_archived']

class RefundForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['refund']
        widgets = {
            'refund': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Montant du remboursement'}),
        }
        help_texts = {
            'refund': 'Montant remboursé au profil.',  # Translated help text
        }

class AtelierForm(forms.ModelForm):
    class Meta:
        model = Atelier
        fields = ['name', 'price', 'price_teacher', 'duration']
        labels = {
            'name': 'Nom de l\'atelier',
            'price': 'Prix',
            'price_teacher': 'Prix pour enseignant',
            'duration': 'Durée (en minutes)',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Nom de l\'atelier'}),
            'price': forms.NumberInput(attrs={'placeholder': 'Prix'}),
            'price_teacher': forms.NumberInput(attrs={'placeholder': 'Prix pour enseignant'}),
            'duration': forms.NumberInput(attrs={'placeholder': 'Durée en minutes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.default:  # Check if instance is set and default is True
            self.fields['name'].disabled = True  # Disable name field

class ForgotPasswordForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Nouveau mot de passe"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmer le nouveau mot de passe"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.error_messages = {'required': _('Ce champ est obligatoire')}

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if username:
            try:
                user = CustomUser.objects.get(username=username)
            except CustomUser.DoesNotExist:
                raise ValidationError("Aucun utilisateur avec ce nom d'utilisateur")

        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', ValidationError(
                "Les mots de passe ne correspondent pas",
                code='password_mismatch'
            ))
        
        return cleaned_data

    def reset_password(self):
        username = self.cleaned_data['username']
        new_password = self.cleaned_data['new_password1']
        user = CustomUser.objects.get(username=username)
        user.set_password(new_password)
        user.save()

class RemiseForm(forms.Form):
    remise = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        required=True,
        label="Remise en pourcentage",
        help_text="%"
    )
