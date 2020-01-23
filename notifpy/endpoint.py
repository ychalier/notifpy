"""This module provides an interface to use the YouTube and Twitch APIs."""


import os
import json
import time
import random
import logging
import datetime
import requests
from . import models


def generate_random_state(length=24):
    """Return a random string of letters and figures of specified length"""
    chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    random.seed(datetime.datetime.now().strftime("%D"))
    return "".join(random.choice(chars) for _ in range(length))


class Credentials:

    """API credentials"""

    def __init__(self, source):
        self.client_id = source["client_id"]
        self.client_secret = source["client_secret"]
        self.redirect_uri = source["redirect_uri"]
        self.scope = source["scope"]


class Token:

    """Token for OAuth authentication"""

    def __init__(self, field):
        self.field = field
        self.access_token = None
        self.refresh_token = None
        self.expires_in = None
        self.delivery_time = None
        self.load()

    def has_expired(self):
        """Check if current access token has expired"""
        if self.delivery_time is None or self.expires_in is None:
            return True
        return self.delivery_time + self.expires_in < time.time()

    def authorize(self, delivery):
        """Handle first token delivery"""
        self.access_token = delivery["access_token"]
        self.refresh_token = delivery.get(
            "refresh_token",
            delivery["access_token"]
        )
        self.expires_in = delivery["expires_in"]
        self.delivery_time = time.time()
        self.save()

    def refresh(self, delivery):
        """Handle token refreshing delivery"""
        self.access_token = delivery["access_token"]
        if "refresh_token" in delivery:
            self.refresh_token = delivery["refresh_token"]
        self.delivery_time = time.time()
        self.save()

    def revoke(self):
        """Revoke current token"""
        self.access_token = None
        self.refresh_token = None
        self.expires_in = None
        self.delivery_time = None
        os.remove(self.filename)

    def save(self):
        """Export current token"""
        obj = models.Token.load()
        setattr(obj, self.field, json.dumps({
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_in": self.expires_in,
            "delivery_time": self.delivery_time,
        }))
        obj.save()

    def load(self):
        """Load token from a file"""
        obj = models.Token.load()
        dictionnary = json.loads(getattr(obj, self.field))
        if len(dictionnary) > 0:
            self.access_token = dictionnary["access_token"]
            self.refresh_token = dictionnary["refresh_token"]
            self.expires_in = dictionnary["expires_in"]
            self.delivery_time = dictionnary["delivery_time"]

    def delivery_datetime(self):
        """Format delivery time as a datetime object"""
        if self.delivery_time is None:
            return datetime.datetime.fromtimestamp(0)
        return datetime.datetime.fromtimestamp(self.delivery_time)

    def expiration_datetime(self):
        """Format expiration time as a datetime object"""
        if self.delivery_time is None or self.expires_in is None:
            return datetime.datetime.fromtimestamp(0)
        return datetime.datetime.fromtimestamp(self.delivery_time + self.expires_in)


class OAuthFlow:

    """Implement OAuth authentication flow for API endpoints"""

    def __init__(self, credentials, uris, token_field):
        self.credentials = Credentials(credentials)
        self.authorize_uri = uris["authorize"]
        self.token_uri = uris["token"]
        self.revoke_uri = uris["revoke"]
        self.state = generate_random_state()
        self.token = Token(token_field)

    def get_authorize_url(self):
        """Return the authorization URL the user should be redirected too"""
        request = requests.Request("GET", self.authorize_uri, params={
            "client_id": self.credentials.client_id,
            "redirect_uri": self.credentials.redirect_uri,
            "response_type": "code",
            "scope": self.credentials.scope,
            "state": self.state,
            "access_type": "offline",
            "prompt": "consent",
        }).prepare()
        logging.debug("Prepared authorization url: %s", request.url)
        return request.url

    def handle_redirect(self, request):
        """Handle code reception from API"""
        if "code" not in request.GET or "state" not in request.GET:
            logging.error("Invalid request GET parameters")
            return
        if self.state != request.GET["state"]:
            logging.error("Invalild state encountered")
            return
        logging.debug("Received valid code '%s'", request.GET["code"])
        response = requests.post(self.token_uri, params={
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": self.credentials.redirect_uri,
            "code": request.GET["code"]
        })
        if response.status_code != 200:
            logging.error(
                "Invalid response status code %s",
                response.status_code
            )
            return
        self.token.authorize(response.json())

    def refresh(self):
        """Refresh the current token"""
        logging.info("Refreshing token at %s", self.token_uri)
        response = requests.post(
            self.token_uri,
            params={
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
                "refresh_token": self.token.refresh_token,
                "grant_type": "refresh_token"
            }
        )
        if response.status_code != 200:
            logging.error(
                "Invalid response status code %d: %s",
                response.status_code,
                response.text,
            )
            return
        self.token.refresh(response.json())

    def revoke(self):
        """Revoke the current token"""
        logging.info("Revoking token at %s", self.revoke_uri)
        response = requests.post(
            self.revoke_uri,
            params={
                "client_id": self.credentials.client_id,
                "token": self.token.access_token,
            }
        )
        if response.status_code != 200:
            logging.error(
                "Invalid response status code %s",
                response.status_code
            )
        self.token.revoke()


class QuotaBucket:

    """Implements the tokens bucket algorithm."""

    def __init__(self, size, rate):
        self.size = size
        self.rate = rate
        self.content = size
        self.last_content_update = time.time()

    def update(self):
        """Refill the bucket since last update"""
        now = time.time()
        elapsed = now - self.last_content_update
        to_add = int(elapsed * self.rate)
        if to_add > 0:
            self.content = min(self.size, self.content + to_add)
            self.last_content_update = now

    def get(self):
        """Return the current bucket filled ratio"""
        self.update()
        return self.content / self.size

    def use(self, amount):
        """Use a sip of the bucket"""
        self.update()
        if self.content >= amount:
            self.content -= amount
            return True
        return False


class Endpoint:

    """Media provider API endpoint"""

    def __init__(self, oauth_flow, quota_bucket):
        self.oauth_flow = oauth_flow
        self.quota_bucket = quota_bucket

    def headers(self):
        """Return the headers containing the access token"""
        if self.oauth_flow.token.has_expired():
            self.oauth_flow.refresh()
        return {
            "Authorization": "Bearer %s" % self.oauth_flow.token.access_token
        }

    def get(self, url, params, cost):
        """Execute a request"""
        if not self.quota_bucket.use(cost):
            logging.warning("Quota bucket is full!")
        response = requests.get(url, params=params, headers=self.headers())
        if not response.status_code == 200:
            logging.error(
                "Wrong answer from API (error %d): %s",
                response.status_code,
                response.text
            )
            return None
        return response.json()


class YoutubeEndpoint(Endpoint):

    """YouTube endpoint"""

    def __init__(self, credentials):
        Endpoint.__init__(
            self,
            OAuthFlow(
                credentials,
                {
                    "authorize": "https://accounts.google.com/o/oauth2/auth",
                    "token": "https://www.googleapis.com/oauth2/v4/token",
                    "revoke": "https://accounts.google.com/o/oauth2/revoke",
                },
                "youtube",
            ),
            QuotaBucket(
                10000,
                10000. / (24. * 3600.)
            ),
        )

    def channels_list(self, for_username=None, channel_id=None):
        """https://developers.google.com/youtube/v3/docs/channels/list"""
        params = {
            "part": "snippet,contentDetails",
            "maxResults": 50,
        }
        if for_username is not None:
            params["forUsername"] = for_username
        if channel_id is not None:
            params["id"] = channel_id
        return self.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params,
            5
        )

    def playlist_items_list(self, playlist_id, part="snippet", page_token=None):
        """https://developers.google.com/youtube/v3/docs/playlistItems/list"""
        params = {
            "part": part,
            "maxResults": 50,
            "playlistId": playlist_id,
        }
        if page_token is not None:
            params["pageToken"] = page_token
        cost = 1
        if part == "snippet":
            cost = 3
        return self.get(
            "https://www.googleapis.com/youtube/v3/playlistItems",
            params,
            cost
        )

    def search_list(self, channel_id=None, resource_type=None):
        """https://developers.google.com/youtube/v3/docs/search/list"""
        params = {
            "part": "snippet",
            "maxResults": 50,
            "order": "date",
        }
        if channel_id is not None:
            params["channelId"] = channel_id
        if resource_type is not None:
            params["type"] = resource_type
        return self.get(
            "https://www.googleapis.com/youtube/v3/search",
            params,
            100
        )

    def videos_list(self, video_id):
        """https://developers.google.com/youtube/v3/docs/videos/list"""
        params = {
            "part": "snippet",
            "id": video_id,
        }
        return self.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params,
            3
        )


class TwitchEndpoint(Endpoint):

    """Twitch endpoint"""

    def __init__(self, credentials):
        Endpoint.__init__(
            self,
            OAuthFlow(
                credentials,
                {
                    "authorize": "https://id.twitch.tv/oauth2/authorize",
                    "token": "https://id.twitch.tv/oauth2/token",
                    "revoke": "https://id.twitch.tv/oauth2/revoke",
                },
                "twitch",
            ),
            QuotaBucket(
                800,
                800 / 60
            ),
        )

    def users(self, ids=None, logins=None):
        """https://dev.twitch.tv/docs/api/reference#get-users"""
        params = dict()
        if ids is not None:
            params["id"] = ids
        if logins is not None:
            params["login"] = logins
        return self.get("https://api.twitch.tv/helix/users", params, 1)

    def streams(self, logins):
        """https://dev.twitch.tv/docs/api/reference#get-streams"""
        params = {
            "user_login": logins,
            "first": 100,
        }
        return self.get("https://api.twitch.tv/helix/streams", params, 1)

    def games(self, ids):
        """https://dev.twitch.tv/docs/api/reference#get-games"""
        params = {
            "id": ids,
        }
        return self.get("https://api.twitch.tv/helix/games", params, 1)
