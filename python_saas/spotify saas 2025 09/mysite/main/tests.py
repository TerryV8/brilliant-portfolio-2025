from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Song, Playlist


class SongModelTest(TestCase):
    def setUp(self):
        self.song = Song.objects.create(
            title="Test Song",
            artist="Test Artist",
            genre="Pop",
            audio_url="https://www.youtube.com/watch?v=test123",
            duration=180
        )

    def test_song_creation(self):
        """Test that a song is created properly"""
        self.assertEqual(self.song.title, "Test Song")
        self.assertEqual(self.song.artist, "Test Artist")
        self.assertEqual(self.song.genre, "Pop")
        self.assertEqual(self.song.duration, 180)

    def test_song_str_method(self):
        """Test the string representation of the song"""
        self.assertEqual(str(self.song), "Test Song")

    def test_is_youtube_url(self):
        """Test YouTube URL detection"""
        self.assertTrue(self.song.is_youtube_url)

    def test_get_playable_url(self):
        """Test getting playable URL"""
        self.assertEqual(self.song.get_playable_url(), self.song.audio_url)


class PlaylistModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.song = Song.objects.create(
            title="Test Song",
            artist="Test Artist",
            genre="Pop"
        )
        self.playlist = Playlist.objects.create(
            name="Test Playlist",
            user=self.user
        )
        self.playlist.song.add(self.song)

    def test_playlist_creation(self):
        """Test that a playlist is created properly"""
        self.assertEqual(self.playlist.name, "Test Playlist")
        self.assertEqual(self.playlist.user, self.user)
        self.assertIn(self.song, self.playlist.song.all())

    def test_playlist_str_method(self):
        """Test the string representation of the playlist"""
        expected_str = f"Test Playlist - {self.user.username}"
        self.assertEqual(str(self.playlist), expected_str)


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.song = Song.objects.create(
            title="Test Song",
            artist="Test Artist",
            genre="Pop"
        )

    def test_index_view(self):
        """Test the index view loads properly"""
        response = self.client.get(reverse('main:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Song")

    def test_authenticated_user_features(self):
        """Test that authenticated users can access playlist features"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('main:index'))
        self.assertEqual(response.status_code, 200)
        # Check that playlist buttons are visible for authenticated users
        self.assertContains(response, "add-to-playlist-btn")
