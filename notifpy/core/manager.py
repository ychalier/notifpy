import datetime
import time
import re

from .. import models
from . import Endpoint


def video_is_valid(channel, title):
    if len(channel.filter_set.all()) == 0:
        return True
    for filter in channel.filter_set.all():
        if re.search(filter.regex, title) is not None:
            return True
    return False


def extract_video_id(string):
    if len(string) == 11:
        return string
    matches = re.search("v?=(.{11})", string)
    if matches is not None:
        return matches.group(1)
    matches = re.search("youtu\.be/(.{11})", string)
    if matches is not None:
        return matches.group(1)


class Manager:

    def __init__(self, secret_file="secret.json"):
        self.endpoint = Endpoint(secret_file)

    def find_channel(self, query):
        channels = self.endpoint.list_channel_username(query)
        if len(query) == 24:
            channels += self.endpoint.list_channel_id(query)
        return [{
                "id": channel["id"],
                "title": channel["snippet"]["title"],
                "thumbnail": channel["snippet"]["thumbnails"]["medium"]["url"],
                }
                for channel in channels
                ]

    def update_channel(self, channel):
        channel.last_update = datetime.datetime.now()
        channel.save()
        videos = list()
        for item in self.endpoint.videos_from_channel(channel.id):
            if "videoId" not in item["id"]:
                continue
            if models.Video.objects.filter(id=item["id"]["videoId"]).exists():
                continue
            if video_is_valid(channel, item["snippet"]["title"]):
                video = models.Video.objects.create(
                    id=item["id"]["videoId"],
                    channel=channel,
                    title=item["snippet"]["title"],
                    publication=item["snippet"]["publishedAt"],
                    thumbnail=item["snippet"]["thumbnails"]["medium"]["url"]
                )
                video.save()
                videos.append(video)
        return videos

    def add_video_to_playlist(self, playlist, query):
        video_id = extract_video_id(query)
        if video_id is None:
            return
        if models.Video.objects.filter(id=video_id).exists():
            return models.Video.objects.get(id=video_id)
        videos = self.endpoint.find_video(video_id)
        if len(videos) == 0:
            return
        channel_id = videos[0]["snippet"]["channelId"]
        if models.Channel.objects.filter(id=channel_id).exists():
            channel = models.Channel.objects.get(id=channel_id)
        else:
            channel_item = self.endpoint.list_channel_id(channel_id)[0]
            channel = models.Channel.objects.create(
                id=channel_item["id"],
                title=channel_item["snippet"]["title"],
                thumbnail=channel_item["snippet"]["thumbnails"]["medium"]["url"],
                priority=models.Channel.PRIORITY_NONE,
            )
            channel.save()
        video = models.Video.objects.create(
            id=videos[0]["id"],
            channel=channel,
            title=videos[0]["snippet"]["title"],
            publication=videos[0]["snippet"]["publishedAt"],
            thumbnail=videos[0]["snippet"]["thumbnails"]["medium"]["url"]
        )
        video.save()
        playlist.videos.add(video)
        playlist.save()
        return video

    def update(self):
        def schedule(t):
            now = datetime.datetime.now()
            if now.weekday() == 5 and now.hour == 0 :
                return models.Channel.PRIORITY_LOW
            if now.hour == 19:
                return models.Channel.PRIORITY_MEDIUM
            if now.hour in [8, 12, 16, 18, 20, 22]:
                return models.Channel.PRIORITY_HIGH
            return None
        priority = schedule(time.time())
        if priority is None:
            return
        for channel in models.Channel.objects.filter(priority=priority):
            self.update_channel(channel)
