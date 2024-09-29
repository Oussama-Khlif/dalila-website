from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns=[
    path('addprofile/',views.addprofile,name='addprofile'),
    path('myclients/', views.myclients, name='myclients'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='pages/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('myaccount/', views.myaccount, name='myaccount'),
    path('profile/<str:matricule>/', views.profile_details, name='profile_details'),
    path('absence_alert/', views.absence_alert, name='absence_alert'),
    path('profile/delete/<str:matricule>/', views.delete_profile, name='delete_profile'),
    path('profile/<str:matricule>/rattrappage/', views.rattrappage_view, name='rattrappage'),
    path('profile/<str:matricule>/check_extratime/', views.check_extratime, name='check_extratime'),
    path('absences/', views.mark_presence, name='absences'),
    path('profile/<str:matricule>/clear_absences/', views.clear_absences, name='clear_absences'),
    path('profile/<str:matricule>/clear_absences_fee/', views.clear_absences_fee, name='clear_absences_fee'),
    path('profile/<str:matricule>/reset_fee_and_facture/', views.reset_fee_and_facture, name='reset_fee_and_facture'),
    path('profile/<str:matricule>/calculate_total_sum/', views.calculate_total_sum, name='calculate_total_sum'),
    path('profile/<str:matricule>/absences/', views.absences_details, name='absences_details'),
    path('view_absences/', views.view_absences, name='view_absences'),
    path('profile/<str:matricule>/fee_details/', views.fee_details, name='fee_details'),
    path('profile/<str:matricule>/refund/', views.refund_profile, name='refund_profile'),
    path('profile/<str:matricule>/teacher_fee/', views.calculate_teacher_fee, name='teacher_fee'),
    path('profile/<str:matricule>/clear_absences_teacher/', views.clear_absences_teacher, name='clear_absences_teacher'),
    path('profile/edit/<str:matricule>/', views.edit_profile, name='edit_profile'),
    path('add_atelier/', views.add_atelier, name='add_atelier'),
    path('my_ateliers/', views.my_ateliers, name='my_ateliers'),
    path('edit_atelier/<int:pk>/', views.edit_atelier, name='edit_atelier'),
    path('delete_atelier/<int:pk>/', views.delete_atelier, name='delete_atelier'),
    path('add_atelier/', views.add_atelier, name='add_atelier'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('profile/<str:matricule>/remise/', views.remise_profile, name='remise_profile'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)