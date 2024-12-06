from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from decimal import ROUND_DOWN, Decimal
from django.forms import ValidationError
from django.db.models import Max
import re
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from human_ressorces.utils import send_email
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.utils.timezone import now

class Atelier(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_teacher = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    duration = models.IntegerField()
    default = models.BooleanField(default=False)  

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)  

    def __str__(self):
        return self.name  

class Profile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Etudiant'),
        ('teacher', 'Enseignant'),
        ('none', 'Non Etudiant'),
    ]

    REGISTRATION_TYPE_CHOICES = [
        ('none', "Pas d'inscription"),
        ('bimestriel', 'Bimestriel'),
        ('annual', 'Annuel'),
    ]

    matricule = models.CharField(max_length=100, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True,max_length=254, unique=True)
    parent_number = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    date_registered = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    groups = models.ManyToManyField(Group, blank=True)
    ateliers = models.ManyToManyField(Atelier, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    absence_alert = models.DateField(null=True, blank=True, help_text="Date of the absence alert.")
    atelier_absent = models.ForeignKey(Atelier, null=True, blank=True, on_delete=models.SET_NULL, related_name='absent_profiles')
    upcoming_absence_date = models.DateField(null=True, blank=True, help_text="Date of the next planned absence.")
    rattrappage = models.DateTimeField(null=True, blank=True, help_text="Date and time for any makeup class or session.")
    registration_type = models.CharField(max_length=20, choices=REGISTRATION_TYPE_CHOICES, default='none')
    facture = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Amount of the facture issued.")
    subscription_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True, help_text="Additional notes or comments.")
    advance = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=Decimal('0.00'))

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
        total_fee = Decimal('0.00')
        absences = Absence.objects.filter(profile=self, is_calculated2=False)
        total_absence_count = absences.count()
        if self.registration_type == 'bimestriel':
            sets_of_8 = total_absence_count // 8
            if total_absence_count >= 8:
                total_fee += Decimal('25.00') * sets_of_8

                if total_fee > 0:
                    Atelier_Facture.objects.create(
                        profile=self,
                        atelier=None,
                        facture=total_fee,
                        facture_type='inscription'
                    )

                oldest_absences = absences.order_by('date_from')[:8]
                for absence in oldest_absences:
                    absence.is_calculated2 = True
                    absence.save()
        elif self.registration_type == 'annual':
            sets_of_36 = total_absence_count // 36
            if total_absence_count >= 36:
                total_fee += Decimal('50.00') * sets_of_36

                if total_fee > 0:
                    Atelier_Facture.objects.create(
                        profile=self,
                        atelier=None,
                        facture=total_fee,
                        facture_type='inscription'
                    )

                oldest_absences = absences.order_by('date_from')[:36]
                for absence in oldest_absences:
                    absence.is_calculated2 = True
                    absence.save()
        return self.subscription_fee

    def calculateFacture(self):
        total_fee = Decimal('0.00')
        today = timezone.now().date()
        age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        for atelier in self.ateliers.all():
            absences = Absence.objects.filter(
                profile=self, 
                atelier=atelier, 
                is_calculated=False)
            absence_count = absences.count()
            sets_of_4 = absence_count // 4
            atelier_price = atelier.price
            atelier_fee = sets_of_4 * atelier_price
            if atelier.name == 'Peinture':
                if age > 12:
                    atelier_fee = sets_of_4 * (atelier_price + Decimal('5'))  
                elif self.role.strip() == 'none':
                    atelier_fee = sets_of_4 * (atelier_price + Decimal('25'))  
                else:
                    atelier_fee = sets_of_4 * atelier_price  
            if atelier_fee > 0:
                Atelier_Facture.objects.create(
                    profile=self,
                    atelier=atelier,
                    facture=atelier_fee
                )
                total_fee += atelier_fee
                absences.update(is_calculated=True)
        self.facture = total_fee
        self.save()
        return total_fee

    def calculate_total_fee(self, total_hours_worked):
        total_fee = Decimal('0.00')
        for atelier in self.ateliers.all():  
            if atelier.price_teacher:  
                fee_per_hour = atelier.price_teacher
                total_fee += Decimal(total_hours_worked) * fee_per_hour
        total_fee = total_fee.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        return total_fee

    def Notify(self):
        self.calculateSubscriptionFee()
        self.calculateFacture()
        if self.role != 'teacher':
            for atelier in self.ateliers.all():
                absence_count = Absence.objects.filter(profile=self, atelier=atelier, is_calculated=False, is_notified=False).count()
                sets_of_4 = absence_count // 4
                if sets_of_4 > 0:  
                    total_fee = self.subscription_fee + self.facture
                    if self.email:  
                        subject = "Votre facture est disponible"
                        context = {
                        'name': self.name,
                        'last_name': self.last_name,
                        'message_body': f"Votre facture est disponible de {total_fee:.2f} DT",
                        'signature': "Chromarium"
                    }
                        message = render_to_string('pages/email_template.html', context)
                        send_email(self.email, subject, message)
                        oldest_absences = list(Absence.objects.filter(profile=self, atelier=atelier, is_calculated=False, is_notified=False).order_by('date_from')[:4])
                        for absence in oldest_absences:
                            absence.is_notified = True
                            absence.save()

    def check_teacher_absence(self):
        if self.role == 'teacher':
            last_absence = Absence.objects.filter(
                profile=self,
                is_absent=True,
                is_calculated=False  
            ).order_by('-date_from').first()  

            if last_absence:
                subsequent_records = Absence.objects.filter(
                    profile=self,
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

    @classmethod
    def process_profiles(cls):
        messages = []
        for profile in cls.objects.all():
            message = profile.check_teacher_absence()
            if message:
                messages.append((profile, message))
        return messages

class Absence(models.Model):
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    date_from = models.DateTimeField(default=timezone.now)  
    date_to = models.DateTimeField(default=timezone.now)  
    atelier = models.ForeignKey('Atelier', on_delete=models.CASCADE, default=1)
    is_present = models.BooleanField(default=False)
    is_absent = models.BooleanField(default=False)
    is_notified = models.BooleanField(default=False)
    is_calculated = models.BooleanField(default=False)
    is_calculated2 = models.BooleanField(default=False)
    is_payed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('profile', 'date_from', 'atelier')

    def clean(self):
        if self.is_present and self.is_absent:
            raise ValidationError("A profile cannot be marked both present and absent.")
        if self.date_from > self.date_to:
            raise ValidationError("The start date (date_from) cannot be later than the end date (date_to).")

    def save(self, *args, **kwargs):
        self.full_clean()  
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return (f"Profile: {self.profile.matricule}, From: {self.date_from}, To: {self.date_to}, "
                f"Atelier: {self.atelier.name}, Status: {status}")

class CustomUser(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+\-\s]+$',
                message="Le nom d'utilisateur ne peut contenir que des lettres, des chiffres, des espaces et les symboles @/./+/-/_",
                code='invalid_username'
            ),
        ],
    )
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    wishlist = models.ManyToManyField('pages.Painting', blank=True, related_name='wishlisted_by')
    is_banned = models.BooleanField(default=False)

class VisitorIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    visit_time = models.DateTimeField(default=now)
    is_me = models.BooleanField(default=False)

    def __str__(self):
        return f"IP: {self.ip_address}, Visited on: {self.visit_time}, Is Me: {self.is_me}"

    
class FinancialStats(models.Model):
    total_fee_student = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_fee_teacher = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    unique_visitors = models.ManyToManyField(VisitorIP, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def count_unique_visitors(self):
        return self.unique_visitors.count()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Financial Stats (Updated on {self.last_updated})"

class Profit_stat(models.Model):
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    last_updated = models.DateTimeField(auto_now=True)

    @classmethod
    def calculate_and_save_profit(cls):
        financial_stats = FinancialStats.objects.first()
        if financial_stats:
            profit_value = financial_stats.total_fee_student - financial_stats.total_fee_teacher
            profit_record = cls.objects.create(profit=profit_value)
            return profit_record
        else:
            return None

    def __str__(self):
        return f"Profit: {self.profit} (Last updated: {self.last_updated})"

class LiveStream(models.Model):
    video_url = models.URLField(max_length=255)

class VerificationCode(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        """Check if the code is still valid (hasn't expired)."""
        return timezone.now() < self.expires_at

User = get_user_model()
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_cleared = models.BooleanField(default=False)
    cleared_at = models.DateTimeField(null=True, blank=True)
    visible_to_admin_only = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification for {self.user}: {self.message}"

class PaymentHistory(models.Model):
    INVOICE_TYPE_CHOICES = [
        ('facture', 'Facture'),
        ('solde', 'Solde Client')
    ]

    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='payment_history')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount of money paid.")
    payment_date = models.DateTimeField(default=now, help_text="Date and time when the payment was made.")
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPE_CHOICES, default='facture')

    def __str__(self):
        return (f"Payment for {self.profile.name} {self.profile.last_name} - "
                f"Amount: {self.amount_paid}, Date: {self.payment_date}, Type: {self.get_invoice_type_display()}")

class Atelier_Facture(models.Model):
    id = models.AutoField(primary_key=True)
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    atelier = models.ForeignKey('Atelier', on_delete=models.CASCADE, null=True, blank=True)
    facture = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    FACTURE_TYPES = [
        ('inscription', 'Inscription'),
        ('atelier', 'Atelier'),
    ]
    
    facture_type = models.CharField(
        max_length=20,
        choices=FACTURE_TYPES,
        default='atelier',
    )

    def __str__(self):
        return f"{self.atelier.name if self.atelier else 'No Atelier'} - {self.facture} DT"

    class Meta:
        pass