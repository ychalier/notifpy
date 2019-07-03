from django.utils.text import slugify
from django.db import models
import random

class Video(models.Model):

    id = models.CharField(max_length=11, primary_key=True)
    channel = models.ForeignKey("Channel", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    publication = models.DateTimeField(auto_now_add=False, auto_now=False)
    gathering = models.DateTimeField(auto_now_add=True, auto_now=False)
    thumbnail = models.URLField()

    def __str__(self):
        return "[{id}] {title}".format(id=self.id, title=self.title)

    def time(self):
        return self.publication.strftime("%d %b. %H:%M")

class Channel(models.Model):

    PRIORITY_NONE = -1
    PRIORITY_LOW = 0
    PRIORITY_MEDIUM = 1
    PRIORITY_HIGH = 2

    PRIORITY_CHOICES = [
        (PRIORITY_NONE, "None"),
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High")
    ]

    # TODO: Add last_update field
    id = models.CharField(max_length=24, primary_key=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM
    )
    thumbnail = models.URLField()
    last_update = models.DateTimeField(auto_now_add=False, auto_now=False, blank=True, null=True)

    def __str__(self):
        return self.title

    def priority_label(self):
        return {
            Channel.PRIORITY_NONE: "None",
            Channel.PRIORITY_LOW: "Low",
            Channel.PRIORITY_MEDIUM: "Medium",
            Channel.PRIORITY_HIGH: "High"
        }[self.priority]

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        models.Model.save(self, *args, **kwargs)

class Filter(models.Model):

    channel = models.ForeignKey("Channel", on_delete=models.CASCADE)
    regex = models.CharField(max_length=255, default=".*")

class Playlist(models.Model):

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    videos = models.ManyToManyField(
        "Video",
        blank=True,
        through="PlaylistMembership"
    )
    rules = models.ManyToManyField("Channel", blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        models.Model.save(self, *args, **kwargs)

    def url_ranked(self):
        ids = [video.id for video in self.videos.order_by("-publication")[:50]]
        return "https://www.youtube.com/watch_videos?video_ids=" + ",".join(ids)

    def url_shuffled(self):
        ids = [video.id for video in self.videos.all()[:50]]
        random.shuffle(ids)
        return "https://www.youtube.com/watch_videos?video_ids=" + ",".join(ids)

class PlaylistMembership(models.Model):

    playlist = models.ForeignKey("Playlist", on_delete=models.CASCADE)
    video = models.ForeignKey("Video", on_delete=models.CASCADE)
    addition = models.DateTimeField(auto_now_add=True, auto_now=False)
    order = models.IntegerField(default=0)
