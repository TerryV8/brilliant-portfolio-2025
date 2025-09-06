from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Song(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    artist = models.CharField(max_length=200, db_index=True)
    genre = models.CharField(max_length=100)
    audio_url = models.URLField(max_length=500, blank=True, null=True)
    audio_file = models.FileField(upload_to="audio_files/", blank=True, null=True)
    duration = models.PositiveIntegerField(default=0, help_text="Duration in seconds")
    cover_image = models.ImageField(upload_to="cover_images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_playable_url(self):
        """Get the best available playable URL"""
        if self.audio_file:
            return self.audio_file.url
        elif self.audio_url:
            return self.audio_url
        return None

    def youtube_url_modify(self):
        """Convert YouTube URL to embed format with better parsing"""
        if not self.audio_url:
            return None

        # If it's already an embed URL, return as is
        if "embed" in self.audio_url:
            return self.audio_url

        import re

        # Extract video ID using regex for better reliability
        youtube_regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
        match = re.search(youtube_regex, self.audio_url)

        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/embed/{video_id}?autoplay=1&controls=1"

        return self.audio_url

    @property
    def is_youtube_url(self):
        """Check if the audio_url is a YouTube URL"""
        if not self.audio_url:
            return False
        return (
            "youtube" in self.audio_url.lower() or "youtu.be" in self.audio_url.lower()
        )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["title", "artist"]),
        ]


class Playlist(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="playlists")
    song = models.ManyToManyField(Song, related_name="playlists")

    def __str__(self):
        return f"{self.name} - {self.user.username}"
