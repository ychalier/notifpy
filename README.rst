# Notifpy

**Notifpy** is a custom YouTube subscription system. The original goal was to
get rid of a Google account. However, querying YouTube API requires an API key
and therefore you still need an account. The good thing is that it wont be able
to see what or when you are watching anything.

## 1. Setup

### 1.1. Install

```bash
git clone https://github.com/ychalier/notifpy.git
cd notifpy/
pip3 install -r requirements.txt
```

### 1.2. Youtube API

In order to use YouTube Data API v3, you need an [API key](https://console.developers.google.com/apis/credentials).
For more information you can check the [documentation](https://developers.google.com/youtube/registering_an_application).
Save your API key in a JSON file `secret.json` with the following schema:
```json
{
    "app": {
        "client_id": "...",
        "redirect_uri": "...",
        "client_secret": "..."
    }
}
```

You are now ready to perform the first start of the program. Try it with
```bash
python3 notif.py list
```

Since this is your first run, the program will have to retrieve a token from the
API. To do so, copy and paste the URL prompted in the terminal to your web
browser and allow access rights. You will get redirected to the `redirect_uri`
setting of the app. The URL will contain the GET parameter `code`. Copy it and
paste it in the terminal.

## 2. Usage

### 2.1. Channels

Subscribe to a channel with:

```bash
python3 notif.py create channel <CHANNEL ID> <PRIORITY>
```

The **channel id** is a 24 characters long string starting with `UC`. To get it,
go on the YouTube channel homepage. The URI is of the following form:
```
https://www.youtube.com/channel/CHANNEL-ID/
```

The **priority** is used for automated updates. Channels with priority `0` are
updated on Saturdays at midnight. Channels with priority `1` are updated every
day at 7pm. Channels with priority `2` are updated every day at 8am, 12am, 4pm,
6pm, 8pm and 10pm.

### 2.2. Patterns

You can apply filters to channels. If a channel has at least one pattern, then
you will only see videos whose title matches one of the patterns. You can use
regular expressions if they follow [Python's syntax](https://docs.python.org/3/library/re.html).

Add a pattern with:
```bash
python3 notif.py create pattern <CHANNEL ID> <REGEX>
```
The `REGEX` field can contain spaces.

### 2.3. Views

You can generate an HTML page that displays the lastly published videos. It gets
printed to the standard output, therefore you can pipe it to a file.

```bash
python3 notif.py html videos > /var/www/html/videos.html
```

### 2.4. Manual Usage

Run the program with flag `--help` for an inventory of possible commands.

### 2.5. Automation

Run the script every hour with the following cron task (use `crontab -e` append
it). The program will adapt updates based on the given priorities.

```
0 * * * * cd /PATH/notifpy && python3 notif.py update schedule
```

Change `PATH` to your actual path.
