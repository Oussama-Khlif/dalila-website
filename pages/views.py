import json
from decimal import Decimal, ROUND_DOWN
from django.views.generic.list import ListView
from django.contrib import messages
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count
from human_ressorces import models
from human_ressorces.models import Atelier
from .models import Painting, Rating, Video, SpecialEvent, MediaFile
from .forms import PaintingForm, SpecialEventForm, VideoForm, MediaUploadForm

def admin_only(user):
    return user.is_superuser or user.username == 'admin'

def about(request):
    events = SpecialEvent.objects.all() 
    return render(request, 'pages/about.html', {'events': events})

def calligraphy(request):
    events = SpecialEvent.objects.all() 

    atelier = Atelier.objects.filter(name='Calligraphie').first()  
    return render(request, 'pages/workshops/calligraphy.html', {'events': events, 'atelier': atelier})

def languages(request):
    events = SpecialEvent.objects.all() 

    atelier = Atelier.objects.filter(name='Langues').first()  
    return render(request, 'pages/workshops/languages.html', {'events': events, 'atelier': atelier})

def theater(request):
    events = SpecialEvent.objects.all() 

    atelier = Atelier.objects.filter(name='Théâtre').first()  
    return render(request, 'pages/workshops/theater.html', {'events': events, 'atelier': atelier})

def mental_calculation(request):
    events = SpecialEvent.objects.all() 

    atelier = Atelier.objects.filter(name='Calcul Mental').first()  
    return render(request, 'pages/workshops/mental_calculation.html', {'events': events, 'atelier': atelier})

def music(request):
    events = SpecialEvent.objects.all() 

    ateliers = Atelier.objects.filter(name__icontains='Musique')  
    return render(request, 'pages/workshops/music.html', {'events': events, 'ateliers': ateliers})

def paint(request):
    events = SpecialEvent.objects.all() 

    atelier = Atelier.objects.filter(name='Peinture').first()  

    if atelier and atelier.price is not None:
        original_price = atelier.price  
        over_12 = (original_price + Decimal('5')).quantize(Decimal('0.01'), rounding=ROUND_DOWN)  
        non_child_price = (original_price + Decimal('25')).quantize(Decimal('0.01'), rounding=ROUND_DOWN)  

    else:
        over_12 = None
        non_child_price = None

    return render(request, 'pages/workshops/paint.html', {
        'events': events,
        'atelier': atelier,
        'over_12': over_12,
        'non_child_price': non_child_price,
    })

def robotics(request):
    events = SpecialEvent.objects.all() 

    atelier = Atelier.objects.filter(name='Robotique').first()  
    return render(request, 'pages/workshops/robotics.html', {'events': events, 'atelier': atelier})

def pottery(request):
    events = SpecialEvent.objects.all()
    atelier = Atelier.objects.filter(name='Potterie').first()  

    context = {
        'events': events,
        'atelier': atelier
    }
    return render(request, 'pages/workshops/pottery.html', context)

def photography(request):
    events = SpecialEvent.objects.all()
    atelier = Atelier.objects.filter(name='Photographie').first()  

    context = {
        'events': events,
        'atelier': atelier
    }
    return render(request, 'pages/workshops/photography.html', context)

def fimo_clay(request):
    events = SpecialEvent.objects.all()
    atelier = Atelier.objects.filter(name='Argile Polymère').first()  

    context = {
        'events': events,
        'atelier': atelier
    }
    return render(request, 'pages/workshops/fimo_clay.html', context)

def gymnastics(request):
    events = SpecialEvent.objects.all()
    atelier = Atelier.objects.filter(name='Gymnastique').first()  

    context = {
        'atelier': atelier,
        'events': events,
    }
    return render(request, 'pages/workshops/gymnastics.html', context)

def oriental_dance(request):
    atelier = Atelier.objects.filter(name='Danse Orientale').first()  
    events = SpecialEvent.objects.all()
    context = {
        'atelier': atelier,
        'events': events,
    }
    return render(request, 'pages/workshops/oriental_dance.html', context)

def singing_club(request):
    atelier = Atelier.objects.filter(name='Club de Chant').first()  
    events = SpecialEvent.objects.all()
    context = {
        'atelier': atelier,
        'events': events,
    }
    return render(request, 'pages/workshops/singing_club.html', context)

def crafting(request):
    atelier = Atelier.objects.filter(name='Bricolage').first()  
    events = SpecialEvent.objects.all()
    context = {
        'atelier': atelier,
        'events': events,
    }
    return render(request, 'pages/workshops/crafting.html', context)

def index(request):
    events = SpecialEvent.objects.all() 
    latest_video = Video.objects.latest('id') if Video.objects.exists() else None

    return render(request, 'pages/index.html', {
        'events': events,
        'latest_video': latest_video,
    })

@login_required
@user_passes_test(admin_only)
def update_event(request):
    events = SpecialEvent.objects.all()
    form = SpecialEventForm()

    if request.method == 'POST':

        if 'delete_multiple' in request.POST:
            event_ids = request.POST.getlist('event_ids')
            SpecialEvent.objects.filter(id__in=event_ids).delete()
            return redirect('update_event')

        elif 'delete_event' in request.POST:
            event_id = request.POST.get('delete_event')
            try:
                event_to_delete = SpecialEvent.objects.get(id=event_id)
                event_to_delete.delete()  
                return redirect('update_event')  
            except SpecialEvent.DoesNotExist:
                pass  

        else:
            form = SpecialEventForm(request.POST, request.FILES)

            if form.is_valid():
                event = form.save()  

                if request.FILES.get('image'):
                    media_file = MediaFile(file=request.FILES['image'])
                    media_file.save()  

                return redirect('update_event')

    context = {
        'event_form': form,
        'events': events,
    }
    return render(request, 'pages/update_event.html', context)

def display_events(request):
    events = SpecialEvent.objects.all()  
    return render(request, 'pages/display_events.html', {'events': events})

@login_required
@user_passes_test(admin_only)
def upload_video(request):
    events = SpecialEvent.objects.all() 

    current_video = Video.objects.first()

    if request.method == 'POST':

        if 'delete' in request.POST:
            video_id = request.POST.get('delete')
            try:
                video_to_delete = Video.objects.get(id=video_id)
                video_to_delete.delete()  
                return redirect('index')  
            except Video.DoesNotExist:
                pass

        video_form = VideoForm(request.POST, request.FILES, instance=current_video)  
        if video_form.is_valid():

            video_instance = video_form.save()

            media_file = MediaFile(file=video_instance.video_file)  
            media_file.save()

            if events:
                media_file.event = events
                media_file.save()

            return redirect('index')
    else:

        video_form = VideoForm(instance=current_video)

    return render(request, 'pages/upload_video.html', {
        'form': video_form,
        'events': events,
        'video': current_video,  
    })

@login_required
def add_painting(request):
    if request.method == 'POST':
        if 'upload_submit' in request.POST:
            form = PaintingForm(request.POST, request.FILES)
            if form.is_valid():
                painting = form.save(commit=False)
                painting.user = request.user  
                painting.save()
                return redirect('mypaintings')  
    else:
        form = PaintingForm()

    return render(request, 'pages/addpainting.html', {
        'form': form,
    })

@login_required
def my_paintings(request):
    events = SpecialEvent.objects.all()

    if request.method == 'POST' and 'delete_painting' in request.POST:
        painting_id = request.POST.get('painting_id')
        try:
            painting_to_delete = Painting.objects.get(id=painting_id, user=request.user)
            painting_to_delete.delete()
            messages.success(request, "Votre peinture a été supprimée avec succès !")
        except Painting.DoesNotExist:
            messages.error(request, "Cette peinture n'existe pas ou vous n'avez pas les droits pour la supprimer.")

    paintings = Painting.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'pages/mypaintings.html', {
        'paintings': paintings,
        'events': events
    })

@login_required
def edit_painting(request, painting_id):
    painting = get_object_or_404(Painting, id=painting_id, user=request.user)

    if request.method == 'POST':
        form = PaintingForm(request.POST, request.FILES, instance=painting)
        if form.is_valid():
            form.save()
            return redirect('mypaintings')  
    else:
        form = PaintingForm(instance=painting)

    return render(request, 'pages/edit_painting.html', {'form': form, 'painting': painting})

def art_gallery(request):
    events = SpecialEvent.objects.all()

    paintings = Painting.objects.annotate(
        average_rating=Avg('ratings__score'),
        rating_count=Count('ratings')  
    ).order_by('-created_at', '-average_rating')  

    return render(request, 'pages/artgallery.html', {
        'paintings': paintings,
        'events': events
    })

@login_required
def user_paintings(request):
    """Fetch paintings uploaded by the logged-in user."""
    return Painting.objects.filter(user=request.user)

def painting_details(request, painting_id):
    events = SpecialEvent.objects.all()

    painting = get_object_or_404(
        Painting.objects.annotate(
            average_rating=Avg('ratings__score'),
            rating_count=Count('ratings')
        ),
        id=painting_id
    )

    return render(request, 'pages/painting_details.html', {
        'painting': painting,
        'events': events,
        'average_rating': painting.average_rating,
        'rating_count': painting.rating_count,
    })

def get_average_rating(painting):
    ratings = painting.ratings.all()
    if ratings.exists():
        return ratings.aggregate(models.Avg('score'))['score__avg']
    return None

@login_required
def submit_rating(request, painting_id):
    if request.method == 'POST':
        rating_value = request.POST.get('rating')
        painting = Painting.objects.get(id=painting_id)

        if rating_value:
            rating, created = Rating.objects.get_or_create(
                painting=painting,
                user=request.user,
                defaults={'score': rating_value}
            )
            if not created:
                rating.score = rating_value
                rating.save()

            messages.add_message(request, messages.SUCCESS, 'Merci pour votre évaluation', extra_tags='rate_message')

        return redirect('art_gallery')  
    else:
        return HttpResponseBadRequest("Invalid request method.")

def wishlist_view(request):
    events = SpecialEvent.objects.all() 

    if request.user.is_authenticated:
        paintings = request.user.wishlist.all()

        return render(request, 'pages/wishlist.html', {'paintings': paintings, 'events': events})

    return redirect('login')

class WishlistView(ListView):
    model = models.CustomUser
    template_name = 'pages/wishlist.html'

    def get_queryset(self):

        return self.request.user.wishlist.all()

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['events'] = SpecialEvent.objects.all()  

        return context

@login_required
def add_to_wishlist(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        painting_id = data.get('painting_id')
        painting = get_object_or_404(Painting, id=painting_id)

        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=400)

        user.wishlist.add(painting)
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def remove_from_wishlist(request, painting_id):
    if request.method == 'POST':
        painting = Painting.objects.get(id=painting_id)
        request.user.wishlist.remove(painting)
        return redirect('wishlist')  

@login_required
def delete_painting(request, pk):
    if request.method == "POST":
        painting = get_object_or_404(Painting, pk=pk)
        if request.user.is_superuser:
            painting.delete()
            return redirect('mypaintings')  
        return HttpResponseForbidden("Vous n'avez pas l'autorisation de supprimer ce tableau.")
    return redirect('mypaintings')  

@login_required
@user_passes_test(admin_only)
def upload_media(request):
    events = SpecialEvent.objects.all()
    if request.method == 'POST':
        form = MediaUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file')
            if not files:
                messages.error(request, "Aucun fichier n'a été sélectionné.")
                return render(request, 'pages/upload.html', {'form': form, 'events': events})

            max_name_length = 100
            long_names = []
            successful_uploads = 0

            for f in files:
                try:
                    if len(f.name) > max_name_length:
                        long_names.append(f.name)
                    else:
                        media_file = MediaFile(file=f)
                        media_file.save()
                        successful_uploads += 1
                except Exception as e:
                    messages.error(request, f"Erreur lors du téléchargement de {f.name}: {str(e)}")

            if long_names:
                messages.error(request, f"Les fichiers suivants ont des noms trop longs: {', '.join(long_names)}")

            if successful_uploads > 0:
                messages.success(request, f"{successful_uploads} fichier(s) ont été téléchargés avec succès.")
                return redirect('list_media')
    else:
        form = MediaUploadForm()

    return render(request, 'pages/upload.html', {'form': form, 'events': events})

def list_media(request):
    events = SpecialEvent.objects.all()
    media_files = MediaFile.objects.all().order_by('-uploaded_at')

    return render(request, 'pages/list.html', {
        'media_files': media_files,
        'events': events
    })

@login_required
@user_passes_test(admin_only)
def delete_photos(request):
    events = SpecialEvent.objects.all() 
    if request.method == 'POST':
        media_ids = request.POST.getlist('media_ids')
        if media_ids:
            MediaFile.objects.filter(id__in=media_ids).delete()
            messages.success(request, 'Les éléments sélectionnés ont été supprimés avec succès.')
        else:
            messages.warning(request, 'Aucun élément sélectionné pour la suppression.')
        return redirect('delete_photos')  

    media_items = MediaFile.objects.all()  
    return render(request, 'pages/delete_photos.html', {'media_items': media_items,'events':events, 'messages': messages.get_messages(request)})