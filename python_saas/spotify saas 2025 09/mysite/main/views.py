import os
import logging
import yt_dlp
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.conf import settings
from django.core.files.base import ContentFile

from .models import Song, Playlist


from django.contrib.auth import login, authenticate, logout

# from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages

from django.contrib.auth.models import User


logger = logging.getLogger(__name__)


def index(request):
    """Home page view displaying all songs"""
    songs = Song.objects.all()

    play_song_id = request.GET.get("play", None)
    play_song = None

    if play_song_id:
        play_song = get_object_or_404(Song, id=play_song_id)

    return render(request, "main/index.html", {"songs": songs, "play_song": play_song})


def extract_youtube_audio(song):
    """Extract audio from YouTube URL and save to media directory"""
    if not song.is_youtube_url:
        logger.warning(f"Invalid YouTube URL for song {song.id}: {song.audio_url}")
        return None

    # Check if audio file already exists to avoid re-extraction
    if song.audio_file:
        logger.info(f"Audio file already exists for song {song.id}")
        return {"success": True, "title": song.title, "duration": 0}

    logger.info(f"Starting YouTube audio extraction for song {song.id}")
    try:
        # Create media directory if it doesn't exist
        audio_dir = os.path.join(settings.MEDIA_ROOT, "extracted_audio")
        os.makedirs(audio_dir, exist_ok=True)

        # Configure yt-dlp options
        ydl_opts = {
            "format": "bestaudio/best",
            "extractaudio": True,
            "audioformat": "mp3",
            "outtmpl": os.path.join(audio_dir, f"{song.id}_%(title)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(song.audio_url, download=False)
            title = info.get("title", "Unknown")
            duration = info.get("duration", 0)

            # Download audio
            ydl.download([song.audio_url])

            # Find the downloaded file
            for filename in os.listdir(audio_dir):
                if filename.startswith(f"{song.id}_"):
                    file_path = os.path.join(audio_dir, filename)

                    # Save to Django model
                    with open(file_path, "rb") as f:
                        audio_content = ContentFile(f.read())
                        song.audio_file.save(
                            f"{song.id}_{title[:50]}.mp3", audio_content, save=True
                        )

                    # Clean up temporary file
                    os.remove(file_path)

                    return {"success": True, "title": title, "duration": duration}

        return None

    except Exception as e:
        logger.error(f"YouTube extraction failed for song {song.id}: {str(e)}")
        return {"success": False, "error": str(e)}


def stream_audio(request, song_id):
    """Get streaming URL for a song - supports both audio files and YouTube"""
    # Validate song_id is a positive integer
    try:
        song_id = int(song_id)
        if song_id <= 0:
            return JsonResponse({"success": False, "error": "Invalid song ID"})
    except (ValueError, TypeError):
        return JsonResponse({"success": False, "error": "Invalid song ID format"})

    try:
        song = get_object_or_404(Song, id=song_id)
        logger.info(f"Processing stream request for song {song_id}: {song.title}")

        # Check if it's a direct audio file (most reliable)
        if song.audio_file:
            return JsonResponse(
                {
                    "success": True,
                    "stream_url": song.audio_file.url,
                    "title": song.title,
                    "artist": song.artist,
                    "duration": 0,
                    "method": "direct_audio",
                    "is_direct": True,
                }
            )

        # Handle YouTube URLs for extraction
        elif song.audio_url:
            # Try to extract YouTube audio
            extraction_result = extract_youtube_audio(song)

            if extraction_result and extraction_result.get("success"):
                # Extraction successful, now serve the extracted audio
                return JsonResponse(
                    {
                        "success": True,
                        "stream_url": song.audio_file.url,
                        "title": song.title,
                        "artist": song.artist,
                        "duration": extraction_result.get("duration", 0),
                        "method": "extracted_audio",
                        "is_direct": True,
                    }
                )
            else:
                # Extraction failed, fall back to YouTube embed
                embed_url = song.youtube_url_modify()
                return JsonResponse(
                    {
                        "success": True,
                        "stream_url": embed_url,
                        "title": song.title,
                        "artist": song.artist,
                        "duration": 0,
                        "method": "youtube_embed",
                        "is_embed": True,
                    }
                )

        else:
            return JsonResponse(
                {"success": False, "error": "No audio source available"}
            )

    except Exception as e:
        logger.error(f"Stream audio error for song {song_id}: {str(e)}")
        return JsonResponse({"success": False, "error": "Unable to load audio"})


def register_user(request):
    """User registration view"""
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        password2 = request.POST["password2"]

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "main/register_user.html", {"username": username})

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "main/register_user.html", {"username": username})

        try:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)

            messages.success(
                request,
                f"Welcome {user.username}! Your account has been created successfully.",
            )

            return render(request, "main/index.html")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, "main/register_user.html", {"username": username})

    return render(request, "main/register_user.html")


def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("main:index")

        messages.error(request, "Invalid username or password.")
        return render(request, "main/login_user.html")

    return render(request, "main/login_user.html")


def logout_user(request):
    """User logout view"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("main:index")


def create_playlist(request):
    if request.method == "POST":
        name_playlist = request.POST["name-playlist"]

        if request.user.is_authenticated:
            create_playlist = Playlist.objects.create(
                name=name_playlist, user=request.user
            )
            create_playlist.save()
            messages.success(request, "Playlist created successfully.")
            return redirect("main:index")

        else:
            return redirect("main:index")

    return render(request, "main/create_playlist.html")


def view_playlist(request, playlist_id):
    if request.user.is_authenticated:
        playlist = Playlist.objects.get(id=playlist_id, user=request.user)
        return render(
            request,
            "main/view_playlist.html",
            {"playlist": playlist},
        )
    else:
        return redirect("main:index")


def all_playlist(request):
    if request.user.is_authenticated:
        playlists = Playlist.objects.filter(user=request.user)
        return render(
            request,
            "main/all_playlist.html",
            {"playlists": playlists},
        )
    else:
        return redirect("main:index")


def add_to_playlist(request, song_id):
    """Add a song to a playlist via AJAX"""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "User not authenticated"})
    
    if request.method == "POST":
        try:
            song = get_object_or_404(Song, id=song_id)
            playlist_id = request.POST.get("playlist_id")
            
            if not playlist_id:
                return JsonResponse({"success": False, "error": "No playlist selected"})
            
            playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
            
            # Check if song is already in playlist
            if playlist.song.filter(id=song_id).exists():
                return JsonResponse({"success": False, "error": "Song already in playlist"})
            
            # Add song to playlist
            playlist.song.add(song)
            
            return JsonResponse({
                "success": True, 
                "message": f"'{song.title}' added to '{playlist.name}'"
            })
            
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Invalid request method"})


def get_user_playlists(request):
    """Get user's playlists for dropdown selection"""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "User not authenticated"})
    
    playlists = Playlist.objects.filter(user=request.user).values('id', 'name')
    return JsonResponse({"success": True, "playlists": list(playlists)})
