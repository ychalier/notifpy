import datetime

from .. import models
from . import Endpoint

class Manager:

    def __init__(self, secret_file="secret.json"):
        self.endpoint = Endpoint(secret_file)

    def update_channel(self, channel):
        channel.last_update = datetime.datetime.now()
        channel.save()
        for item in self.endpoint.videos_from_channel(channel.id):
            if "videoId" not in item["id"]:
                continue
            video_id = item["id"]["videoId"]
            if models.Video.objects.filter(id=video_id).exists():
                continue
            valid = len(channel.filter_set.all()) == 0
            for filter in channel.filter_set.all():
                if re.search(filter.regex, item["snippet"]["title"]) is not None:
                    valid = True
                    break
            if valid:
                video = models.Video.objects.create(
                    id=video_id,
                    channel=channel,
                    title=item["snippet"]["title"],
                    publication=item["snippet"]["publishedAt"],
                    thumbnail=item["snippet"]["thumbnails"]["medium"]["url"]
                )
                video.save()
        return redirect("channel", slug=channel.slug)

    def add_video_to_playlist(self, playlist, video_id):
        pass

    def remove_video_from_playlist(self, playlist, video_id):
        pass
