from django import forms
from .models import Painting, Video, SpecialEvent, Rating

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class MediaUploadForm(forms.Form):
    file = MultipleFileField(
        label='Fichiers',
        required=True,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

class SpecialEventForm(forms.ModelForm):
    class Meta:
        model = SpecialEvent
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'video_file']
        labels = {
            'title': 'Légende',
            'video_file': 'Vidéo',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'video_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class PaintingForm(forms.ModelForm):
    height = forms.IntegerField(
        required=True,
        label='Hauteur',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'ex. 2200',
            'min': '0'
        })
    )
    width = forms.IntegerField(
        required=True,
        label='Largeur',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'ex. 3000',
            'min': '0'
        })
    )
    price = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=True,
        label='Prix (DT)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'ex. 1000',
            'step': '0.01',
            'min': '0',
            'max': '99999.99',
            'oninput': 'this.value = Math.min(this.value, 99999.99)'
        })
    )

    class Meta:
        model = Painting
        fields = ['photo', 'name', 'price', 'date', 'location', 'phone_number', 'height', 'width', 'technique']
        labels = {
            'photo': 'Photo',
            'name': 'Nom',
            'date': 'Date de création',
            'location': 'Lieu',
            'phone_number': 'Numéro de téléphone',
            'technique': 'Technique',
        }
        widgets = {
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'technique': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(PaintingForm, self).__init__(*args, **kwargs)
        if self.instance.date:
            self.initial['date'] = self.instance.date.strftime('%Y-%m-%d')

class PaintingDeletionForm(forms.Form):
    name = forms.CharField(max_length=255, label='Name of Painting to Delete', widget=forms.TextInput(attrs={'class': 'form-control'}))

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
        }
