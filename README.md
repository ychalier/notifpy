# notif.py

Some crazy productive YouTube channels (like stream replay or TV/Radio channels) publish tons a video a day, which would flood your subscription list. However, there is one series they have that particularly have you interested. Install *notif.py*, and it will notify you whenever a new video comes out!

## install

First clone the repository:

    git clone https://github.com/ychalier/notif.py.git
    cd notif.py/

In order to use YouTube Data API v3, the script requires an API client, which you can create at https://console.developers.google.com/apis/credentials. For more information you can check the [documentation](https://developers.google.com/youtube/registering_an_application).

You will also need an SMTP server to be able to send mails to yourself when a new video comes out. If you use GMail, you can use the host `smtp.gmail.com:587`. The script will then need your username and password to connect to this host, and finally a mail address to receive the message.

Those information goes into a JSON file `client_secret.json` located next to the other script files. Here's the format of this file:

    {
      "app": {
        "client_id": "PASTE YOUR CLIENT ID HERE",
        "client_secret": "PASTE YOUR CLIENT SECRET HERE"
      },
      "smtp": {
        "host": "smtp.gmail.com:587",
        "username": "alex.delarge@gmail.com",
        "password": "hereisasecurepassword",
        "address": "alex.delarge@gmail.com"
      }
    }

## setup and permissions

At first launch, the script will ask you to grant access to your YouTube account. This is needed to retrieve the token that will be used to managed the playlist _notif.py_ on your account, create it and insert new videos into it.

#### revocation

You can revoke this permission at any moment from your Google account. Go to your Application preferences and revoke the token to be fully sure. Or simply delete the `token.json` local file. No copy is made online.

## usage

When started, the script starts a thread that runs in the background to check for new videos. Meanwhile, you can type in commands in the command prompt:

    notif.py>

Here is a list of available commands:

 - `quit`: stop the program (also closes the update thread)
 - `list`: list all currently checked channels
 - `update`: force update
 - `add`: see below

**Add a new videos series to check**

The command syntax is the following:

    notif.py>add TYPE IDENTIFIER PATTERN

To know the type and the identifier to put in, go check on YouTube the list of all videos from the channel you want to analyze:
 - if the URL is like `youtube.com/channel/UC2Qw1dzXDBAZPwS7zm37g8g/videos`, then the type is `channel` and the identifier is the channel id, in this case `UC2Qw1dzXDBAZPwS7zm37g8g`.
 - if the URL is like `youtube.com/user/username/videos`, the type is `username` and the identifier is the given username. *Caution: the displayed username (aka the Channel Title) does not work, use the one in the URL*.

Then the *pattern* is a regular expression to match the videos from this channel that you want to extract. It can be a single string matching or you can use regular expression characters. See [re documentation](https://docs.python.org/3.5/library/re.html) for more information.

If you don't know whether you should write `channel` or `username`, use the following syntax:

    notif.py>add URL PATTERN

Just paste the URL you get when going on the desired channel's page.

**Now just wait for a video to be published, and you'll get a notification on your email address and the video will be added to the playlist _notif.py_ created on your YouTube account.**

## tips

**Automatic start**

If you want for the script to be executed at startup silently so the update thread always runs in the background, be sure to use the command `pythonw notif.py`.

For example, on Windows, create a batch file in `%AppData%\Roaming\Microsoft\Windows\Start Menu\Programs\Startup` and write:

    @echo off
    cd C:\Path\To\The\Folder\notif.py\
    start /B pythonw notif.py

**Notification area**

I personally use it with `python` in a regular command window, so I can check the log so that everything's fine. But I did not want to see the command window always in my desktop or even my taskbar, so I found this little program [RBTray](http://rbtray.sourceforge.net) that allows you to minimize any window into the notification area. Pretty neat.

## development notes

### todo

 - [x] handle YouTube API errors
 - [x] detect when a refreshing is necessary
 - [x] send a mail when a new video comes out
 - [x] add new videos to a playlist
 - [ ] remove old videos from database
 - [ ] let user configure notification method(s)
 - [ ] help message
