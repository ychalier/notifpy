from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib.request
import datetime
import sqlite3
import smtplib
import json
import time
import re


class API:

    def __init__(self):
        self.settings = {}
        self.read_settings()
        self.server = None
        self.conn = sqlite3.connect('videos.db')
        self.init_database()

    def read_settings(self):
        settings = {}
        file_object = open('.credentials', 'r')
        for line in file_object.readlines():
            line = line.replace('\n', '')
            settings[line.split('=')[0]] = line.split('=')[1]
        for ts in ["google_api_key", "smtp_host", "smtp_username",
                   "smtp_password", "smtp_address"]:
            if ts not in settings.keys():
                print("[ERROR] Setting not found: " + ts)
                exit()
        file_object.close()
        self.settings = settings

    def init_database(self):
        c = self.conn.cursor()
        try:
            c.execute('CREATE TABLE videos (channel TEXT, video TEXT)')
            self.conn.commit()
        except sqlite3.OperationalError:
            pass
        try:
            c.execute('CREATE TABLE channels (id TEXT, pattern TEXT)')
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

    def retrieve_channel_id(self, username):
        href = "https://www.googleapis.com/youtube/v3/channels?part=snippet" \
               + "&forUsername=" + username\
               + "&key=" + self.settings["google_api_key"]
        response = urllib.request.urlopen(href)
        return json.loads(response.read().decode('utf-8'))['items'][0]['id']

    def retrieve_video_list(self, channel_id):
        href = "https://www.googleapis.com/youtube/v3/search?order=date" \
               + "&part=snippet&channelId=" + channel_id \
               + "&maxResults=25&key=" + self.settings["google_api_key"]
        response = urllib.request.urlopen(href)
        return json.loads(response.read().decode('utf-8'))['items']

    def retrieve_matching_videos(self, channel_id, pattern):
        return apply_mask(self.retrieve_video_list(channel_id), pattern)

    def notify_video(self, vid):
        subject = "[notif.py] New video from " + vid['snippet']['channelTitle']
        body = open('mail-template.html', 'r').read()\
            .replace("%CHANNEL_TITLE%", vid['snippet']['channelTitle'])\
            .replace("%VIDEO_ID%", vid['id']['videoId'])\
            .replace("%THUMBNAIL_URL%",
                     vid['snippet']['thumbnails']['medium']['url'])\
            .replace("%VIDEO_TITLE%", vid['snippet']['title'])
        self.send_mail(subject, body)
        log("Sending mail " + subject + " to " + self.settings["smtp_address"])

    def send_mail(self, subject, body):
        msg = MIMEMultipart()
        msg['From'] = self.settings["smtp_address"]
        msg['To'] = self.settings["smtp_address"]
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        if self.server is None:
            log("Connecting to SMTP server")
            self.server = smtplib.SMTP("smtp.gmail.com", 587)
            self.server.ehlo()
            self.server.starttls()
            self.server.ehlo()
            self.server.login(self.settings["smtp_username"],
                              self.settings["smtp_password"])
            log("Connected to SMTP server")
        self.server.sendmail(self.settings["smtp_address"],
                             self.settings["smtp_address"],
                             msg.as_string())

    def is_new(self, channel_id, video_id):
        c = self.conn.cursor()
        c.execute('SELECT * FROM videos WHERE video=?', (video_id,))
        if c.fetchone() is None:
            c.execute('INSERT INTO videos VALUES (?, ?)',
                      (channel_id, video_id))
            self.conn.commit()
            return True
        return False

    def inspect_channel(self, channel_id, pattern):
        c = self.conn.cursor()
        c.execute('INSERT INTO channels VALUES (?, ?)', (channel_id, pattern))
        self.conn.commit()

    def inspect_username(self, username, pattern):
        self.inspect_channel(self.retrieve_channel_id(username), pattern)

    def check_for_news(self, channel_id, pattern):
        vids = self.retrieve_matching_videos(channel_id, pattern)
        for vid in vids:
            if self.is_new(channel_id, vid['id']['videoId']):
                log("New video from " + channel_id
                    + ": " + vid['id']['videoId'])
                self.notify_video(vid)

    def update(self):
        c = self.conn.cursor()
        c.execute('SELECT * FROM channels')
        for channel_id, pattern in c.fetchall():
            log("Checking channel " + channel_id)
            self.check_for_news(channel_id, pattern)

    def close(self):
        self.conn.close()
        if self.server is not None:
            self.server.close()


def apply_mask(videos, pattern):
    prog = re.compile(pattern)
    filtered_videos = []
    for vid in videos:
        result = prog.match(vid['snippet']['title'])
        if result is not None:
            filtered_videos.append(vid)
    return filtered_videos


def log(text):
    timestamp = datetime.datetime.fromtimestamp(
        time.time()).strftime('%Y-%m-%d %H:%M:%S')
    print(timestamp + "\t" + text)


if __name__ == "__main__":
    api = API()
    api.update()
    api.close()
