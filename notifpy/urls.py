from django.urls import path
from . import views

app_name = "notifpy"

urlpatterns = [
    path("", views.abstract, name="abstract"),
    path("home", views.home, name="home"),
    path("oauth/<source>", views.oauth_redirect, name="oauth_redirect"),
    path("oauth/<source>/refresh", views.refresh_token, name="refresh_token"),
    path("oauth/<source>/revoke", views.revoke_token, name="revoke_token"),
    path("create-channel", views.create_channel, name="create_channel"),
    path("channel/<slug>", views.view_channel, name="channel"),
    path("channel/<slug>/edit", views.edit_channel, name="edit_channel"),
    path("channel/<slug>/delete", views.delete_channel, name="delete_channel"),
    path("channel/<slug>/update", views.update_channel, name="update_channel"),
    path("update", views.update_channels, name="update"),
    path("create-filter", views.create_filter, name="create_filter"),
    path("delete-filter", views.delete_filter, name="delete_filter"),
    path("create-playlist", views.create_playlist, name="create_playlist"),
    path("playlists/<slug>", views.view_playlist, name="playlist"),
    path("playlists/<slug>/add", views.add_playlist, name="add_playlist"),
    path("playlists/<slug>/edit", views.edit_playlist, name="edit_playlist"),
    path("playlists/<slug>/delete", views.delete_playlist, name="delete_playlist"),
    path("playlists/<slug>/remove", views.remove_playlist, name="remove_playlist"),
    path("playlists/<slug>/move/<order>/<direction>", views.move_playlist, name="move_playlist"),
    path("create-twitch-user", views.create_twitch_user, name="create_twitch_user"),
    path("twitch-user/<login>/delete", views.delete_twitch_user, name="delete_twitch_user"),
    path("manage-endpoints", views.manage_endpoints, name="manage_endpoints"),
    path("settings", views.settings, name="settings"),
    path("edit-schedule", views.edit_schedule, name="edit_schedule"),
    path("clear", views.clear_old_videos, name="clear_old_videos"),
    path("twitch-api", views.twitch_streams_api, name="twitch_streams_api"),
    path("playlists", views.view_playlists, name="playlists"),
]
