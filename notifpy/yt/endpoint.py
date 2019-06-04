import requests
from .api import Api


class Endpoint(Api):

    PLAYLIST_URI = "https://www.googleapis.com/youtube/v3/playlists"
    PLAYLIST_ITEMS_URI = "https://www.googleapis.com/youtube/v3/playlistItems"
    CHANNELS_URI = "https://www.googleapis.com/youtube/v3/channels"
    SEARCH_URI = "https://www.googleapis.com/youtube/v3/search"

    def headers(self):
        return {
            "Authorization": "Bearer " + self.refresh_token["access_token"]
        }

    def get(self, url, params, retry=False):
        response = requests.get(url, params=params, headers=self.headers())
        if response.status_code == 401 and not retry:
            self.refresh()
            return self.get(url, params, retry=True)
        return response.json()

    def list_channel_username(self, username):
        return self.get(Endpoint.CHANNELS_URI, {
            "part": "snippet",
            "maxResults": 50,
            "forUsername": username
        })["items"]

    def list_channel_id(self, channel_id):
        return self.get(Endpoint.CHANNELS_URI, {
            "part": "snippet",
            "maxResults": 50,
            "id": channel_id
        })["items"]

    def videos_from_channel(self, channel_id):
        return self.get( Endpoint.SEARCH_URI, {
            "part": "snippet",
            "maxResults": 50,
            "order": "date",
            "channelId": channel_id
        })["items"]
