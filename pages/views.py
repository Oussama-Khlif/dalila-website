import json
from django.views.generic.list import ListView
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg
from human_ressorces import models
from .models import Painting, Rating, Video, SpecialEvent
from .forms import PaintingForm, SpecialEventForm
from .forms import VideoForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Painting
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import MediaFile
from human_ressorces.models import Atelier
from decimal import Decimal, ROUND_DOWN
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Painting
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden
from .models import Painting
from django.shortcuts import render, redirect
from .forms import MediaUploadForm
from .models import MediaFile
from django.contrib import messages

def admin_only(user):
    return user.is_superuser or user.username == 'admin'

def about(request):
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None  # Handle case where no event is available
    return render(request, 'pages/about.html', {'event': event})

def calligraphy(request):
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None  # Handle case where no event is available

    atelier = Atelier.objects.filter(name='Calligraphie').first()  # Fetch specific Atelier for Calligraphy
    return render(request, 'pages/workshops/calligraphy.html', {'event': event, 'atelier': atelier})

def languages(request):
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None  # Handle case where no event is available

    atelier = Atelier.objects.filter(name='Langues').first()  # Fetch specific Atelier for Languages
    return render(request, 'pages/workshops/languages.html', {'event': event, 'atelier': atelier})

def theater(request):
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None  # Handle case where no event is available

    atelier = Atelier.objects.filter(name='Théâtre').first()  # Fetch specific Atelier for Theater
    return render(request, 'pages/workshops/theater.html', {'event': event, 'atelier': atelier})

def mental_calculation(request):
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None  # Handle case where no event is available

    atelier = Atelier.objects.filter(name='Calcul Mental').first()  # Fetch specific Atelier for Mental Calculation
    return render(request, 'pages/workshops/mental_calculation.html', {'event': event, 'atelier': atelier})

def music(request):
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None  # Handle case where no event is available

    # Fetch all ateliers related to music
    ateliers = Atelier.objects.filter(name__icontains='Musique')  # Fetch ateliers containing "Musique"

    return render(request, 'pages/workshops/music.html', {'event': event, 'ateliers': ateliers})

def paint(request):
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None  # Handle case where no event is available

    atelier = Atelier.objects.filter(name='Peinture').first()  # Fetch specific Atelier for Paint

    # Ensure that atelier.price is a Decimal
    if atelier and atelier.price is not None:
        original_price = atelier.price  # This should already be a Decimal
        over_12 = (original_price + Decimal('5')).quantize(Decimal('0.01'), rounding=ROUND_DOWN)  # Add 5 to original price
        non_child_price = (original_price + Decimal('25')).quantize(Decimal('0.01'), rounding=ROUND_DOWN)  # Add 25 to original price

    else:
        over_12 = None
        non_child_price = None

    return render(request, 'pages/workshops/paint.html', {
        'event': event,
        'atelier': atelier,
        'over_12': over_12,
        'non_child_price': non_child_price,
    })

def robotics(request):
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None  # Handle case where no event is available

    atelier = Atelier.objects.filter(name='Robotique').first()  # Fetch specific Atelier for Robotics
    return render(request, 'pages/workshops/robotics.html', {'event': event, 'atelier': atelier})

def index(request):
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None  # Handle case where no event is available

    latest_video = Video.objects.latest('id') if Video.objects.exists() else None

    return render(request, 'pages/index.html', {
        'event': event,
        'latest_video': latest_video,
    })

@login_required
@user_passes_test(admin_only)
def update_event(request):
    try:
        event = SpecialEvent.objects.latest('updated_at')  # Get the latest event by updated_at
    except SpecialEvent.DoesNotExist:
        event = None  # No existing event

    if request.method == 'POST':
        # Check if the delete button is pressed
        if 'delete_event' in request.POST:
            event_id = request.POST.get('delete_event')
            try:
                event_to_delete = SpecialEvent.objects.get(id=event_id)
                event_to_delete.delete()  # Delete the event
                return redirect('index')  # Redirect to the index page after deletion
            except SpecialEvent.DoesNotExist:
                pass  # Handle if the event does not exist (edge case)

        # Create the event form
        if event:  # If an event exists, update it
            form = SpecialEventForm(request.POST, request.FILES, instance=event)
        else:  # If no event exists, create a new one
            form = SpecialEventForm(request.POST, request.FILES)

        if form.is_valid():
            event = form.save()  # Save the SpecialEvent instance
            
            # Now save the image to the MediaFile model
            if request.FILES.get('image'):
                media_file = MediaFile(file=request.FILES['image'])
                media_file.save()  # Save the MediaFile instance

            return redirect('index')
    else:
        form = SpecialEventForm(instance=event) if event else SpecialEventForm()

    return render(request, 'pages/update_event.html', {'event_form': form, 'event': event})

@login_required
@user_passes_test(admin_only)
def upload_video(request):
    # Fetch the latest event
    try:
        event = SpecialEvent.objects.latest('updated_at')
    except SpecialEvent.DoesNotExist:
        event = None  # No existing event, so we set event to None

    # Get the current video (assuming only one video exists)
    current_video = Video.objects.first()

    if request.method == 'POST':
        # Handle video deletion if the delete button is clicked
        if 'delete' in request.POST:
            video_id = request.POST.get('delete')
            try:
                video_to_delete = Video.objects.get(id=video_id)
                video_to_delete.delete()  # Delete the video instance
                return redirect('index')  # Redirect after deletion
            except Video.DoesNotExist:
                pass

        # Handle video upload or update
        video_form = VideoForm(request.POST, request.FILES, instance=current_video)  # Prepopulate form with current video
        if video_form.is_valid():
            # Save the video instance (update if current_video exists)
            video_instance = video_form.save()

            # Save the video file to the MediaFile model
            media_file = MediaFile(file=video_instance.video_file)  # Assuming MediaFile has a 'file' field
            media_file.save()

            # Optional: Associate the video with the latest event if desired
            if event:
                media_file.event = event
                media_file.save()

            return redirect('index')
    else:
        # Prepopulate the form with the current video if it exists
        video_form = VideoForm(instance=current_video)

    return render(request, 'pages/upload_video.html', {
        'form': video_form,
        'event': event,
        'video': current_video,  # Pass the current video to the template
    })

@login_required
def add_painting(request):
    if request.method == 'POST':
        if 'upload_submit' in request.POST:
            form = PaintingForm(request.POST, request.FILES)
            if form.is_valid():
                painting = form.save(commit=False)
                painting.user = request.user  # Associate painting with the logged-in user
                painting.save()
                return redirect('mypaintings')  # Redirect to the mypaintings page after adding
    else:
        form = PaintingForm()

    return render(request, 'pages/addpainting.html', {
        'form': form,
    })

@login_required
def my_paintings(request):
    if request.method == 'POST' and 'delete_painting' in request.POST:
        painting_id = request.POST.get('painting_id')
        try:
            painting_to_delete = Painting.objects.get(id=painting_id, user=request.user)
            painting_to_delete.delete()
            messages.success(request, "Votre peinture a été supprimée avec succès !")  # Success message
        except Painting.DoesNotExist:
            messages.error(request, "Cette peinture n'existe pas ou vous n'avez pas les droits pour la supprimer.")  # Error message

    paintings = Painting.objects.filter(user=request.user)
    return render(request, 'pages/mypaintings.html', {
        'paintings': paintings
    })

@login_required
def edit_painting(request, painting_id):
    painting = get_object_or_404(Painting, id=painting_id, user=request.user)

    if request.method == 'POST':
        form = PaintingForm(request.POST, request.FILES, instance=painting)
        if form.is_valid():
            form.save()
            return redirect('mypaintings')  # Redirect to the page where paintings are managed
    else:
        form = PaintingForm(instance=painting)

    return render(request, 'pages/edit_painting.html', {'form': form, 'painting': painting})

def art_gallery(request):
    # Calculate average rating for each painting and order by average rating
    paintings = Painting.objects.annotate(
        average_rating=Avg('ratings__score')
    ).order_by('-average_rating')  # Order from highest to lowest average rating

    return render(request, 'pages/artgallery.html', {
        'paintings': paintings,
    })

@login_required
def user_paintings(request):
    """Fetch paintings uploaded by the logged-in user."""
    return Painting.objects.filter(user=request.user)

def painting_details(request, painting_id):
    painting = get_object_or_404(Painting, id=painting_id)
    return render(request, 'pages/painting_details.html', {
        'painting': painting,
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

            # Add success message with key 'rate_message'
            messages.add_message(request, messages.SUCCESS, 'Merci pour votre évaluation', extra_tags='rate_message')

        return redirect('art_gallery')  # Redirect to the art gallery or another page
    else:
        return HttpResponseBadRequest("Invalid request method.")

def wishlist_view(request):
    if request.user.is_authenticated:
        paintings = request.user.wishlist.all()
        return render(request, 'pages/wishlist.html', {'paintings': paintings})
    return redirect('login')

class WishlistView(ListView):
    model = models.CustomUser
    template_name = 'pages/wishlist.html'
    
    def get_queryset(self):
        return self.request.user.wishlist.all()

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
        return redirect('wishlist')  # Redirect to the wishlist page after removal

def delete_painting(request, pk):
    if request.method == "POST":
        painting = get_object_or_404(Painting, pk=pk)
        if request.user.is_superuser:
            painting.delete()
            return redirect('art_gallery')  # Redirect to the gallery after deletion
        return HttpResponseForbidden("Vous n'avez pas l'autorisation de supprimer ce tableau.")
    return redirect('art_gallery')  # Redirect to gallery if not POST request

def upload_media(request):
    if request.method == 'POST':
        form = MediaUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file')  # 'file' should match your field name
            max_name_length = 100  # Define the maximum file name length
            long_names = []  # To store file names that are too long

            for f in files:
                if len(f.name) > max_name_length:
                    long_names.append(f.name)  # Collect names that are too long
                else:
                    media_file = MediaFile(file=f)  # Create instance with uploaded file
                    media_file.save()  # This will trigger the compression and save process

            # If any file name is too long, add a message and stop the upload
            if long_names:
                messages.error(request, f"Les fichiers suivants ont des noms trop longs")
            else:
                # Success message
                messages.success(request, "Les fichiers ont été téléchargés avec succès.")
                return redirect('list_media')  # Redirect after successful upload

    else:
        form = MediaUploadForm()
    
    return render(request, 'pages/upload.html', {'form': form})

def list_media(request):
    media_files = MediaFile.objects.all()
    return render(request, 'pages/list.html', {'media_files': media_files})

def delete_photos(request):
    if request.method == 'POST':
        media_ids = request.POST.getlist('media_ids')
        if media_ids:
            MediaFile.objects.filter(id__in=media_ids).delete()
            messages.success(request, 'Les éléments sélectionnés ont été supprimés avec succès.')
        else:
            messages.warning(request, 'Aucun élément sélectionné pour la suppression.')
        return redirect('delete_photos')  # Adjust the redirect as necessary

    media_items = MediaFile.objects.all()  # Adjust this query as needed
    return render(request, 'pages/delete_photos.html', {'media_items': media_items, 'messages': messages.get_messages(request)})
