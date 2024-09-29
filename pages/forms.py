from django import forms
from .models import Painting, Video, SpecialEvent
from django import forms
from .models import Rating
from django import forms
from .models import MediaFile

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

class MediaUploadForm(forms.ModelForm):
    file = MultipleFileField(label='Sélectionner des fichiers', required=False)

    class Meta:
        model = MediaFile
        fields = ['file']

class SpecialEventForm(forms.ModelForm):
    class Meta:
        model = SpecialEvent
        fields = ['caption', 'image']
        labels = {
            'caption': 'Légende (facultatif)',
        }
        help_texts = {
            'caption': 'Laissez ce champ vide si vous n\'avez pas de légende.',
        }

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'video_file']
        labels = {
            'title': 'Légende',
            'video_file': 'Vidéo',
        }

class PaintingForm(forms.ModelForm):
    class Meta:
        model = Painting
        fields = ['photo', 'name', 'price', 'date', 'location', 'phone_number', 'height', 'width', 'technique']
        labels = {
            'photo': 'Photo',
            'name': 'Nom',
            'price': 'Prix',
            'date': 'Date',
            'location': 'Lieu',
            'phone_number': 'Numéro de téléphone',
            'height': 'Hauteur',
            'width': 'Largeur',
            'technique': 'Technique',
        }
        widgets = {
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'class': 'form-control'}),
            'width': forms.NumberInput(attrs={'class': 'form-control'}),
            'technique': forms.TextInput(attrs={'class': 'form-control'}),
        }

    # Add additional fields for height and width
    height = forms.CharField(max_length=10, required=False, label='Hauteur')
    width = forms.CharField(max_length=10, required=False, label='Largeur')

    def __init__(self, *args, **kwargs):
        super(PaintingForm, self).__init__(*args, **kwargs)
        # Customizing field widgets
        self.fields['height'].widget.attrs.update({'placeholder': 'ex. 2200'})
        self.fields['width'].widget.attrs.update({'placeholder': 'ex. 3000'})
        
        # Convert date to the correct format for the DateInput widget
        if self.instance.date:
            self.initial['date'] = self.instance.date.strftime('%Y-%m-%d')

class PaintingDeletionForm(forms.Form):
    name = forms.CharField(max_length=255, label='Name of Painting to Delete')

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }