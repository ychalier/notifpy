from django.contrib import admin
from . import models

admin.site.register(models.Video)
admin.site.register(models.Channel)
admin.site.register(models.Filter)
admin.site.register(models.Playlist)
admin.site.register(models.PlaylistMembership)
