from datetime import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from PIL import Image as PilImage, ImageOps
from io import BytesIO
import os
from PIL import Image
from django.core.files.base import ContentFile

class MediaFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} uploaded at {self.uploaded_at}"

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')

        if self.file.name.lower().endswith(image_extensions):
            with PilImage.open(self.file.path) as img:

                img = ImageOps.exif_transpose(img)

                max_size = (1920, 1080)  
                img.thumbnail(max_size, PilImage.LANCZOS)  

                if img.mode != 'RGB':
                    img = img.convert('RGB')

                jpeg_path = os.path.splitext(self.file.path)[0] + '.jpg'
                img.save(jpeg_path, format='JPEG', quality=70, optimize=True)

                if not self.file.name.lower().endswith('.jpg'):
                    os.remove(self.file.path)

                self.file.name = os.path.basename(jpeg_path)
                with open(jpeg_path, 'rb') as new_file:
                    self.file.save(self.file.name, new_file, save=False)

        super().save(update_fields=['file'])

class SpecialEvent(models.Model):
    image = models.ImageField(upload_to='special_events/')
    updated_at = models.DateTimeField(auto_now=True)

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
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        img = Image.open(self.photo)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        img_io = BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        self.photo.save(self.photo.name, ContentFile(img_io.getvalue()), save=False)
        super().save(*args, **kwargs)

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