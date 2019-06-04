from .model import Model


class Channel(Model):

    fields = [
        "id",
        "title",
        "description",
        "priority"
    ]

    table = "channels"

    def wrap(json, priority):
        return [
            json["id"],
            json["snippet"]["title"],
            json["snippet"]["description"],
            priority
        ]
