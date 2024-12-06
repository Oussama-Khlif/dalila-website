from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns=[
    path('',views.index,name='index'),
    path('about/',views.about,name='about'),
    path('calligraphy/',views.calligraphy,name='calligraphy'),
    path('languages/',views.languages,name='languages'),
    path('mental_calculation/',views.mental_calculation,name='mental_calculation'),
    path('theater/',views.theater,name='theater'),
    path('music/',views.music,name='music'),
    path('paint/',views.paint,name='paint'),
    path('robotics/',views.robotics,name='robotics'),
    path('update-event/', views.update_event, name='update_event'),
    path('upload/', views.upload_video, name='upload_video'),
    path('addpainting/', views.add_painting, name='add_painting'),
    path('artgallery/', views.art_gallery, name='art_gallery'),
    path('edit-painting/<int:painting_id>/', views.edit_painting, name='edit_painting'),
    path('mypaintings/', views.my_paintings, name='mypaintings'),
    path('rate_painting/<int:painting_id>/', views.submit_rating, name='submit_rating'),
    path('painting/<int:painting_id>/', views.painting_details, name='painting_details'),
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('add_to_wishlist/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:painting_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('delete-painting/<int:pk>/', views.delete_painting, name='delete_painting'),
    path('upload_media/', views.upload_media, name='upload_media'),
    path('list/', views.list_media, name='list_media'),
    path('delete-photos/', views.delete_photos, name='delete_photos'),
    path('events/', views.display_events, name='display_events'),
    path('pottery/', views.pottery, name='pottery'),
    path('fimo_clay/', views.fimo_clay, name='fimo_clay'),
    path('gymnastics/', views.gymnastics, name='gymnastics'),
    path('oriental_dance/', views.oriental_dance, name='oriental_dance'),
    path('singing_club/', views.singing_club, name='singing_club'),
    path('crafting/', views.crafting, name='crafting'),
    path('photography/', views.photography, name='photography'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)