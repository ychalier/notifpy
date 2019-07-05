import requests
import json
import time
import os


class Endpoint:

    TOKEN_URI = "https://www.googleapis.com/oauth2/v4/token"
    AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
    TOKEN_FILE = "token.json"
    PLAYLIST_URI = "https://www.googleapis.com/youtube/v3/playlists"
    PLAYLIST_ITEMS_URI = "https://www.googleapis.com/youtube/v3/playlistItems"
    CHANNELS_URI = "https://www.googleapis.com/youtube/v3/channels"
    SEARCH_URI = "https://www.googleapis.com/youtube/v3/search"
    VIDEO_URI = "https://www.googleapis.com/youtube/v3/videos"
    LOG_PATH = "log.tsv"

    def __init__(self, secret_file):
        self.secret = dict()
        with open(secret_file) as file:
            self.secret = json.load(file)["app"]
        self.auth_token = None
        self.retrieve_token()

    def log(self, url, params, cost):
        with open(Endpoint.LOG_PATH, "a") as file:
            file.write("{timestamp}\t{url}\t{params}\t{cost}\n".format(
                timestamp=time.time(),
                url=url,
                params=json.dumps(params),
                cost=cost,
            ))

    def auth(self):
        auth_params = {
            "client_id": self.secret["client_id"],
            "redirect_uri": self.secret["redirect_uri"],
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/youtube.force-ssl",
            "state": "authentication"
        }
        request = requests.get(Endpoint.AUTH_URI, params=auth_params)
        code = input(request.url + "\n")
        token_params = {
            'code': code,
            'client_id': self.secret["client_id"],
            'client_secret': self.secret["client_secret"],
            'redirect_uri': self.secret["redirect_uri"],
            'grant_type': "authorization_code"
        }
        response = requests.post(Endpoint.TOKEN_URI, params=token_params)
        assert response.status_code == 200
        return response.json()

    def retrieve_token(self):
        if os.path.isfile(Endpoint.TOKEN_FILE):
            with open(Endpoint.TOKEN_FILE) as file:
                self.auth_token = json.load(file)
                self.refresh_token = self.auth_token
            return self.refresh_token
        else:
            token = self.auth()
            with open(Endpoint.TOKEN_FILE, "w") as file:
                json.dump(token, file)
            self.auth_token = token
            return self.refresh()

    def refresh(self):
        token_params = {
            'client_id': self.secret["client_id"],
            'client_secret': self.secret["client_secret"],
            'refresh_token': self.auth_token["refresh_token"],
            'grant_type': "refresh_token"
        }
        response = requests.post(Endpoint.TOKEN_URI, params=token_params)
        assert response.status_code == 200
        self.refresh_token = response.json()
        return self.refresh_token

    def headers(self):
        return {
            "Authorization": "Bearer " + self.refresh_token["access_token"]
        }

    def get(self, url, params, retry=False, cost=1):
        self.log(url, params, cost)
        response = requests.get(url, params=params, headers=self.headers())
        if response.status_code == 401 and not retry:
            self.refresh()
            return self.get(url, params, retry=True, cost=cost)
        return response.json()

    def list_channel_username(self, username):
        return self.get(Endpoint.CHANNELS_URI, {
            "part": "snippet",
            "maxResults": 50,
            "forUsername": username
        }, cost=3)["items"]

    def list_channel_id(self, channel_id):
        return self.get(Endpoint.CHANNELS_URI, {
            "part": "snippet",
            "maxResults": 50,
            "id": channel_id
        }, cost=3)["items"]

    def videos_from_channel(self, channel_id):
        return self.get(Endpoint.SEARCH_URI, {
            "part": "snippet",
            "maxResults": 50,
            "order": "date",
            "channelId": channel_id
        }, cost=100)["items"]

    def find_video(self, video_id):
        return self.get(Endpoint.VIDEO_URI, {
            "part": "snippet",
            "id": video_id,
        }, cost=3)["items"]
