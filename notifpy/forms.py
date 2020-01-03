from django import forms
from . import models


class YoutubeChannelForm(forms.ModelForm):

    class Meta:
        model = models.YoutubeChannel
        fields = ["thumbnail", "priority"]


class FilterForm(forms.ModelForm):

    class Meta:
        model = models.Filter
        fields = ["channel", "regex"]


class YoutubeVideoForm(forms.ModelForm):

    class Meta:
        model = models.YoutubeVideo
        fields = ["id", "channel", "title", "publication", "thumbnail"]


class PlaylistForm(forms.ModelForm):

    class Meta:
        model = models.Playlist
        fields = ["title", "rules"]
