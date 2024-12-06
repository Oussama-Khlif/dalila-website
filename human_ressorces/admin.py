from django.contrib import admin
from django.forms import ValidationError
from .models import FinancialStats, Notification, PaymentHistory, Profile, Absence, CustomUser, Atelier, Profit_stat, VerificationCode, VisitorIP
from .models import Profile, Group

admin.site.register(CustomUser)

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('profile', 'date_from', 'date_to', 'atelier', 'is_present', 'is_absent', 'is_notified','is_calculated','is_calculated2','is_payed')  
    list_filter = ('date_from', 'atelier', 'is_present', 'is_absent', 'is_calculated','is_calculated2')  
    search_fields = ('profile__name', 'profile__last_name', 'profile__matricule', 'atelier__name','is_notified','is_calculated','is_calculated2','is_payed')
    date_hierarchy = 'date_from'  

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile', 'atelier')

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            form.add_error(None, str(e))

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'last_name', 'email', 'matricule', 'date_of_birth', 'role',
        'profile_picture', 'registration_type', 'facture', 'subscription_fee',
        'absence_alert', 'atelier_absent', 'upcoming_absence_date',
        'rattrappage', 'notes'
    )

    list_filter = (
        'role', 'registration_type', 'facture', 'subscription_fee', 'groups'
    )

    fields = (
        'matricule', 'name', 'last_name', 'email', 'parent_number', 'date_of_birth',
        'role', 'ateliers', 'profile_picture', 'registration_type', 'facture',
        'subscription_fee', 'absence_alert', 'atelier_absent', 'upcoming_absence_date',
        'rattrappage', 'groups', 'notes'
    )

    readonly_fields = ('atelier_absent', 'upcoming_absence_date')  

    filter_horizontal = ('ateliers', 'groups')

@admin.register(Atelier)
class AtelierAdmin(admin.ModelAdmin):
    list_display = ('name', 'price','price_teacher', 'duration')

@admin.register(Profit_stat)
class ProfitStatAdmin(admin.ModelAdmin):
    list_display = ('profit', 'last_updated')
    search_fields = ('profit',)
    list_filter = ('last_updated',)

@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'expires_at')
    list_filter = ('user', 'created_at', 'expires_at')
    search_fields = ('user__username', 'code')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_cleared', 'created_at', 'cleared_at')  
    list_filter = ('is_cleared', 'user')  
    search_fields = ('message',)  
    ordering = ('-created_at',)

from django.contrib import admin
from .models import Atelier_Facture

class AtelierFactureAdmin(admin.ModelAdmin):
    list_display = ('profile', 'atelier', 'facture', 'created_at')
    search_fields = ('profile__name', 'atelier__name')
    list_filter = ('atelier',)
    ordering = ('-created_at',)

admin.site.register(Atelier_Facture, AtelierFactureAdmin)

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('profile', 'amount_paid', 'payment_date', 'invoice_type')
    list_filter = ('invoice_type', 'payment_date')
    search_fields = ('profile__name', 'profile__last_name', 'invoice_type')

@admin.register(FinancialStats)
class FinancialStatsAdmin(admin.ModelAdmin):
    list_display = ('total_fee_student', 'total_fee_teacher', 'last_updated', 'count_unique_visitors')

@admin.register(VisitorIP)
class VisitorIPAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'visit_time', 'is_me')