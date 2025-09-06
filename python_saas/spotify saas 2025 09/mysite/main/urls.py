from django.urls import path
from . import views

app_name = "main"
urlpatterns = [
    path("", views.index, name="index"),
    path("stream/<int:song_id>/", views.stream_audio, name="stream_audio"),
    path("register_user/", views.register_user, name="register_user"),
    path("login_user/", views.login_user, name="login_user"),
    path("logout_user/", views.logout_user, name="logout_user"),
    path("create_playlist/", views.create_playlist, name="create_playlist"),
    path("view_playlist/<int:playlist_id>/", views.view_playlist, name="view_playlist"),
    path("all_playlist/", views.all_playlist, name="all_playlist"),
    path("add_to_playlist/<int:song_id>/", views.add_to_playlist, name="add_to_playlist"),
    path("get_user_playlists/", views.get_user_playlists, name="get_user_playlists"),
]
