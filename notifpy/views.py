from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.encoding import smart_str
from django.http import HttpResponse
import datetime
import json
import time
import re

from . import core
from . import models
from . import forms

manager = core.Manager("secret.json")


@login_required
def home(request):
    page_size = 48
    page = int(request.GET.get("page", 0))
    order = request.GET.get("order", "publication")
    channels = models.Channel.objects\
        .exclude(priority=models.Channel.PRIORITY_NONE)\
        .order_by("title")
    videos = models.Video.objects\
        .exclude(channel__priority=models.Channel.PRIORITY_NONE)\
        .order_by("-" + order)[page_size * page:page_size * (page + 1)]
    return render(request, "notifpy/home.html", {
        "channels": channels,
        "videos": videos,
        "next": page + 1,
        "prev": page - 1,
    })


@login_required
def update(request):
    manager.update()
    return redirect("home")


@login_required
def update_channel(request, slug):
    if not models.Channel.objects.filter(slug=slug).exists():
        return redirect("home")
    channel = models.Channel.objects.get(slug=slug)
    manager.update_channel(channel)
    return redirect("channel", slug=channel.slug)


@login_required
def channel(request, slug):
    if not models.Channel.objects.filter(slug=slug).exists():
        return redirect("home")
    channel = models.Channel.objects.get(slug=slug)
    videos = channel.video_set.order_by("-publication")[:15]
    return render(request, "notifpy/channel.html", {
        "channel": channel,
        "videos": videos,
    })


@login_required
def create_channel(request):
    if request.method == "POST":
        if models.Channel.objects.filter(id=request.POST["id"]).exists():
            return redirect("channel", slug=models.Channel.objects.get(id=request.POST["id"]).slug)
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


@login_required
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


@login_required
def delete_channel(request, slug):
    if models.Channel.objects.filter(slug=slug).exists():
        channel = models.Channel.objects.get(slug=slug)
        channel.delete()
    return redirect("home")


@login_required
def find_channel(request):
    return HttpResponse(
        json.dumps(manager.find_channel(request.body.decode("utf8"))),
        content_type="application/json"
    )


@login_required
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


@login_required
def delete_filter(request):
    if request.method == "POST":
        filter = models.Filter.objects.get(id=request.POST["id"])
        slug = filter.channel.slug
        filter.delete()
        return redirect("edit_channel", slug=slug)
    return redirect("home")


@login_required
def playlist(request, slug):
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("library")
    playlist = models.Playlist.objects.get(slug=slug)
    return render(request, "notifpy/playlist.html", {
        "playlist": playlist
    })


@login_required
def create_playlist(request):
    if request.method == "POST":
        form = forms.PlaylistForm(request.POST)
        if form.is_valid():
            playlist = form.save()
            return redirect("library")
    form = forms.PlaylistForm()
    return render(request, "notifpy/create_playlist.html", locals())


@login_required
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


@login_required
def add_playlist(request, slug):
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("library")
    playlist = models.Playlist.objects.get(slug=slug)
    if request.method == "POST":
        manager.add_video_to_playlist(playlist, request.POST.get("video", ""))
    return redirect("library")


@login_required
def remove_playlist(request, slug):
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("library")
    playlist = models.Playlist.objects.get(slug=slug)
    if request.method == "POST":
        video = models.Video.objects.get(id=request.POST["id"])
        playlist.videos.remove(video)
        playlist.save()
    return redirect("edit_playlist", slug=slug)


@login_required
def delete_playlist(request, slug):
    if not models.Playlist.objects.filter(slug=slug).exists():
        return redirect("library")
    playlist = models.Playlist.objects.get(slug=slug)
    playlist.delete()
    return redirect("library")


@login_required
def library(request):
    playlists = models.Playlist.objects.all()
    return render(request, "notifpy/library.html", {
        "playlists": playlists,
    })


def abstract(request):
    return render(request, "notifpy/abstract.html", {})


@login_required
def quotas(request):
    with open(core.Endpoint.LOG_PATH) as file:
        lines = file.readlines()[1:]
    now = time.time()
    data = [{
        "timestamp": float(t),
        "url": url.replace("https://www.googleapis.com/youtube/v3/", ""),
        "params": json.loads(params),
        "cost": int(cost),
        "date": datetime.datetime.fromtimestamp(float(t))
    }
        for t, url, params, cost in map(lambda s: s.strip().split("\t"), lines)
    ]
    daily = sum([
        row["cost"]
        for row in data
        if row["timestamp"] > now - 24 * 3600
    ])
    return render(request, "notifpy/quotas.html", {
        "daily": daily,
        "data": data,
    })


@login_required
def reset_quotas(request):
    with open("log.tsv", "w") as file:
        file.write("timestamp\turl\tparameters\tcost\n")
    return redirect("quotas")


@login_required
def download_quotas(request):
    with open("log.tsv") as file:
        text = file.read()
    response = HttpResponse(text, content_type="application/force-download")
    response["Content-Disposition"] = "attachment; filename=%s" % smart_str(
        "log.tsv")
    response["X-Sendfile"] = smart_str("log.tsv")
    return response
