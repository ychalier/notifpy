import webbrowser
import requests
import os.path
import socket
import json
import time


class YoutubeAPI:

    TOKEN_URI = 'https://www.googleapis.com/oauth2/v4/token'
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    PLAYLIST_URI = 'https://www.googleapis.com/youtube/v3/playlists'
    PLAYLIST_ITEMS_URI = 'https://www.googleapis.com/youtube/v3/playlistItems'
    CHANNELS_URI = 'https://www.googleapis.com/youtube/v3/channels'
    SEARCH_URI = 'https://www.googleapis.com/youtube/v3/search'
    TOKEN_FILE = 'token.json'
    REDIRECT_PORT = 8000
    REDIRECT_URI = 'http://localhost:' + str(REDIRECT_PORT) + '/'
    PLAYLIST_TITLE = 'notif.py'
    PLAYLIST_DESCRIPTION = 'Automatic playlist from notif.py'

    def __init__(self, secret):
        self.secret = secret
        self.retrieve_token()
        if "playlist_id" not in self.secret.keys():
            playlist = self.create_playlist()
            self.secret["playlist_id"] = playlist["id"]
            with open(self.CLIENT_SECRETS_FILE, 'w') as outfile:
                json.dump(self.secret, outfile)
        self.playlist_id = self.secret["playlist_id"]

    def auth(self):
        auth_params = {
            "client_id": self.secret["client_id"],
            "redirect_uri": self.REDIRECT_URI,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/youtube.force-ssl",
            "state": "authentication"
        }

        req = requests.get(self.AUTH_URI, params=auth_params)
        log("Opening request with authentication request url")
        webbrowser.open(req.url)

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', self.REDIRECT_PORT))
        log("Starting loopback server on port", self.REDIRECT_PORT)
        while True:
            server.listen(1)
            client, address = server.accept()
            log("Loopback response received")
            request = {}
            for param in client.recv(255).decode("utf-8")\
                               .split('\r\n')[0][6:-9].split('&'):
                key, value = param.split('=')
                request[key] = value

            body = "".join([
                "<html>",
                "<head>",
                "<style>"
                "* { font-family:sans-serif; text-align:center }",
                "</style>",
                "</head>",
                "<body>",
                "<h1>notif.py</h1>",
                "<p>You can close this tab now.</p>",
                "</body>",
                "</html>"
            ]).encode()

            head = "".join([
                "HTTP/1.1 200 OK",
                "Content-Type: text/plain\n",
                "Content-Length: " + str(len(body)) + "\n",
                "Connection: close\n\n"
            ]).encode()

            client.send(head)
            client.send(body)

            time.sleep(.5)

            client.close()
            server.close()
            break

        log("Loopback server closed")

        token_params = {
            'code': request['code'],
            'client_id': self.secret["client_id"],
            'client_secret': self.secret["client_secret"],
            'redirect_uri': self.REDIRECT_URI,
            'grant_type': "authorization_code"
        }

        log("Retrieving authentication token")
        req = requests.post(self.TOKEN_URI, params=token_params)
        return req.json()

    def refresh(self):
        token_params = {
            'client_id': self.secret["client_id"],
            'client_secret': self.secret["client_secret"],
            'refresh_token': self.auth_token["refresh_token"],
            'grant_type': "refresh_token"
        }

        log("Refreshing token")
        req = requests.post(self.TOKEN_URI, params=token_params)
        self.refresh_token = req.json()
        return req.json()

    def retrieve_token(self):
        if os.path.isfile(self.TOKEN_FILE):
            with open(self.TOKEN_FILE, 'r+') as f:
                self.auth_token = json.load(f)
                return self.refresh()
        else:
            token = self.auth()
            with open(self.TOKEN_FILE, 'w') as outfile:
                json.dump(token, outfile)
                self.auth_token = token
                return self.refresh()

    def headers(self):
        header = {
            "Authorization": "Bearer " + self.refresh_token["access_token"]
        }
        return header

    def playlist_insert(self):
        params = {
            "part": "snippet, status"
        }
        body = {
            "snippet" : {
                "title": self.PLAYLIST_TITLE,
                "description": self.PLAYLIST_DESCRIPTION
            },
            "status" : {
                "privacyStatus": "public"
            }
        }
        req = requests.post(self.PLAYLIST_URI,
                            params=params, json=body,
                            headers=self.headers())
        return req.json()

    def playlist_item_insert(self, video_id):
        params = {
            "part": "snippet"
        }
        body = {
            "snippet" : {
                "playlistId": self.playlist_id,
                "resourceId": {
                    "videoId": video_id,
                    "kind": "youtube#video"
                }
            }
        }
        req = requests.post(self.PLAYLIST_ITEMS_URI,
                            params=params, json=body,
                            headers=self.headers())
        return req.json()

    def channels_list(self, username):
        params = {
            "part": "id",
            "maxResults": 1,
            "forUsername": username
        }
        req = requests.get(self.CHANNELS_URI,
                           params=params,
                           headers=self.headers())
        return req.json()

    def search_list(self, channel_id):
        params = {
            "part": "snippet",
            "maxResults": 50,
            "order": "date",
            "channelId": channel_id
        }
        req = requests.get(self.SEARCH_URI,
                           params=params,
                           headers=self.headers())
        return req.json()


def log(arg, **kwargs):
    pass
