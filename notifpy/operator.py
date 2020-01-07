"""This module provides the Operator class"""

import datetime
import json
import re
from django.utils import timezone
from .endpoint import YoutubeEndpoint, TwitchEndpoint
from . import models


def select_thumbnail(snippet):
    """Select the thumbail of a YouTube video"""
    thumbnails = sorted(
        snippet["snippet"]["thumbnails"].values(),
        key=lambda x: -x["width"]
    )
    for thumbnail in thumbnails:
        if thumbnail["width"] / thumbnail["height"] == 16. / 9:
            return thumbnail["url"]
    return ""


def extract_video_id(string):
    """Extract what looks like a YouTube video id from a string"""
    if len(string) == 11:
        return string
    matches = re.search("v?=(.{11})", string)
    if matches is not None:
        return matches.group(1)
    matches = re.search(r"youtu\.be/(.{11})", string)
    if matches is not None:
        return matches.group(1)
    return None


class Operator:
    """Operator that uses API endpoints to edit the database."""

    def __init__(self, credentials_file):
        with open(credentials_file, "r") as file:
            credentials = json.load(file)
        self.youtube = YoutubeEndpoint(credentials)
        self.twitch = TwitchEndpoint(credentials)
        try:
            if not models.UpdateSchedule.objects.all().exists():
                schedule = models.UpdateSchedule.objects.create(text=json.dumps({
                    models.YoutubeChannel.PRIORITY_LOW: [3],
                    models.YoutubeChannel.PRIORITY_MEDIUM: [9, 19],
                    models.YoutubeChannel.PRIORITY_HIGH: [9, 12, 19],
                }))
                schedule.save()
        except:
            pass

    def follow_users(self, query):
        """Follow a set of Twitch users"""
        response = self.twitch.users(
            logins=[s.strip() for s in query.strip().split("\n")]
        )
        if response is None:
            return
        for twitch_user_item in response["data"]:
            if models.TwitchUser.objects.filter(id=twitch_user_item["id"]).exists():
                continue
            twitch_user = models.TwitchUser.objects.create(
                id=twitch_user_item["id"],
                login=twitch_user_item["login"],
                display_name=twitch_user_item["display_name"],
                profile_image_url=twitch_user_item["profile_image_url"],
                offline_image_url=twitch_user_item["offline_image_url"],
            )
            twitch_user.save()

    def get_twitch_game(self, game_id):
        """Return a Twitch game from database or fetch it if necessary"""
        if game_id == "":
            return None
        if models.TwitchGame.objects.filter(id=game_id).exists():
            return models.TwitchGame.objects.get(id=game_id)
        response = self.twitch.games(ids=[game_id])
        if response is None or len(response["data"]) == 0:
            return None
        game_item = response["data"][0]
        game = models.TwitchGame.objects.create(
            id=game_item["id"],
            name=game_item["name"],
            box_art_url=game_item["box_art_url"]
        )
        return game

    def get_streams(self):
        """Get currently live streams"""
        if len(models.TwitchUser.objects.all()) == 0:
            return []
        logins = [user.login for user in models.TwitchUser.objects.all()]
        batch_size = 99
        aggregated = list()
        for i in range(0, len(logins), batch_size):
            batch = logins[i:i+batch_size]
            response = self.twitch.streams(logins=batch)
            if response is None:
                continue
            aggregated += response["data"]
        results = list()
        for stream in aggregated:
            stream["user"] = models.TwitchUser.objects.get(
                id=stream["user_id"])
            stream["thumbnail"] = stream["thumbnail_url"].format(
                width=1600, height=900)
            stream["game"] = self.get_twitch_game(stream["game_id"])
            results.append(stream)
        return results

    def subscribe_to_channels(self, main_query):
        """Subscribe to a set of YouTube channels"""
        queries = [s.strip() for s in main_query.strip().split("\n")]
        url_channel_pattern = re.compile(r"channel\/(.{24})")
        url_username_pattern = re.compile(r"user\/([a-zA-Z0-9-]+)")
        for query in queries:
            channel_id = None
            snippet = None
            if url_username_pattern.search(query) is not None:
                username = url_username_pattern.search(query).group(1)
                response = self.youtube.channels_list(for_username=username)
                if response is None or response["pageInfo"]["totalResults"] == 0:
                    continue
                snippet = response["items"][0]
            elif url_channel_pattern.search(query) is not None:
                channel_id = url_channel_pattern.search(query).group(1)
                response = self.youtube.channels_list(channel_id=channel_id)
                if response is None or response["pageInfo"]["totalResults"] == 0:
                    continue
                snippet = response["items"][0]
            if snippet is not None:
                if models.YoutubeChannel.objects.filter(id=snippet["id"]).exists():
                    continue
                thumbnail = ""
                if "high" in snippet["snippet"]["thumbnails"]:
                    thumbnail = snippet["snippet"]["thumbnails"]["high"]["url"]
                elif "medium" in snippet["snippet"]["thumbnails"]:
                    thumbnail = snippet["snippet"]["thumbnails"]["medium"]["url"]
                else:
                    thumbnail = snippet["snippet"]["thumbnails"]["default"]["url"]
                channel = models.YoutubeChannel.objects.create(
                    id=snippet["id"],
                    title=snippet["snippet"]["title"],
                    thumbnail=thumbnail,
                    priority=models.YoutubeChannel.PRIORITY_MEDIUM,
                    playlist_id=snippet["contentDetails"]["relatedPlaylists"]["uploads"],
                )
                channel.save()

    def update_channel(self, channel):
        """Update videos of a YouTube channel"""
        channel.last_update = timezone.now()
        channel.save()
        response = self.youtube.playlist_items_list(channel.playlist_id)
        if response is None:
            return
        for snippet in response["items"]:
            rsc_id = snippet["snippet"]["resourceId"]
            if rsc_id["kind"] != "youtube#video"\
                    or models.YoutubeVideo.objects.filter(id=rsc_id["videoId"]).exists()\
                    or not channel.video_is_valid(snippet["snippet"]["title"]):
                continue
            video = models.YoutubeVideo.objects.create(
                id=rsc_id["videoId"],
                channel=channel,
                title=snippet["snippet"]["title"],
                publication=snippet["snippet"]["publishedAt"],
                thumbnail=select_thumbnail(snippet)
            )
            video.save()
            for playlist in channel.playlist_set.all():
                if models.PlaylistMembership.objects\
                        .filter(playlist=playlist, video=video).exists():
                    continue
                membership = models.PlaylistMembership.objects.create(
                    playlist=playlist,
                    video=video
                )
                membership.save()

    def update_channels(self, priorities=None, verbose=False):
        """Update all channels from the database"""
        if priorities is None:
            priorities = list()
            now = datetime.datetime.now().hour
            schedule = models.UpdateSchedule.objects.get().to_json()
            for priority, hours in schedule.items():
                if now in hours:
                    priorities.append(int(priority))
        for priority in priorities:
            if verbose:
                print("Updating priority %d" % priority)
            for channel in models.YoutubeChannel.objects.filter(priority=priority):
                print("Updating channel '%s'" % channel)
                self.update_channel(channel)

    def add_video_to_playlist(self, playlist, query):
        """Add a video to a playlist"""
        for line in query.strip().split("\n"):
            video_id = extract_video_id(line.strip())
            if video_id is None:
                return
            if models.YoutubeVideo.objects.filter(id=video_id).exists():
                video = models.YoutubeVideo.objects.get(id=video_id)
            else:
                response = self.youtube.videos_list(video_id)
                if response is None or response["pageInfo"]["totalResults"] == 0:
                    return
                video_item = response["items"][0]
                channel_id = video_item["snippet"]["channelId"]
                if models.YoutubeChannel.objects.filter(id=channel_id).exists():
                    channel = models.YoutubeChannel.objects.get(id=channel_id)
                else:
                    channel_item = self.youtube.channels_list(
                        channel_id=channel_id)["items"][0]
                    channel = models.YoutubeChannel.objects.create(
                        id=channel_item["id"],
                        title=channel_item["snippet"]["title"],
                        thumbnail=channel_item["snippet"]["thumbnails"]["medium"]["url"],
                        priority=models.YoutubeChannel.PRIORITY_NONE,
                    )
                    channel.save()
                video = models.YoutubeVideo.objects.create(
                    id=video_item["id"],
                    channel=channel,
                    title=video_item["snippet"]["title"],
                    publication=video_item["snippet"]["publishedAt"],
                    thumbnail=select_thumbnail(video_item),
                )
                video.save()
            playlist_membership = models.PlaylistMembership.objects.create(
                playlist=playlist,
                video=video,
            )
            playlist_membership.save()


def clear_old_videos(older_than=2592000):
    """Remove old videos from the database"""
    now = timezone.now()
    for video in models.YoutubeVideo.objects.filter(playlistmembership=None):
        if (now - video.gathering).total_seconds() > older_than:
            video.delete()
