"""This module contains all views from the application"""

import re
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.urls import reverse
from django.http import HttpResponse
from django.db.models.functions import Lower
from django.http import Http404
from django.core.exceptions import PermissionDenied
from piweb.decorators import require_app_access, require_superuser
from piweb.utils import pretty_paginator
from . import operator
from . import models


def abstract(request):
    """View with abstract of the application"""
    return render(request, "notifpy/abstract.html", {})


# VIEWS FOR HOMEPAGE


@require_app_access("notifpy")
def home(request):
    """Main view to display last updates."""
    page_size = 18
    page = int(request.GET.get("page", 1))
    order = request.GET.get("order", "publication")
    querysets = []
    for subscription in models.YoutubeSubscription.objects.filter(user=request.user):
        filters = models.Filter.objects.filter(channel=subscription.channel, user=request.user)
        if filters:
            regex = "(" + "|".join(map(lambda f: f.regex, filters)) + ")"
            queryset = subscription.channel.youtubevideo_set.filter(title__iregex=regex)
        else:
            queryset = subscription.channel.youtubevideo_set.all()
        querysets.append(queryset)
    video_list = []
    if len(querysets) > 0:
        video_list = querysets[0].union(*querysets[1:]).order_by("-" + order)
    paginator = Paginator(video_list, page_size)
    videos = paginator.get_page(page)
    return render(request, "notifpy/home.html", {
        "videos": videos,
        "video_paginator": pretty_paginator(videos),
    })


@require_app_access("notifpy")
def twitch_streams_api(request):
    """View that simply returns a JSON from Twitch endpoint"""
    body = list()
    twitch_users = [
        subscription.channel
        for subscription in models.TwitchSubscription.objects.filter(user=request.user)
    ]
    streams = operator.Operator().get_streams(twitch_users)
    if streams is not None:
        for stream in streams:
            body.append({
                "lnk": stream["user"].link(),
                "thumb": stream["user"].thumbnail(),
                "name": stream["user_name"],
                "game": "Uncategorized",
                "title": stream["title"],
                "screen": stream["thumbnail"],
                "started_at": stream["started_at"],
                "viewer_count": stream["viewer_count"],
            })
            if stream["game"] is not None:
                body[-1]["game"] = stream["game"].name
    return HttpResponse(json.dumps(body), content_type="application/json")


# VIEWS FOR PLAYLIST


@require_app_access("notifpy")
def create_playlist(request):
    """Add a new playlist object"""
    if request.method == "POST":
        title = request.POST.get("title", "Untitled")
        if models.Playlist.objects.filter(owner=request.user, title=title).exists():
            playlist = models.Playlist.objects.get(owner=request.user, title=title)
        else:
            playlist = models.Playlist.objects.create(
                owner=request.user,
                title=request.POST["title"]
            )
        return redirect("notifpy:playlist", slug=playlist.slug)
    return redirect("notifpy:playlists")


def get_playlist_from_slug(slug, required_owner=None):
    if not models.Playlist.objects.filter(slug=slug).exists():
        raise Http404("Playlist does not exist")
    playlist = models.Playlist.objects.get(slug=slug)
    if required_owner is not None and playlist.owner != required_owner:
        raise PermissionDenied
    return playlist


def view_playlist(request, slug):
    """View a playlist"""
    playlist = get_playlist_from_slug(slug)
    if not playlist.public and (
            not request.user.is_authenticated
            or playlist.owner != request.user):
        return redirect("notifpy:abstract")
    playlist.owned = playlist.owner == request.user
    return render(request, "notifpy/playlist.html", {
        "playlist": playlist,
    })


@require_app_access("notifpy")
def edit_playlist(request, slug):
    """Edit playlist properties"""
    playlist = get_playlist_from_slug(slug, request.user)
    if request.method == "POST":
        title = request.POST["title"]
        playlist.title = title
        playlist.save()
    return redirect("notifpy:playlist", slug=playlist.slug)


@require_app_access("notifpy")
def add_playlist(request, slug):
    """Add a video (or more) to a playlist"""
    playlist = get_playlist_from_slug(slug, request.user)
    if request.method == "POST":
        operator.Operator().add_video_to_playlist(
            playlist, request.POST.get("video", ""))
    return redirect("notifpy:playlist", slug=playlist.slug)


@require_app_access("notifpy")
def remove_playlist(request, slug):
    """Remove a video from a playlist"""
    playlist = get_playlist_from_slug(slug, request.user)
    if request.method == "POST":
        video = models.YoutubeVideo.objects.get(id=request.POST["id"])
        playlist.videos.remove(video)
        playlist.save()
        playlist.shift_orders()
    return redirect("notifpy:playlist", slug=playlist.slug)


@require_app_access("notifpy")
def delete_playlist(request, slug):
    """Delete a playlist"""
    playlist = get_playlist_from_slug(slug, request.user)
    playlist.delete()
    return redirect("notifpy:playlists")


@require_app_access("notifpy")
def order_playlist(request, slug):
    playlist = get_playlist_from_slug(slug, request.user)
    if request.method == "POST":
        ordering = dict()
        for i, playlist_membership_id in enumerate(request.POST.get("ordering").split(";")):
            ordering[int(playlist_membership_id)] = i
        for playlist_membership in playlist.playlistmembership_set.all():
            if playlist_membership.id in ordering:
                playlist_membership.order = ordering[playlist_membership.id]
                playlist_membership.save()
    return redirect("notifpy:playlist", slug=playlist.slug)


@require_app_access("notifpy")
def move_playlist(request, slug, order, direction):
    """Edit the video odering within a playlist"""
    playlist = get_playlist_from_slug(slug, request.user)
    ref = models.PlaylistMembership.objects.get(
        playlist=playlist, order=int(order))
    if direction == "up":
        new = models.PlaylistMembership.objects.get(
            playlist=playlist, order=int(order) - 1)
    elif direction == "down":
        new = models.PlaylistMembership.objects.get(
            playlist=playlist, order=int(order) + 1)
    ref.order = new.order
    ref.save()
    new.order = int(order)
    new.save()
    return redirect("notifpy:playlist", slug=playlist.slug)


@require_app_access("notifpy")
def publish_playlist(request, slug, state):
    """Change the public attribute of a given playlist"""
    playlist = get_playlist_from_slug(slug, request.user)
    if state == "public":
        playlist.public = True
    elif state == "private":
        playlist.public = False
    playlist.save()
    return redirect("notifpy:playlist", slug=playlist.slug)


@require_app_access("notifpy")
def view_playlists(request):
    """View playlists"""
    playlists = models.Playlist.objects.filter(owner=request.user)
    return render(request, "notifpy/playlists.html", {
        "playlists": playlists,
    })


# VIEWS FOR YOUTUBE CHANNELS


@require_app_access("notifpy")
def view_channel(request, slug):
    """View all information about a YouTube channel"""
    if not models.YoutubeChannel.objects.filter(slug=slug).exists():
        raise Http404("Channel not found.")
    channel = models.YoutubeChannel.objects.get(slug=slug)
    subscribed = models.YoutubeSubscription.objects.filter(channel=channel, user=request.user).exists()
    filters = models.Filter.objects.filter(channel=channel, user=request.user)
    if filters:
        regex = "(" + "|".join(map(lambda f: f.regex, filters)) + ")"
        videos = channel.youtubevideo_set.filter(title__iregex=regex).order_by("-publication")[:15]
    else:
        videos = channel.youtubevideo_set.order_by("-publication")[:15]
    return render(request, "notifpy/channel.html", {
        "channel": channel,
        "videos": videos,
        "subscribed": subscribed,
        "filters": filters,
    })


@require_superuser
def edit_channel(request, slug):
    """Edit a YouTube channel information"""
    if not request.user.is_staff or not models.YoutubeChannel.objects.filter(slug=slug).exists():
        return redirect("notifpy:home")
    channel = models.YoutubeChannel.objects.get(slug=slug)
    if request.method == "POST":
        if "thumbnail" in request.POST:
            channel.thumbnail = request.POST["thumbnail"]
        if "priority" in request.POST:
            channel.priority = request.POST["priority"]
        channel.save()
    return redirect("notifpy:channel", slug=slug)


@require_superuser
def delete_channel(_, slug):
    """Unsubscribe from a channel"""
    if models.YoutubeChannel.objects.filter(slug=slug).exists():
        channel = models.YoutubeChannel.objects.get(slug=slug)
        channel.delete()
    return redirect("notifpy:home")


@require_superuser
def update_channel(_, slug):
    """Update a YouTube channel videos"""
    if not models.YoutubeChannel.objects.filter(slug=slug).exists():
        return redirect("notifpy:home")
    channel = models.YoutubeChannel.objects.get(slug=slug)
    operator.Operator().update_channel(channel)
    return redirect("notifpy:channel", slug=channel.slug)


@require_app_access("notifpy")
def create_filter(request):
    """Append a filter to a channel"""
    if request.method == "POST":
        channel = models.YoutubeChannel.objects.get(id=request.POST["channel"])
        for regex in request.POST["regexes"].split("\n"):
            filters = models.Filter.objects.create(
                user=request.user,
                channel=channel,
                regex=re.sub("\r", "", regex)
            )
            filters.save()
        return redirect("notifpy:channel", slug=channel.slug)
    return redirect("notifpy:home")


@require_app_access("notifpy")
def delete_filter(request):
    """Delete a filter from a channel"""
    if request.method == "POST":
        filters = models.Filter.objects.get(id=request.POST["id"])
        if filters.user != request.user and not request.user.is_superuser:
            raise PermissionDenied
        slug = filters.channel.slug
        filters.delete()
        return redirect("notifpy:channel", slug=slug)
    return redirect("notifpy:home")


# VIEWS FOR TWITCH USERS


@require_app_access("notifpy")
def view_user(request, login):
    """View all information about a YouTube channel"""
    if not models.TwitchUser.objects.filter(login=login).exists():
        raise Http404("Twitch user not found.")
    user = models.TwitchUser.objects.get(login=login)
    subscribed = models.TwitchSubscription.objects.filter(channel=user, user=request.user).exists()
    return render(request, "notifpy/user.html", {
        "user": user,
        "subscribed": subscribed,
    })


@require_superuser
def delete_twitch_user(_, login):
    """Unfollow a Twitch user"""
    if models.TwitchUser.objects.filter(login=login).exists():
        user = models.TwitchUser.objects.get(login=login)
        user.delete()
    return redirect("notifpy:home")


@require_app_access("notifpy")
def update_profile_picture(request, login):
    """Force update the profile picture of a given Twitch user"""
    operator.Operator().update_user_thumbnail(login)
    return redirect("notifpy:view_twitch_user", login=login)


# VIEWS FOR SUBSCRIPTIONS


@require_app_access("notifpy")
def subscriptions(request):
    """View to a user current subscriptions"""
    history, _ = models.SubscriptionHistory.objects.get_or_create(user=request.user)
    youtube_subscriptions = dict()
    for subscription in models.YoutubeSubscription.objects.filter(user=request.user):
        youtube_subscriptions[subscription.channel.id] = True
    channels = history.youtube.order_by("title")
    if request.user.is_superuser:
        channels = models.YoutubeChannel.objects.order_by("title")
    for channel in channels:
        channel.subscribed = youtube_subscriptions.get(channel.id, False)
        channel.thumbnail_link = channel.thumbnail.replace("=s800", "=s32")
    twitch_subscriptions = dict()
    for subscription in models.TwitchSubscription.objects.filter(user=request.user):
        twitch_subscriptions[subscription.channel.id] = True
    users = history.twitch.order_by("login")
    if request.user.is_superuser:
        users = models.TwitchUser.objects.order_by("login")
    for user in users:
        user.subscribed = twitch_subscriptions.get(user.id, False)    
    return render(request, "notifpy/subscriptions.html", {
        "history": history,
        "channels": channels,
        "users": users,
    })


@require_app_access("notifpy")
def subscribe(request):
    """View to subscribe the logged in user to a channel"""
    if request.method == "POST":
        channels = set()
        users = set()
        for key in request.POST:
            if key.startswith("youtube-"):
                channel_id = key[8:]
                if models.YoutubeChannel.objects.filter(id=channel_id).exists():
                    channels.add(models.YoutubeChannel.objects.get(id=channel_id))
            elif key.startswith("twitch-"):
                user_id = key[7:]
                if models.TwitchUser.objects.filter(id=user_id).exists():
                    users.add(models.TwitchUser.objects.get(id=user_id))
        action = request.POST.get("action")
        if action == "Subscribe":
            for channel in channels:
                if not models.YoutubeSubscription.objects.filter(channel=channel, user=request.user).exists():
                    models.YoutubeSubscription.objects.create(channel=channel, user=request.user)
            for user in users:
                if not models.TwitchSubscription.objects.filter(channel=user, user=request.user).exists():
                    models.TwitchSubscription.objects.create(channel=user, user=request.user)
        elif action == "Unsubscribe" or action == "Remove from history":
            for channel in channels:
                for entry in models.YoutubeSubscription.objects.filter(channel=channel, user=request.user):
                    entry.delete()
            for user in users:
                for entry in models.TwitchSubscription.objects.filter(channel=user, user=request.user):
                    entry.delete()
            history = getattr(request.user, "subscriptionhistory", None)
            if action == "Remove from history" and history is not None:
                for channel in channels:
                    history.youtube.remove(channel)
                for user in users:
                    history.twitch.remove(user)
    return redirect("notifpy:subscriptions")


@require_app_access("notifpy")
def create_channel(request):
    """Subscribe to a YouTube channel"""
    if request.method == "POST" and "query" in request.POST:
        result = operator.Operator().subscribe_to_channels(request.POST["query"])
        history, _ = models.SubscriptionHistory.objects.get_or_create(user=request.user)
        for channel in result["channels"]:
            history.youtube.add(channel)
            if not models.YoutubeSubscription.objects.filter(channel=channel, user=request.user).exists():
                models.YoutubeSubscription.objects.create(channel=channel, user=request.user)
    return redirect("notifpy:subscriptions")


@require_app_access("notifpy")
def create_twitch_user(request):
    """Follow a Twitch user"""
    if request.method == "POST" and "query" in request.POST:
        result = operator.Operator().follow_users(request.POST["query"])
        history, _ = models.SubscriptionHistory.objects.get_or_create(user=request.user)
        for user in result["users"]:
            history.twitch.add(user)
            if not models.TwitchSubscription.objects.filter(channel=user, user=request.user).exists():
                models.TwitchSubscription.objects.create(channel=user, user=request.user)
    return redirect("notifpy:subscriptions")


# VIEWS FOR SETTINGS


@require_superuser
def settings(request):
    """View to show general information and forms"""
    schedule = models.UpdateSchedule.objects.get().to_json()
    current_schedule = {
        "low": " ".join(map(str, schedule["0"])),
        "medium": " ".join(map(str, schedule["1"])),
        "high": " ".join(map(str, schedule["2"]))
    }
    channels = models.YoutubeChannel.objects\
        .exclude(priority=models.YoutubeChannel.PRIORITY_NONE)\
        .order_by("slug")
    users = models.TwitchUser.objects\
        .all()\
        .extra(select={'lower_name': 'lower(display_name)'})\
        .order_by("lower_name")
    return render(request, "notifpy/settings.html", {
        "current_schedule": current_schedule,
        "operator": operator.Operator(),
        "channels": channels,
        "users": users,
    })


@require_superuser
def oauth_redirect(request, source):
    """Redirection handling during OAuth flow"""
    opr = operator.Operator()
    if source == "youtube" and opr.youtube is not None:
        opr.youtube.oauth_flow.handle_redirect(request)
    elif source == "twitch" and opr.twitch is not None:
        opr.twitch.oauth_flow.handle_redirect(request)
    return redirect("notifpy:settings")


@require_superuser
def refresh_token(_, source):
    """Request an endpoint token to be refreshed"""
    opr = operator.Operator()
    if source == "youtube" and opr.youtube is not None:
        opr.youtube.oauth_flow.refresh()
    elif source == "twitch" and opr.twitch is not None:
        opr.twitch.oauth_flow.refresh()
    return redirect("notifpy:settings")


@require_superuser
def revoke_token(_, source):
    """Request an endpoint token to be revoked"""
    opr = operator.Operator()
    if source == "youtube" and opr.youtube is not None:
        opr.youtube.oauth_flow.revoke()
    elif source == "twitch" and opr.twitch is not None:
        opr.twitch.oauth_flow.revoke()
    return redirect("notifpy:settings")


@require_superuser
def clear_old_videos(request):
    """Remove old videos from database"""
    if request.method == "POST":
        operator.clear_old_videos(older_than=int(request.POST["older"]))
    return redirect("notifpy:settings")


@require_superuser
def edit_schedule(request):
    """Edit automatic updates schedule"""
    if request.method == "POST":
        schedule = models.UpdateSchedule.objects.get()

        def fun(query):
            return [int(x.strip()) for x in query.split(" ") if x.strip() != ""]
        schedule.text = json.dumps({
            models.YoutubeChannel.PRIORITY_LOW: fun(request.POST["low"]),
            models.YoutubeChannel.PRIORITY_MEDIUM: fun(request.POST["medium"]),
            models.YoutubeChannel.PRIORITY_HIGH: fun(request.POST["high"]),
        })
        schedule.save()
    return redirect("notifpy:settings")


@require_superuser
def update_channels(request):
    """Update all YouTube channel videos"""
    if request.method == "POST":
        operator.Operator().update_channels(
            list(map(int, request.POST["priority"])))
    return redirect("notifpy:home")