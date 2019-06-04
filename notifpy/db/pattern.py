from .model import Model


class Pattern(Model):

    fields = [
        "id",
        "channelId",
        "regex"
    ]

    table = "patterns"
