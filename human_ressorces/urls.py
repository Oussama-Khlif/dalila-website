from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns=[
    path('addprofile/',views.addprofile,name='addprofile'),
    path('myclients/', views.myclients, name='myclients'),
    path('register/', views.register, name='register'),
    path('login/', views.custom_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('myaccount/', views.myaccount, name='myaccount'),
    path('profile/<str:matricule>/', views.profile_details, name='profile_details'),
    path('absence_alert/', views.absence_alert, name='absence_alert'),
    path('profile/delete/<str:matricule>/', views.delete_profile, name='delete_profile'),
    path('profile/<str:matricule>/rattrappage/', views.rattrappage_view, name='rattrappage'),
    path('profile/<str:matricule>/check_extratime/', views.check_extratime, name='check_extratime'),
    path('absences/', views.mark_presence, name='absences'),
    path('profile/<str:matricule>/clear_absences/', views.clear_absences, name='clear_absences'),
    path('profile/<str:matricule>/absences/', views.absences_details, name='absences_details'),
    path('view_absences/', views.view_absences, name='view_absences'),
    path('profile/<str:matricule>/fee_details/', views.fee_details, name='fee_details'),
    path('profile/<str:matricule>/teacher_fee/', views.calculate_teacher_fee, name='teacher_fee'),
    path('profile/<str:matricule>/clear_absences_teacher/', views.clear_absences_teacher, name='clear_absences_teacher'),
    path('profile/edit/<str:matricule>/', views.edit_profile, name='edit_profile'),
    path('add_atelier/', views.add_atelier, name='add_atelier'),
    path('my_ateliers/', views.my_ateliers, name='my_ateliers'),
    path('edit_atelier/<int:pk>/', views.edit_atelier, name='edit_atelier'),
    path('delete_atelier/<int:pk>/', views.delete_atelier, name='delete_atelier'),
    path('add_atelier/', views.add_atelier, name='add_atelier'),
    path('forgot-password/', views.forgot_password_request, name='forgot_password_request'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('live-stream/', views.live_stream, name='live_stream'),
    path('absences/edit/<int:absence_id>/', views.edit_absence, name='edit_absence'),
    path('check-user-image/', views.check_user_image, name='check-user-image'),
    path('profiles/manage/', views.manage_profiles, name='manage_profiles'),
    path('clear-notifications/', views.clear_notifications, name='clear_notifications'),
    path('profile/<str:matricule>/edit-notes/', views.edit_profile_notes, name='edit_profile_notes'),
    path('update-advance/', views.update_advance, name='update_advance'),
    path('profile/<str:matricule>/payment_history/', views.payment_history, name='payment_history'),
    path('profile/<str:profile_matricule>/facture_details/', views.facture_details, name='facture_details'),
    path('profile/<str:matricule>/facture_details/', views.facture_details, name='facture_details'),
    path('profile/<str:matricule>/clear_absences/<int:atelier_facture_id>/', views.clear_absences, name='clear_absences'),
    path('manage-users/', views.manage_users, name='manage_users'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)