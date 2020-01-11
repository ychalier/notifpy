import re
import sqlite3
from django.core.management.base import BaseCommand
from notifpy import models


class Command(BaseCommand):
    """Merge an external database"""
    help = "Merge an external database"

    def add_arguments(self, parser):
        parser.add_argument(
            "filename",
            type=str,
            help="Path to the external database."
        )

    def handle(self, *args, **kwargs):
        filename = kwargs["filename"]
        connection = sqlite3.connect(filename)
        cursor = connection.cursor()
        youtube_channels = dict()
        print("Loading YouTube channels")
        iterator = list(cursor.execute("SELECT id, title, slug, priority, thumbnail, last_update, playlist_id FROM notifpy_youtubechannel"))
        for i, row in enumerate(iterator):
            channel_id, title, slug, priority, thumbnail, last_update, playlist_id = row
            print("%d/%d: %s" % (i + 1, len(iterator), title))
            if models.YoutubeChannel.objects.filter(id=channel_id).exists():
                youtube_channels[channel_id] = models.YoutubeChannel.objects.get(
                    id=channel_id
                )
            else:
                youtube_channels[channel_id] = models.YoutubeChannel.objects.create(
                    id=channel_id,
                    title=title,
                    slug=slug,
                    priority=priority,
                    thumbnail=thumbnail,
                    last_update=last_update,
                    playlist_id=playlist_id
                )
        print("Loading filters")
        iterator = list(cursor.execute("SELECT id, regex, channel_id FROM notifpy_filter"))
        for i, row in enumerate(iterator):
            _, regex, channel_id = row
            channel = youtube_channels[channel_id]
            regex = re.sub("\r", "", regex)
            print("%d/%d: %s" % (i + 1, len(iterator), regex.encode("utf8")))
            if models.Filter.objects.filter(channel=channel, regex=regex).exists():
                continue
            models.Filter.objects.create(
                channel=channel,
                regex=regex,
            )
        print("Loading Twitch users")
        iterator = list(cursor.execute("SELECT id, login, display_name, profile_image_url, offline_image_url FROM notifpy_twitchuser"))
        for i, row in enumerate(iterator):
            user_id, login, display_name, profile_image_url, offline_image_url = row
            print("%d/%d: %s" % (i + 1, len(iterator), display_name))
            if models.TwitchUser.objects.filter(id=user_id).exists():
                continue
            models.TwitchUser.objects.create(
                id=user_id,
                login=login,
                display_name=display_name,
                profile_image_url=profile_image_url,
                offline_image_url=offline_image_url,
            )
        connection.close()
