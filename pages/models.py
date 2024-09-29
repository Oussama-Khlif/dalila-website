from datetime import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from PIL import Image as PilImage
from PIL import ImageOps
import os
from django.db import models
from PIL import Image as PilImage
from PIL import ImageOps

class MediaFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} uploaded at {self.uploaded_at}"

    def save(self, *args, **kwargs):
        # Call the original save method first
        super().save(*args, **kwargs)

        # List of supported image extensions
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')

        # Check if the file is an image
        if self.file.name.lower().endswith(image_extensions):
            with PilImage.open(self.file.path) as img:
                # Correct orientation for all image types
                img = ImageOps.exif_transpose(img)

                # Downscale the image
                max_size = (1920, 1080)  # Set the maximum dimensions
                img.thumbnail(max_size, PilImage.LANCZOS)  # Use LANCZOS for high-quality downscaling

                # Convert to RGB if it's not already (handles PNG transparency)
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Save the image as JPEG with compression
                jpeg_path = os.path.splitext(self.file.path)[0] + '.jpg'
                img.save(jpeg_path, format='JPEG', quality=70, optimize=True)

                # Remove the original file if it's not already JPEG
                if not self.file.name.lower().endswith('.jpg'):
                    os.remove(self.file.path)

                # Update the file field to point to the new JPEG file
                self.file.name = os.path.basename(jpeg_path)
                with open(jpeg_path, 'rb') as new_file:
                    self.file.save(self.file.name, new_file, save=False)

        # Save the model again to update the file field
        super().save(update_fields=['file'])

class SpecialEvent(models.Model):
    caption = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='special_events/')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.caption if self.caption else ''  # Return an empty string if caption is None or empty

class Video(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    video_file = models.FileField(upload_to='videos/')

    def __str__(self):
        return self.title

User = get_user_model()
class Painting(models.Model):
    photo = models.ImageField(upload_to='paintings/')
    name = models.CharField(max_length=15)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    location = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    height = models.CharField(max_length=10, blank=True, null=True)
    width = models.CharField(max_length=10, blank=True, null=True)
    technique = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

User = get_user_model()
class Rating(models.Model):
    painting = models.ForeignKey(Painting, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('painting', 'user')

    def __str__(self):
        return f'{self.user} - {self.painting.name}: {self.score}'