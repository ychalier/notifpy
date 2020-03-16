"""This module contains all views from the application"""

import re
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.urls import reverse
from django.http import HttpResponse
from visitors.monitor_visitors import monitor_visitors
from . import operator
from . import models
from . import forms


def inform(request, title=None, input_msg=None, output_msg=None, next_page=None):
    if next_page is not None:
        next_page = reverse(next_page)
    return render(request, "notifpy/inform.html", {
        "title": title,
        "input": input_msg,
        "output": output_msg,
        "next": next_page,
    })


@monitor_visitors
def abstract(request):
    """View with abstract of the application"""
    return render(request, "notifpy/abstract.html", {})


@login_required
def home(request):
    """Main view to display last updates."""
    page_size = 16
    page = int(request.GET.get("page", 1))
    order = request.GET.get("order", "publication")
    video_list = models.YoutubeVideo.objects\
        .exclude(channel__priority=models.YoutubeChannel.PRIORITY_NONE)\
        .order_by("-" + order)
    paginator = Paginator(video_list, page_size)
    videos = paginator.get_page(page)
    return render(request, "notifpy/home.html", {
        "videos": videos,
    })


def twitch_streams_api(_):
    """View that simply returns a JSON from Twitch endpoint"""
    body = list()
    twitch_users = models.TwitchUser.objects.all()
    streams = operator.Operator().get_streams()
    if streams is not None:
        for stream in streams:
            user = twitch_users.get(id=stream["user_id"])
            body.append({
                "lnk": user.link(),
                "thumb": user.thumbnail(),
                "name": stream["user_name"],
                "game": stream["game"].name,
                "title": stream["title"],
                "screen": stream["thumbnail"],
            })
    return HttpResponse(json.dumps(body), content_type="application/json")


def oauth_redirect(request, source):
    """Redirection handling during OAuth flow"""
    opr = operator.Operator()
    if source == "youtube" and opr.youtube is not None:
        opr.youtube.oauth_flow.handle_redirect(request)
    elif source == "twitch" and opr.twitch is not None:
        opr.twitch.oauth_flow.handle_redirect(request)
    return redirect("notifpy:settings")


@login_required
def refresh_token(_, source):
    """Request an endpoint token to be refreshed"""
    opr = operator.Operator()
    if source == "youtube" and opr.youtube is not None:
        opr.youtube.oauth_flow.refresh()
    elif source == "twitch" and opr.twitch is not None:
        opr.twitch.oauth_flow.refresh()
    return redirect("notifpy:settings")


@login_required
def revoke_token(_, source):
    """Request an endpoint token to be revoked"""
    opr = operator.Operator()
    if source == "youtube" and opr.youtube is not None:
        opr.youtube.oauth_flow.revoke()
    elif source == "twitch" and opr.twitch is not None:
        opr.twitch.oauth_flow.revoke()
    return redirect("notifpy:settings")


@login_required
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


@login_required
def clear_old_videos(request):
    """Remove old videos from database"""
    if request.method == "POST":
        operator.clear_old_videos(older_than=int(request.POST["older"]))
    return redirect("notifpy:settings")


@login_required
def create_channel(request):
    """Subscribe to a YouTube channel"""
    if request.method == "POST" and "query" in request.POST:
        result = operator.Operator().subscribe_to_channels(request.POST["query"])
        return inform(
            request,
            "create YouTube channel",
            request.POST["query"],
            result,
            "notifpy:home"
        )
    return redirect("notifpy:home")


@login_required
def view_channel(request, slug):
    """View all information about a YouTube channel"""
    if not models.YoutubeChannel.objects.filter(slug=slug).exists():
        return redirect("notifpy:home")
    channel = models.YoutubeChannel.objects.get(slug=slug)
    videos = channel.youtubevideo_set.order_by("-publication")[:15]
    return render(request, "notifpy/channel.html", {
        "channel": channel,
        "videos": videos,
    })


@login_required
def edit_channel(request, slug):
    """Edit a YouTube channel information"""
    if not models.YoutubeChannel.objects.filter(slug=slug).exists():
        return redirect("notifpy:home")
    channel = models.YoutubeChannel.objects.get(slug=slug)
    if request.method == "POST":
        if "thumbnail" in request.POST:
            channel.thumbnail = request.POST["thumbnail"]
        if "priority" in request.POST:
            channel.priority = request.POST["priority"]
        channel.save()
    return redirect("notifpy:channel", slug=slug)


@login_required
def delete_channel(_, slug):
    """Unsubscribe from a channel"""
    if models.YoutubeChannel.objects.filter(slug=slug).exists():
        channel = models.YoutubeChannel.objects.get(slug=slug)
        channel.delete()
    return redirect("notifpy:home")


@login_required
def create_filter(request):
    """Append a filter to a channel"""
    if request.method == "POST":
        channel = models.YoutubeChannel.objects.get(id=request.POST["channel"])
        for regex in request.POST["regexes"].split("\n"):
            filters = models.Filter.objects.create(
                channel=channel,
                regex=re.sub("\r", "", regex)
            )
            filters.save()
        return redirect("notifpy:channel", slug=channel.slug)
    return redirect("notifpy:home")


@login_required
def delete_filter(request):
    """Delete a filter from a channel"""
    if request.method == "POST":
        filters = models.Filter.objects.get(id=request.POST["id"])
        slug = filters.channel.slug
        filters.delete()
        return redirect("notifpy:channel", slug=slug)
    return redirect("notifpy:home")


@login_required
def update_channel(_, slug):
    """Update a YouTube channel videos"""
    if not models.YoutubeChannel.objects.filter(slug=slug).exists():
        return redirect("notifpy:home")
    channel = models.YoutubeChannel.objects.get(slug=slug)
    operator.Operator().update_channel(channel)
    return redirect("notifpy:channel", slug=channel.slug)


@login_required
def update_channels(request):
    """Update all YouTube channel videos"""
    if request.method == "POST":
        operator.Operator().update_channels(list(map(int, request.POST["priority"])))
    return redirect("notifpy:home")


@login_required
def create_playlist(request):
    """Add a new playlist object"""
    if request.method == "POST":
        form = forms.PlaylistForm(request.POST)
        if form.is_valid():
            playlist = form.save()
            return redirect("notifpy:playlist", slug=playlist.slug)
    form = forms.PlaylistForm()
    return render(request, "notifpy/create_playlist.html", locals())


@login_required
def view_playlist(request, slug):
    """View a playlist"""
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("notifpy:playlists")
    playlist = models.Playlist.objects.get(slug=slug)
    return render(request, "notifpy/playlist.html", {
        "playlist": playlist,
    })


@login_required
def edit_playlist(request, slug):
    """Edit playlist properties"""
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("notifpy:playlists")
    playlist = models.Playlist.objects.get(slug=slug)
    if request.method == "POST":
        title = request.POST["title"]
        playlist.title = title
        playlist.save()
    return redirect("notifpy:playlist", slug=playlist.slug)


@login_required
def add_playlist(request, slug):
    """Add a video (or more) to a playlist"""
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("notifpy:playlists")
    playlist = models.Playlist.objects.get(slug=slug)
    if request.method == "POST":
        operator.Operator().add_video_to_playlist(playlist, request.POST.get("video", ""))
    return redirect("notifpy:playlist", slug=playlist.slug)


@login_required
def remove_playlist(request, slug):
    """Remove a video from a playlist"""
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("notifpy:playlists")
    playlist = models.Playlist.objects.get(slug=slug)
    if request.method == "POST":
        video = models.YoutubeVideo.objects.get(id=request.POST["id"])
        playlist.videos.remove(video)
        playlist.save()
        playlist.shift_orders()
    return redirect("notifpy:playlist", slug=playlist.slug)


@login_required
def delete_playlist(_, slug):
    """Delete a playlist"""
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("notifpy:playlists")
    playlist = models.Playlist.objects.get(slug=slug)
    playlist.delete()
    return redirect("notifpy:playlists")


@login_required
def move_playlist(_, slug, order, direction):
    """Edit the video odering within a playlist"""
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("notifpy:playlists")
    playlist = models.Playlist.objects.get(slug=slug)
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


@login_required
def view_playlists(request):
    """View playlists"""
    playlists = models.Playlist.objects.all()
    return render(request, "notifpy/playlists.html", {
        "playlists": playlists,
    })


@login_required
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


@login_required
def create_twitch_user(request):
    """Follow a Twitch user"""
    if request.method == "POST" and "query" in request.POST:
        result = operator.Operator().follow_users(request.POST["query"])
        return inform(
            request,
            "create Twitch user",
            request.POST["query"],
            result,
            "notifpy:home"
        )
    return redirect("notifpy:home")


@login_required
def delete_twitch_user(_, login):
    """Unfollow a Twitch user"""
    if models.TwitchUser.objects.filter(login=login).exists():
        user = models.TwitchUser.objects.get(login=login)
        user.delete()
    return redirect("notifpy:home")
