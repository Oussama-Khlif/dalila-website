from django.contrib import admin
from .models import Painting, Rating, SpecialEvent
from django.contrib import admin
from .models import Video, MediaFile
from django.contrib import admin
from .models import Painting
from django.contrib import admin
from .models import MediaFile


@admin.register(SpecialEvent)
class SpecialEventAdmin(admin.ModelAdmin):
    list_display = ('caption', 'updated_at')

@admin.register(Painting)
class PaintingAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = (
        'photo', 'name', 'price', 'date', 'location', 'phone_number', 'get_dimensions', 'technique', 'user'
    )
    
    # Fields to display in the form view
    fields = (
        'photo', 'name', 'price', 'date', 'location', 'phone_number', 'height', 'width', 'technique', 'user'
    )
    
    # Fields to be excluded from the form view, if needed
    # exclude = ('user',)  # Example to exclude a field from the form
    
    # Add search functionality
    search_fields = ('name', 'location', 'height', 'width', 'technique')
    
    # Add filters on the right side of the list view
    list_filter = ('date', 'price')
    
    # Add ordering in the list view
    ordering = ('-date',)

    # Custom method to display combined height and width
    def get_dimensions(self, obj):
        return f"{obj.height} x {obj.width}"
    get_dimensions.short_description = 'Dimensions'

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('painting', 'user', 'score', 'created_at')  # Ensure 'created_at' exists
    list_filter = ('painting', 'user', 'score')
    search_fields = ('painting__name', 'user__username')

@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'uploaded_at')  # Display these fields in the admin list view
    search_fields = ('file',)  # Allow searching by file name

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'video_file')  # Display these fields in the admin list view
    search_fields = ('title',)  # Add search functionality by title