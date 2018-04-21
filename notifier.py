from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib.request
import threading
import datetime
import sqlite3
import smtplib
import json
import time
import sys
import re

from youtube import *

class Notifier:

    CLIENT_SECRETS_FILE = 'client_secret.json'

    def __init__(self, wait=False):
        self.server = None
        self.conn = sqlite3.connect('videos.db')
        self.init_database()

        with open(self.CLIENT_SECRETS_FILE, 'r+') as f:
            client_secret = json.load(f)
            self.smtp = client_secret["smtp"]
            self.api = YoutubeAPI(client_secret["app"], wait=wait)

    def init_database(self):
        c = self.conn.cursor()
        try:
            c.execute('CREATE TABLE videos (t TIMESTAMP DEFAULT CURRENT_TIMESTAMP, '\
                      + 'channelId TEXT, videoId TEXT, videoTitle TEXT)')
            self.conn.commit()
        except sqlite3.OperationalError:
            pass
        try:
            c.execute('CREATE TABLE patterns (channelId TEXT, '\
                      + 'channelTitle TEXT, pattern TEXT)')
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

    def close(self):
        self.conn.close()
        if self.server is not None:
            self.server.close()

    def retrieve_matching_videos(self, channel_id, pattern):
        return apply_mask(self.api.search_list(channel_id)["items"], pattern)

    def is_new(self, channel_id, vid):
        video_id = vid["id"]["videoId"]
        video_title = vid["snippet"]["title"]
        c = self.conn.cursor()
        c.execute('SELECT * FROM videos WHERE videoId=?', (video_id,))
        if c.fetchone() is None:
            c.execute('INSERT INTO videos (channelId, videoId, videoTitle)'\
                      + ' VALUES (?, ?, ?)', (channel_id, video_id, video_title))
            self.conn.commit()
            return True
        return False

    def inspect_channel(self, channel_id, pattern):
        c = self.conn.cursor()
        vids = self.api.search_list(channel_id)["items"]
        channel_title = vids[0]["snippet"]["channelTitle"]
        c.execute('INSERT INTO patterns VALUES (?, ?, ?)',
                  (channel_id, channel_title, pattern))
        self.conn.commit()
        log("Added channel " + channel_id)

    def inspect_username(self, username, pattern):
        self.inspect_channel(
            self.api.channels_list(username)["items"][0]["id"],
            pattern
        )

    def list_channels(self):
        c = self.conn.cursor()
        c.execute('SELECT * FROM patterns')
        for channel_id, channel_title, pattern in c.fetchall():
            print(channel_id + "\t" + channel_title + "\t" + pattern)

    def check_for_news(self, channel_id, pattern):
        vids = self.retrieve_matching_videos(channel_id, pattern)
        for vid in vids:
            if self.is_new(channel_id, vid):
                log("New video from " + vid['snippet']['channelTitle']
                    + ": " + vid['snippet']['title'])
                self.notify_video(vid)

    def update(self):
        c = self.conn.cursor()
        c.execute('SELECT * FROM patterns')
        for channel_id, channel_title, pattern in c.fetchall():
            log("Checking " + channel_title + " for pattern " + pattern)
            self.check_for_news(channel_id, pattern)

    def notify_video(self, vid):
        self.send_mail(vid)
        self.api.playlist_item_insert(vid['id']['videoId'])

    def send_mail(self, vid):
        subject = "[notif.py] New video from " + vid['snippet']['channelTitle']
        body = open('mail-template.html', 'r').read()\
            .replace("%CHANNEL_TITLE%", vid['snippet']['channelTitle'])\
            .replace("%VIDEO_ID%", vid['id']['videoId'])\
            .replace("%THUMBNAIL_URL%",
                     vid['snippet']['thumbnails']['medium']['url'])\
            .replace("%VIDEO_TITLE%", vid['snippet']['title'])
        # log("Sending mail " + subject + " to " + self.smtp["address"])
        msg = MIMEMultipart()
        msg['From'] = self.smtp["address"]
        msg['To'] = self.smtp["address"]
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        if self.server is None:
            log("Connecting to SMTP server")
            self.server = smtplib.SMTP("smtp.gmail.com", 587)
            self.server.ehlo()
            self.server.starttls()
            self.server.ehlo()
            self.server.login(self.smtp["username"],
                              self.smtp["password"])
            log("Connected to SMTP server")
        self.server.sendmail(self.smtp["address"],
                             self.smtp["address"],
                             msg.as_string())


def apply_mask(videos, pattern):
    prog = re.compile(pattern)
    filtered_videos = []
    for vid in videos:
        result = prog.search(vid['snippet']['title'])
        if result is not None:
            filtered_videos.append(vid)
    return filtered_videos


def clean(string):
    new_string = ""
    for c in string:
        try:
            new_string += c
        except UnicodeEncodeError:
            pass
    return new_string
