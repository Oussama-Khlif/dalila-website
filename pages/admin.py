from django.contrib import admin
from .models import Painting, Rating, SpecialEvent, Video, MediaFile

class SpecialEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'updated_at')  
    list_filter = ('updated_at',)  
    search_fields = ('id',)  

admin.site.register(SpecialEvent, SpecialEventAdmin)

@admin.register(Painting)
class PaintingAdmin(admin.ModelAdmin):

    list_display = (
        'photo', 'name', 'price', 'date', 'location', 'phone_number', 'get_dimensions', 'technique', 'user'
    )

    fields = (
        'photo', 'name', 'price', 'date', 'location', 'phone_number', 'height', 'width', 'technique', 'user'
    )

    search_fields = ('name', 'location', 'height', 'width', 'technique')

    list_filter = ('date', 'price')

    ordering = ('-date',)

    def get_dimensions(self, obj):
        return f"{obj.height} x {obj.width}"
    get_dimensions.short_description = 'Dimensions'

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('painting', 'user', 'score', 'created_at')  
    list_filter = ('painting', 'user', 'score')
    search_fields = ('painting__name', 'user__username')

@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'uploaded_at')  
    search_fields = ('file',)  

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'video_file')  
    search_fields = ('title',)