"""Data models for Notifpy"""

import random
import json
import re
from django.utils.text import slugify
from django.db import models
from django.contrib.auth.models import User


class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        """Return singleton and creates it if needed"""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Settings(SingletonModel):

    youtube = models.TextField(default="{}")
    twitch = models.TextField(default="{}")

    def get_youtube(self):
        return json.loads(self.youtube)

    def get_twitch(self):
        return json.loads(self.twitch)


class Token(SingletonModel):

    youtube = models.TextField(default="{}")
    twitch = models.TextField(default="{}")

    def get_youtube(self):
        return json.loads(self.youtube)

    def get_twitch(self):
        return json.loads(self.twitch)


class YoutubeVideo(models.Model):

    """Represent a YouTube video"""

    id = models.CharField(max_length=11, primary_key=True)
    channel = models.ForeignKey("YoutubeChannel", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    publication = models.DateTimeField(auto_now_add=False, auto_now=False)
    gathering = models.DateTimeField(auto_now_add=True, auto_now=False)
    thumbnail = models.URLField()

    def __str__(self):
        return "[{id}] {title}".format(id=self.id, title=self.title)

    def time(self):
        """Return the publication time in a readable format"""
        return self.publication.strftime("%d %b. %H:%M")


class YoutubeChannel(models.Model):

    """Represent a YouTube channel"""

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

    id = models.CharField(max_length=24, primary_key=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM
    )
    thumbnail = models.URLField()
    last_update = models.DateTimeField(
        auto_now_add=False, auto_now=False, blank=True, null=True)
    playlist_id = models.CharField(max_length=255)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        models.Model.save(self, *args, **kwargs)

    def priority_label(self):
        """Return the label of the priority level of the channel"""
        return {
            YoutubeChannel.PRIORITY_NONE: "None",
            YoutubeChannel.PRIORITY_LOW: "Low",
            YoutubeChannel.PRIORITY_MEDIUM: "Medium",
            YoutubeChannel.PRIORITY_HIGH: "High"
        }[self.priority]

    def video_is_valid(self, title):
        """Check if a video is valid regarding filters"""
        if len(self.filter_set.all()) == 0:
            return True
        for filters in self.filter_set.all():
            if re.search(filters.regex, title) is not None:
                return True
        return False


class Filter(models.Model):

    """Represent a regex filter for the videos of a channel"""

    channel = models.ForeignKey("YoutubeChannel", on_delete=models.CASCADE)
    regex = models.CharField(max_length=255, default=".*")

    def __str__(self):
        return "Filter<Channel: %s; Regex: %s>" % (
            self.channel,
            self.regex.encode("utf8")
        )


class Playlist(models.Model):

    """Represent an ordered list of videos"""

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    videos = models.ManyToManyField(
        "YoutubeVideo",
        blank=True,
        through="PlaylistMembership"
    )
    rules = models.ManyToManyField("YoutubeChannel", blank=True)
    public = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.owner.username + " " + self.title)
        models.Model.save(self, *args, **kwargs)

    def get_videos(self):
        """Return all memberships of the playlist, ranked"""
        return self.playlistmembership_set.all().order_by("order")

    def shift_orders(self):
        """Reset ordering so the first item is at 0 and increment is always 1"""
        for i, membership in enumerate(self.get_videos()):
            membership.order = i
            membership.save()

    def url_ranked(self):
        """Return a url with the first 50 videos in the playlist"""
        ids = [entry.video.id for entry in self.get_videos()[:50]]
        return "https://www.youtube.com/watch_videos?video_ids=" + ",".join(ids)

    def url_shuffled(self):
        """Return a url with the first 50 videos in the playlist, shuffled"""
        ids = [entry.video.id for entry in self.get_videos()]
        random.shuffle(ids)
        return "https://www.youtube.com/watch_videos?video_ids=" + ",".join(ids[:50])

    def size(self):
        return self.videos.count()


class PlaylistMembership(models.Model):

    """Represent membership of a video to a playlist"""

    playlist = models.ForeignKey("Playlist", on_delete=models.CASCADE)
    video = models.ForeignKey("YoutubeVideo", on_delete=models.CASCADE)
    addition = models.DateTimeField(auto_now_add=True, auto_now=False)
    order = models.IntegerField(default=-1)

    def __str__(self):
        return "PlaylistMembership<'%s' to '%s' (rk. %d)>" % (
            self.video,
            self.playlist,
            self.order
        )

    def save(self, *args, **kwargs):
        if self.order == -1:
            self.order = len(self.playlist.videos.all())
        models.Model.save(self, *args, **kwargs)


class TwitchUser(models.Model):

    """Represent a Twitch user"""

    id = models.CharField(max_length=24, primary_key=True)
    login = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    profile_image_url = models.URLField()
    offline_image_url = models.URLField()

    def __str__(self):
        return "TwitchUser<%s (%s)>" % (self.display_name, self.id)

    def link(self):
        """Return the link to the Twitch channel of this user"""
        return "https://www.twitch.tv/%s" % self.login

    def thumbnail(self):
        return self.profile_image_url.replace("300x300", "50x50")


class UpdateSchedule(models.Model):

    """Store the update schedule as JSON format"""

    text = models.TextField()

    def to_json(self):
        """Return a JSON object from stored text"""
        return json.loads(self.text)


class TwitchGame(models.Model):

    id = models.CharField(max_length=24, primary_key=True)
    name = models.CharField(max_length=255)
    box_art_url = models.URLField()

    def __str__(self):
        return "%s (%s)" % (self.name, self.id)

    def thumbnail(self):
        return self.box_art_url.format(width=144, height=192)


class YoutubeSubscription(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(YoutubeChannel, on_delete=models.CASCADE)


class TwitchSubscription(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(TwitchUser, on_delete=models.CASCADE)
