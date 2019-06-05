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

    def advanced_list(self, conditions=[], search=[], order=None, limit=None, offset=None):
        sql = "SELECT * FROM videos JOIN channels ON videos.channelId = channels.id"
        if len(conditions) + len(search) > 0:
            sql += " WHERE "
        if len(conditions) > 0:
            sql += " AND ".join(["videos." + c[0]+"=?" for c in conditions])
            if len(search) > 0:
                sql += " AND "
        if len(search) > 0:
            sql += " OR ".join([c[0]+" LIKE ?" for c in search])
        if order is not None:
            sql += " ORDER BY videos.{order}".format(order=order)
        if limit is not None:
            sql += " LIMIT {limit}".format(limit=limit)
        if offset is not None:
            sql += " OFFSET {offset}".format(offset=offset)
        rows = self.db.execute(sql, [c[1] for c in conditions + search])
        return [self.parse(row) for row in rows]

