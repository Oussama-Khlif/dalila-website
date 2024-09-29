from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal
from django.forms import ValidationError
from django.db.models import Max
import re
from django.db.models.signals import m2m_changed
from django.core.exceptions import ValidationError
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Atelier(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_teacher = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    duration = models.IntegerField()
    default = models.BooleanField(default=False)  # New boolean field

    def __str__(self):
        return self.name

class Profile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Etudiant'),
        ('teacher', 'Enseignant'),
        ('none', 'Non Etudiant'),
    ]

    REGISTRATION_TYPE_CHOICES = [
        ('bimestriel', 'Bimestriel'),
        ('annuel', 'Annuel'),
        ('none', 'None'),
    ]
    
    matricule = models.CharField(max_length=100, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    parent_number = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    date_registered = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    ateliers = models.ManyToManyField(Atelier, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    absence_alert = models.DateField(null=True, blank=True, help_text="Date of the absence alert.")
    atelier_absent = models.ForeignKey(Atelier, null=True, blank=True, on_delete=models.SET_NULL, related_name='absent_profiles')
    upcoming_absence_date = models.DateField(null=True, blank=True, help_text="Date of the next planned absence.")
    rattrappage = models.DateTimeField(null=True, blank=True, help_text="Date and time for any makeup class or session.")
    extratime = models.BooleanField(default=False, help_text="Indicates if extra time is allocated.")
    registration_type = models.CharField(max_length=10, choices=REGISTRATION_TYPE_CHOICES, default='none')
    facture = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Amount of the facture issued.")
    subscription_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    refund = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Montant remboursé")
    remise = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Remise en pourcentage")


    def __str__(self):
        return f"{self.name} {self.last_name} - {self.matricule}"

    def save(self, *args, **kwargs):
        if not self.matricule:
            last_matricule = Profile.objects.aggregate(Max('matricule'))['matricule__max']
            
            if last_matricule:
                number = int(re.search(r'\d+', last_matricule).group())
                new_number = number + 1
                new_matricule = f"CR{new_number:04d}"
            else:
                new_matricule = "CR0001"
            
            self.matricule = new_matricule
            
        if self.role == 'teacher':
            self.registration_type = 'none'

        super(Profile, self).save(*args, **kwargs)

    def calculateSubscriptionFee(self):
        self.subscription_fee = Decimal('0.00')
        
        # Get the total absence count for this profile, regardless of atelier
        total_absence_count = Absence.objects.filter(profile=self, is_payed=False).count()
        
        if self.registration_type == 'bimestriel':
            # Calculate how many sets of 8 absences there are
            sets_of_8 = total_absence_count // 8
            self.subscription_fee += Decimal('25.00') * sets_of_8
        
        elif self.registration_type == 'annuel':
            # Calculate how many sets of 12 absences there are
            sets_of_12 = total_absence_count // 12
            self.subscription_fee += Decimal('50.00') * sets_of_12
        
        self.save()



            
    def calculateFacture(self):
        total_fee = Decimal('0.00')
        today = timezone.now().date()
        age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

        for atelier in self.ateliers.all():
            absence_count = Absence.objects.filter(profile=self, atelier=atelier, is_archived=False).count()
            sets_of_4 = absence_count // 4
            
            atelier_price = atelier.price

            if atelier.name == 'Peinture':
                if age > 12:
                    atelier_fee = sets_of_4 * (atelier_price + Decimal('5'))  # Add 5 to the price
                elif self.role.strip() == 'none':
                    atelier_fee = sets_of_4 * (atelier_price + Decimal('25'))  # Add 25 to the price
                else:
                    atelier_fee = sets_of_4 * atelier_price  # Default fee for other roles
            else:
                atelier_fee = sets_of_4 * atelier_price  # For other ateliers

            total_fee += atelier_fee

        if self.refund:
            total_fee -= self.refund

        # Apply the discount if there is one
        if self.remise > 0:
            discount_amount = total_fee * (self.remise / Decimal('100'))
            total_fee -= discount_amount

        self.facture = total_fee
        self.save()
        return total_fee

def enforce_teacher_atelier_limit(sender, instance, action, **kwargs):
    if action == "pre_add" and instance.role == 'teacher' and instance.ateliers.count() >= 1:
        # Prevent adding more than 1 atelier if the profile is a teacher
        instance.adding_too_many_ateliers = True
    else:
        instance.adding_too_many_ateliers = False

m2m_changed.connect(enforce_teacher_atelier_limit, sender=Profile.ateliers.through)

class Absence(models.Model):
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    date_from = models.DateTimeField(default=timezone.now)  # Ensure this field is defined
    date_to = models.DateTimeField(default=timezone.now)  # Ensure this field is defined
    atelier = models.ForeignKey('Atelier', on_delete=models.CASCADE, default=1)
    is_present = models.BooleanField(default=False)
    is_absent = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_payed = models.BooleanField(default=False)


    class Meta:
        unique_together = ('profile', 'date_from', 'atelier')

    def clean(self):
        if self.is_present and self.is_absent:
            raise ValidationError("A profile cannot be marked both present and absent.")
        if not self.is_present and not self.is_absent:
            raise ValidationError("A profile must be marked either present or absent.")
        if self.date_from > self.date_to:
            raise ValidationError("The start date (date_from) cannot be later than the end date (date_to).")

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensure the model passes validation before saving
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return (f"Profile: {self.profile.matricule}, From: {self.date_from}, To: {self.date_to}, "
                f"Atelier: {self.atelier.name}, Status: {status}, Archived: {self.is_archived}")

class CustomUser(AbstractUser):
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    wishlist = models.ManyToManyField('pages.Painting', blank=True, related_name='wishlisted_by')
