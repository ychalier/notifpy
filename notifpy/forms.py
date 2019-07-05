from django import forms
from . import models


class ChannelForm(forms.ModelForm):

    class Meta:
        model = models.Channel
        fields = ["thumbnail", "priority"]


class FilterForm(forms.ModelForm):

    class Meta:
        model = models.Filter
        fields = ["channel", "regex"]


class VideoForm(forms.ModelForm):

    class Meta:
        model = models.Video
        fields = ["id", "channel", "title", "publication", "thumbnail"]


class PlaylistForm(forms.ModelForm):

    class Meta:
        model = models.Playlist
        fields = ["title", "rules"]
