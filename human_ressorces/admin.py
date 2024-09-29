from django.contrib import admin
from django.forms import ValidationError
from .models import Profile, Absence, CustomUser, Atelier
from django.contrib import admin
from .models import Absence
from django.contrib import admin
from .models import Absence

admin.site.register(CustomUser)

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('profile', 'date_from', 'date_to', 'atelier', 'is_present', 'is_absent', 'is_archived', 'is_payed')  # Added is_payed
    list_filter = ('date_from', 'atelier', 'is_present', 'is_absent', 'is_archived', 'is_payed')  # Added is_payed
    search_fields = ('profile__name', 'profile__last_name', 'profile__matricule', 'atelier__name')
    date_hierarchy = 'date_from'  # Use 'date_from' for date hierarchy

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile', 'atelier')

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            form.add_error(None, str(e))

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'last_name', 'matricule', 'date_of_birth', 'role',
        'profile_picture', 'registration_type', 'facture', 'subscription_fee',
        'absence_alert', 'atelier_absent',
        'upcoming_absence_date',
        'rattrappage', 'extratime', 'refund', 'remise'  # Add remise here
    )
    
    list_filter = (
        'role', 'registration_type', 'facture', 'extratime', 'subscription_fee'
    )
    
    fields = (
        'matricule', 'name', 'last_name', 'parent_number', 'date_of_birth',
        'role', 'ateliers', 'profile_picture', 'registration_type', 'facture',
        'subscription_fee', 'absence_alert', 'atelier_absent',
        'upcoming_absence_date',
        'rattrappage', 'extratime', 'refund', 'remise'  # Add remise here
    )
        
    readonly_fields = ('atelier_absent', 'upcoming_absence_date')  # Optional: Make read-only if needed
    
    filter_horizontal = ('ateliers',)

@admin.register(Atelier)
class AtelierAdmin(admin.ModelAdmin):
    list_display = ('name', 'price','price_teacher', 'duration')
