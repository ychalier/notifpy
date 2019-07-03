from django.shortcuts import render, redirect
from django.http import HttpResponse
from .core.endpoint import Endpoint
import datetime
import json
import re

from . import core

from . import models
from . import forms

def home(request):
    page_size = 48
    page = int(request.GET.get("page", 0))
    order = request.GET.get("order", "publication")
    channels = models.Channel.objects.order_by("title")
    videos = models.Video.objects.order_by("-" + order)[page_size*page:page_size*(page+1)]
    return render(request, "notifpy/home.html", {
        "channels": channels,
        "videos": videos,
        "next": page+1,
        "prev": page-1,
    })

def update(request):
    return HttpResponse("update")

def update_channel(request, slug):
    if not models.Channel.objects.filter(slug=slug).exists():
        return redirect("home")
    channel = models.Channel.objects.get(slug=slug)
    channel.last_update = datetime.datetime.now()
    channel.save()
    endpoint = Endpoint("secret.json")
    for item in endpoint.videos_from_channel(channel.id):
        if "videoId" not in item["id"] or models.Video.objects.filter(id=item["id"]["videoId"]).exists():
            continue
        valid = len(channel.filter_set.all()) == 0
        for filter in channel.filter_set.all():
            if re.search(filter.regex, item["snippet"]["title"]) is not None:
                valid = True
                break
        if valid:
            video = models.Video.objects.create(
                id=item["id"]["videoId"],
                channel=channel,
                title=item["snippet"]["title"],
                publication=item["snippet"]["publishedAt"],
                thumbnail=item["snippet"]["thumbnails"]["medium"]["url"]
            )
            video.save()
    return redirect("channel", slug=channel.slug)

def channel(request, slug):
    if not models.Channel.objects.filter(slug=slug).exists():
        return redirect("home")
    channel = models.Channel.objects.get(slug=slug)
    videos = channel.video_set.order_by("-publication")[:15]
    return render(request, "notifpy/channel.html", {
        "channel": channel,
        "videos": videos,
    })

def create_channel(request):
    if request.method == "POST":
        channel = models.Channel.objects.create(
            id=request.POST["id"],
            title=request.POST["title"],
            thumbnail=request.POST["thumbnail"],
            priority=request.POST["priority"]
        )
        channel.save()
        return redirect("channel", slug=channel.slug)
    else:
        return render(request, "notifpy/create_channel.html", {})

def edit_channel(request, slug):
    if not models.Channel.objects.filter(slug=slug).exists():
        return redirect("home")
    channel = models.Channel.objects.get(slug=slug)
    if request.method == "POST":
        form = forms.ChannelForm(request.POST, instance=channel)
        if form.is_valid():
            channel = form.save()
            return redirect("channel", slug=slug)
    form = forms.ChannelForm(instance=channel)
    return render(request, "notifpy/edit_channel.html", locals())

def delete_channel(request, slug):
    if models.Channel.objects.filter(slug=slug).exists():
        channel = models.Channel.objects.get(slug=slug)
        channel.delete()
    return redirect("home")

def create_filter(request):
    if request.method == "POST":
        channel = models.Channel.objects.get(id=request.POST["channel"])
        for regex in request.POST["regexes"].split("\n"):
            filter = models.Filter.objects.create(
                channel=channel,
                regex=regex
            )
            filter.save()
        return redirect("edit_channel", slug=channel.slug)
    return redirect("home")

def delete_filter(request):
    if request.method == "POST":
        filter = models.Filter.objects.get(id=request.POST["id"])
        slug = filter.channel.slug
        filter.delete()
        return redirect("edit_channel", slug=slug)
    return redirect("home")

def playlist(request, slug):
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("library")
    playlist = models.Playlist.objects.get(slug=slug)
    return render(request, "notifpy/playlist.html", {
        "playlist": playlist
    })

def create_playlist(request):
    if request.method == "POST":
        form = forms.PlaylistForm(request.POST)
        if form.is_valid():
            playlist = form.save()
            return redirect("library")
    form = forms.PlaylistForm()
    return render(request, "notifpy/create_playlist.html", locals())

def edit_playlist(request, slug):
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("library")
    playlist = models.Playlist.objects.get(slug=slug)
    if request.method == "POST":
        form = forms.PlaylistForm(request.POST, instance=playlist)
        if form.is_valid():
            playlist = form.save()
            return redirect("library")
    form = forms.PlaylistForm(instance=playlist)
    return render(request, "notifpy/edit_playlist.html", locals())

def add_playlist(request, slug):
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("library")
    playlist = models.Playlist.objects.get(slug=slug)
    if request.method == "POST":
        link = request.POST["video"]
        video_id = re.search("v?=(.{11})", link)
        if video_id is None:
            video_id = re.search("youtu.be/(.{11})", link)
        if video_id is None:
            video_id = link
        else:
            video_id = video_id.group(1)
        video = None
        if models.Video.objects.filter(id=video_id).exists():
            video = models.Video.objects.get(id=video_id)
        else:
            endpoint = Endpoint("secret.json")
            v_items = endpoint.find_video(video_id)
            if len(v_items) > 0:
                v = v_items[0]
                channel = None
                if models.Channel.objects.filter(id=v["snippet"]["channelId"]).exists():
                    channel = models.Channel.objects.get(id=v["snippet"]["channelId"])
                else:
                    c_items = endpoint.list_channel_id(v["snippet"]["channelId"])
                    if len(c_items) > 0:
                        c = c_items[0]
                        channel = models.Channel.objects.create(
                            id=c["id"],
                            title=c["snippet"]["title"],
                            thumbnail=c["snippet"]["thumbnails"]["medium"]["url"],
                            priority=models.Channel.PRIORITY_NONE,
                        )
                        channel.save()
                if channel is not None:
                    video = models.Video.objects.create(
                        id=v["id"],
                        channel=channel,
                        title=v["snippet"]["title"],
                        publication=v["snippet"]["publishedAt"],
                        thumbnail=v["snippet"]["thumbnails"]["medium"]["url"]
                    )
                    video.save()
        if video is not None:
            playlist.videos.add(video)
            playlist.save()
    return redirect("library")

def remove_playlist(request, slug):
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("library")
    playlist = models.Playlist.objects.get(slug=slug)
    if request.method == "POST":
        video = models.Video.objects.get(id=request.POST["id"])
        playlist.videos.remove(video)
        playlist.save()
    return redirect("edit_playlist", slug=slug)

def delete_playlist(request, slug):
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("library")
    playlist = models.Playlist.objects.get(slug=slug)
    playlist.delete()
    return redirect("library")

def library(request):
    playlists = models.Playlist.objects.all()
    return render(request, "notifpy/library.html", {
        "playlists": playlists,
    })

def api_find_channel(request):
    query = request.body.decode("utf8")
    endpoint = Endpoint("secret.json")
    candidates = endpoint.list_channel_username(query)
    if len(query) == 24:
        candidates += endpoint.list_channel_id(query)
    results = [{
            "id": candidate["id"],
            "title": candidate["snippet"]["title"],
            "thumbnail": candidate["snippet"]["thumbnails"]["medium"]["url"],
        }
        for candidate in candidates
    ]
    return HttpResponse(json.dumps(results), content_type="application/json")
