from .model import Model
import datetime


class Video(Model):

    fields = [
        "id",
        "channelId",
        "title",
        "publishedAt",
        "description",
        "thumbnail",
        "creation"
    ]

    table = "videos"

    def wrap(json):
        return [
            json["id"]["videoId"],
            json["snippet"]["channelId"],
            json["snippet"]["title"],
            json["snippet"]["publishedAt"],
            json["snippet"]["description"],
            json["snippet"]["thumbnails"]["medium"]["url"],
            datetime.datetime.now().isoformat() + "Z"
        ]
