from django.utils import timezone
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Atelier_Facture, LiveStream, Profile, Absence, CustomUser, Atelier
from .models import Profile, Group
from django.contrib.auth.forms import AuthenticationForm
from django import forms             
from .models import Group

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Nom d’utilisateur",
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-field',  
            'placeholder': 'Entrez votre nom d’utilisateur'  
        })
    )
    password = forms.CharField(
        label="Mot de Passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-field',  
            'placeholder': 'Entrez votre mot de passe'  
        })
    )

class ProfileDeletionForm(forms.Form):
    matricule = forms.CharField(
        max_length=100,
        label='Matricule',
        widget=forms.TextInput(attrs={
            'placeholder': 'CR0001', 
            'class': 'form-control'  
        })
    )

class AbsenceSearchForm(forms.Form):
    matricule = forms.CharField(
        max_length=100,
        label='Matricule',
        widget=forms.TextInput(attrs={
            'placeholder': 'Entrez votre matricule', 
            'class': 'form-control'  
        })
    )

    def search_absences(self):
        matricule = self.cleaned_data['matricule']
        return Absence.objects.filter(profile__matricule=matricule)

class CustomUserCreationForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False, label='Photo de Profil')

    username = forms.CharField(required=True, label='Nom d’utilisateur')
    email = forms.EmailField(required=True, label='Email')
    password1 = forms.CharField(required=True, label='Mot de passe', widget=forms.PasswordInput)
    password2 = forms.CharField(required=True, label='Confirmer le mot de passe', widget=forms.PasswordInput)

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
            'password1': '',
            'password2': '',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': "Entrez votre nom d'utilisateur"
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': "Entrez votre adresse email"
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Entrez un mot de passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmez votre mot de passe'
        })
        self.fields['profile_picture'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': "Téléchargez votre photo de profil (facultatif)"
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if CustomUser.objects.filter(email=email, is_active=True).exists():
            raise ValidationError("Cette adresse email est déjà utilisée par un utilisateur actif. Veuillez en choisir une autre.")

        return email

class ProfileUpdateForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, label='Photo de Profil')

    class Meta:
        model = CustomUser
        fields = ['profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_picture'].widget.attrs.update({'class': 'form-control'})

class UsernameUpdateForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label='Nouveau nom d’utilisateur',
        widget=forms.TextInput(attrs={
            'placeholder': 'Entrez un nouveau nom d’utilisateur', 
            'class': 'form-control'  
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mot de passe actuel', 
            'class': 'form-control'  
        }),
        label='Mot de passe'
    )

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Ancien mot de passe', 
            'class': 'form-control'  
        }),
        label='Ancien mot de passe'
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Nouveau mot de passe', 
            'class': 'form-control'  
        }),
        label='Nouveau mot de passe'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirmer le nouveau mot de passe', 
            'class': 'form-control'  
        }),
        label='Confirmer le nouveau mot de passe'
    )

class AbsenceAlertForm(forms.Form):
    matricule = forms.CharField(
        max_length=100,
        label='Matricule',
        widget=forms.TextInput(attrs={
            'placeholder': 'Entrez votre matricule',
            'class': 'form-control'  
        })
    )

    upcoming_absence_date = forms.DateField(
        label='Date de l\'absence à venir',
        widget=forms.TextInput(attrs={
            'type': 'date', 
            'class': 'form-control'  
        })
    )

    atelier = forms.ModelChoiceField(
        queryset=Atelier.objects.all(),  
        label='Atelier',
        widget=forms.Select(attrs={
            'class': 'form-control'  
        })
    )

    phone_number = forms.CharField(
        max_length=15,
        label='Numéro de téléphone',
        widget=forms.TextInput(attrs={
            'placeholder': 'Entrez votre numéro de téléphone', 
            'class': 'form-control'  
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        matricule = cleaned_data.get('matricule')
        phone_number = cleaned_data.get('phone_number')
        atelier = cleaned_data.get('atelier')
        upcoming_absence_date = cleaned_data.get('upcoming_absence_date')

        if upcoming_absence_date and upcoming_absence_date < timezone.localdate():
            raise ValidationError("La date de l'absence à venir ne peut pas être dans le passé.")

        try:
            profile = Profile.objects.get(matricule=matricule)

            if profile.parent_number != phone_number:
                raise ValidationError("Le numéro de téléphone ne correspond pas à nos enregistrements.")

            if atelier not in profile.ateliers.all():
                raise ValidationError("L'atelier ne correspond pas à ceux enregistrés avec ce matricule.")

        except Profile.DoesNotExist:
            raise ValidationError("Aucun profil trouvé avec le matricule donné.")

        return cleaned_data

class RattrappageForm(forms.Form):
    rattrappage = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'  
        }),
        required=False,
        help_text="Date et heure pour toute classe ou séance de rattrapage"
    )

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'name', 
            'last_name', 
            'email',  
            'parent_number', 
            'date_of_birth',
            'role', 
            'registration_type',
            'ateliers', 
            'profile_picture',
            'groups',  
        ]
        labels = {
            'name': 'Nom',
            'last_name': 'Prénom',
            'email': 'Email',  
            'parent_number': 'Numéro des parents',
            'date_of_birth': 'Date de naissance',
            'role': 'Rôle',
            'registration_type': 'Type d\'inscription',
            'ateliers': 'Ateliers inscrits',
            'profile_picture': 'Photo de profil',
            'groups': 'Groupes',  
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez votre nom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez votre prénom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@example.com'}),
            'parent_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro de téléphone des parents'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'role': forms.Select(attrs={'class': 'form-control'}),  
            'registration_type': forms.Select(choices=Profile.REGISTRATION_TYPE_CHOICES, attrs={'class': 'form-control'}),
            'ateliers': forms.CheckboxSelectMultiple(attrs={'class': 'custom-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),  
            'groups': forms.CheckboxSelectMultiple(),  
        }

    def clean_ateliers(self):
        ateliers = self.cleaned_data.get('ateliers')
        if not ateliers or len(ateliers) < 1:
            raise forms.ValidationError("Le profil doit être inscrit à au moins un atelier.")
        return ateliers

class MarkPresenceForm(forms.Form):
    date_from = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'  
        }),
        label='Début Séance'
    )
    date_to = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'  
        }),
        label="Fin Séance"
    )
    atelier = forms.ModelChoiceField(
        queryset=Atelier.objects.all(),
        label='Atelier',
        widget=forms.Select(attrs={'class': 'form-control'})  
    )
    groups = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label='Groupe',
        widget=forms.Select(attrs={'class': 'form-control'}),  
        required=False  
    )

class ProfilePresenceForm(forms.ModelForm):
    class Meta:
        model = Absence
        fields = ['profile', 'is_present', 'is_absent']
        widgets = {
            'profile': forms.Select(),
            'is_present': forms.CheckboxInput(),
            'is_absent': forms.CheckboxInput(),
        }
        labels = {
            'profile': 'Profil',
            'is_present': 'Présent',
            'is_absent': 'Absent',
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
        if self.instance and self.instance.default:  
            self.fields['name'].disabled = True  

class ForgotPasswordRequestForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,  
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        required=True,  
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')

        if not username or not email:
            raise ValidationError(_('Veuillez remplir tous les champs requis'))  

        return cleaned_data

class ResetPasswordForm(forms.Form):
    verification_code = forms.CharField(
        max_length=6,
        required=True,
        label="Code de vérification",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        required=True,
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_new_password1',
        }),
    )
    new_password2 = forms.CharField(
        required=True,
        label="Confirmer le nouveau mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_new_password2',
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        verification_code = cleaned_data.get('verification_code')
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if not verification_code:
            raise ValidationError(_('Veuillez entrer le code de vérification.'))

        if new_password1 != new_password2:
            raise ValidationError(_('Les mots de passe ne correspondent pas.'))

        return cleaned_data

class LiveStreamForm(forms.ModelForm):
    class Meta:
        model = LiveStream
        fields = ['video_url']
        widgets = {
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Entrez la nouvelle URL'}),
        }
        labels = {
            'video_url': 'Mettre à jour l\'URL',
        }

class AbsenceUpdateForm(forms.ModelForm):
    class Meta:
        model = Absence
        fields = ['is_present', 'is_absent']

    def clean(self):
        cleaned_data = super().clean()
        is_present = cleaned_data.get("is_present")
        is_absent = cleaned_data.get("is_absent")

        if is_present and is_absent:
            raise forms.ValidationError("A profile cannot be marked both present and absent.")

        return cleaned_data

class AccountDeletionForm(forms.Form):
    username = forms.CharField(
        required=True, 
        label='Nom d’utilisateur',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre nom d’utilisateur'
        })
    )
    password = forms.CharField(
        required=True, 
        label='Mot de passe', 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_password_unique',
            'placeholder': 'Entrez votre mot de passe'
        })
    )

class VerificationCodeForm(forms.Form):
    verification_code = forms.CharField(max_length=6, label="Code de vérification")

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        labels = {
            'name': 'Nom du groupe',
        }

class NoteForm(forms.ModelForm):
    notes = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile', None)
        super(NoteForm, self).__init__(*args, **kwargs)

        if self.profile is not None:
            self.initial['notes'] = self.profile.notes if self.profile.notes is not None else ""

    class Meta:
        model = Profile
        fields = ['notes']

class ApplyRemiseForm(forms.Form):
    facture_choices = forms.ModelMultipleChoiceField(
        queryset=Atelier_Facture.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label="Sélectionner les factures"
    )
    remise = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label="Montant",
        required = True
    )

    def __init__(self, *args, **kwargs):
        profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        if profile:
            self.fields['facture_choices'].queryset = Atelier_Facture.objects.filter(profile=profile)

from django import forms
from .models import CustomUser

class CustomUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)  # Optional password field

    class Meta:
        model = CustomUser
        fields = ['username', 'profile_picture', 'wishlist']
