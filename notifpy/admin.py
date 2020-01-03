from django.contrib import admin
from . import models

admin.site.register(models.YoutubeVideo)
admin.site.register(models.YoutubeChannel)
admin.site.register(models.Filter)
admin.site.register(models.Playlist)
admin.site.register(models.PlaylistMembership)
admin.site.register(models.TwitchUser)
admin.site.register(models.UpdateSchedule)
