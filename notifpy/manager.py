from notifpy.templates import Renderer
from notifpy.db import Channel, Pattern, Video
import datetime
import sys
import re


class Manager:

    def __init__(self, db, endpoint):
        self.db = db
        self.endpoint = endpoint

    def clean_database(self):
        self.db.clean()

    def create_channel(self, args):
        candidates = self.endpoint.list_channel_username(args[0])
        if len(args[0]) == 24:
            candidates += self.endpoint.list_channel_id(args[0])
        for channel in candidates:
            instance = Channel.wrap(channel, args[1])
            if Channel(self.db).exists(instance[0]):
                print("Found existing channel:", instance[0], instance[1])
                continue
            if input("Is '{title}' correct (y/n)? ".format(title=instance[1])) == "y":
                Channel(self.db).create(*instance)
                return
        print("Channel not found")

    def delete_channel(self, args):
        model = Channel(self.db)
        if model.exists(args[0]):
            model.delete(args[0])
        else:
            print("Channel not found")

    def create_pattern(self, args):
        channel_id, *pattern = args
        model = Pattern(self.db)
        model.create(None, channel_id, " ".join(pattern))

    def delete_pattern(self, args):
        model = Pattern(self.db)
        if model.exists(args[0]):
            model.delete(args[0])
        else:
            print("Pattern not found")

    def list(self):
        model_channel = Channel(self.db)
        model_pattern = Pattern(self.db)
        channels = model_channel.list()
        patterns = {channel["id"]: [] for channel in channels}
        for pattern in model_pattern.list():
            if pattern["channelId"] in patterns:
                patterns[pattern["channelId"]].append(pattern)
        first = True
        for channel in channels:
            if first:
                first = False
            else:
                print("")
            print("{id}\t{title}".format(
                id=channel["id"],
                title=channel["title"])
            )
            for pattern in patterns[channel["id"]]:
                print("\t{id}\t'{regex}'".format(
                    id=pattern["id"],
                    regex=pattern["regex"])
                )
            if len(patterns[channel["id"]]) == 0:
                print("\tNo patterns for this channel.")

    def html_channels(self, args):
        parameters = {
            "limit": 10,
            "order": "publishedAt DESC",
        }
        for arg in args:
            key, value = arg.split("=")
            if key in ["offset", "limit"]:
                value = int(value)
            parameters[key] = value
        channel_model = Channel(self.db)
        video_model = Video(self.db)
        renderer = Renderer("channels.html")
        channels = channel_model.list(order="title")
        for channel in channels:
            videos = video_model.list(
                conditions=[("channelId", channel["id"])],
                order=parameters["order"],
                limit=parameters["limit"]
            )
            for video in videos:
                video["time"] = datetime.datetime.strptime(
                                    video["publishedAt"],
                                    "%Y-%m-%dT%H:%M:%S.%fZ"
                                ).strftime("%d %b. %H:%M")
            channel["videos"] = videos
            channel["ids"] = ",".join([v["id"] for v in videos])
        return renderer.render({"channels": channels})

    def html_videos(self, args, template="videos.html"):
        parameters = {
            "offset": 0,
            "limit": 50,
            "order": "publishedAt DESC",
            "channel": None,
            "query": None
        }
        for arg in args:
            key, value = arg.split("=")
            if key in ["offset", "limit"]:
                value = int(value)
            elif key in ["channel", "query"] and value == "None":
                value = None
            parameters[key] = value
        channel_model = Channel(self.db)
        video_model = Video(self.db)
        renderer = Renderer(template)
        conditions = []
        if parameters["channel"] is not None:
            conditions.append(("channelId", parameters["channel"]))
        search = []
        if parameters["query"] is not None:
            search.append(("videos.title", "%{query}%".format(query=parameters["query"])))
            search.append(("channels.title", "%{query}%".format(query=parameters["query"])))
        videos = video_model.advanced_list(
            conditions=conditions,
            search=search,
            order=parameters["order"],
            limit=parameters["limit"],
            offset=parameters["offset"]
        )
        for video in videos:
            video["channel"] = channel_model.list(
                conditions=[("id", video["channelId"])]
            )[0]["title"]
            video["time"] = datetime.datetime.strptime(
                video["publishedAt"],
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ).strftime("%d %b. %H:%M")
        return renderer.render({"videos": videos})

    def html_body(self, args):
        return self.html_videos(args, "body.html")

    def html(self, mode, args=[]):
        if mode == "channels":
            html = self.html_channels(args)
        elif mode == "videos":
            html = self.html_videos(args)
        elif mode == "body":
            html = self.html_body(args)
        else:
            html = "<h1>404 Not Found</h1>"
        sys.stdout.buffer.write(html.encode("utf8"))

    def update_channel(self, channel):
        pattern_model = Pattern(self.db)
        video_model = Video(self.db)
        patterns = pattern_model.list([("channelId", channel["id"])])
        for video in self.endpoint.videos_from_channel(channel["id"]):
            if "videoId" not in video["id"]:
                continue
            instance = Video.wrap(video)
            valid = len(patterns) == 0
            for pattern in patterns:
                if re.search(pattern["regex"], instance[2]) is not None:
                    valid = True
                    break
            if valid and not video_model.exists(instance[0]):
                video_model.create(*instance)
                print("{channel}\t{id}\t{title}".format(
                    id=instance[0],
                    title=instance[2],
                    channel=channel["id"])
                )

    def update(self, priority=None):
        channel_model = Channel(self.db)
        conditions = []
        if priority is not None:
            conditions = [("priority", priority)]
        for channel in channel_model.list(conditions=conditions):
            self.update_channel(channel)

    def scheduling(self):
        now = datetime.datetime.now()
        if now.weekday() == 5 and now.hour == 0 :
            return 0
        if now.hour == 19:
            return 1
        if now.hour in [8, 12, 16, 18, 20, 22]:
            return 2
        return -1

    def process(self, args):
        if len(args) == 0:
            return False
        elif args[0] == "clean":
            self.clean_database()
            return True
        elif args[0] == "update":
            if len(args) > 1:
                if args[1] == "schedule":
                    priority = self.scheduling()
                    if priority >= 0:
                        self.update(priority)
                    return True
                elif args[1] == "priority":
                    if len(args) != 3:
                        return False
                    self.update(int(args[2]))
                    return True
                elif args[1] == "channel":
                    if len(args) != 3:
                        return False
                    if Channel(self.db).exists(args[2]):
                        self.update_channel(Channel(self.db).list(conditions=[("id", args[2])])[0])
                    else:
                        print("Channel not found.")
                    return True
                return False
            self.update()
            return True
        elif args[0] == "list":
            self.list()
            return True
        elif args[0] == "html":
            if len(args) < 2:
                return False
            self.html(args[1], args[2:])
            return True
        elif args[0] == "create":
            if len(args) != 4:
                return False
            if args[1] == "channel":
                self.create_channel(args[2:])
                return True
            elif args[1] == "pattern":
                self.create_pattern(args[2:])
                return True
        elif args[0] == "delete":
            if len(args) != 3:
                return False
            if args[1] == "channel":
                self.delete_channel(args[2:])
                return True
            elif args[1] == "pattern":
                self.delete_pattern(args[2:])
                return True
        return False
