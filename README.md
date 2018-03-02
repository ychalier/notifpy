# notif.py

Some crazy productive YouTube channels publish tons a video a day, which would flood your subscription list. However, there is one series they have that particularly have you interested. Install *notif.py*, and it will notify you whenever a new video comes out!

## install

First clone the repository:

    git clone https://github.com/ychalier/notif.py.git
    cd notif.py/

In order to communicate with YouTube, the script requires a Google API key, which you can get from https://console.developers.google.com.

You will also need an SMTP server to be able to send mails to yourself when a new video comes out. If you use GMail, you can use the host `smtp.gmail.com:587`. The script will then need your username and password to connect to this host, and finally a mail address to receive the message.

All those information must be written in `.credentials`, a file in the same folder as `notif.py`. Here is an example:

    google_api_key=abcdefghijklmnopqrstuvwxyzabcdefghijklm
    smtp_host=smtp.gmail.com:587
    smtp_username=your.name@gmail.com
    smtp_password=password
    smtp_address=your.name@gmail.com

## usage

When started, the script starts a thread that runs in the background to check for new videos. Meanwhile, you can type in commands in the command prompt:

    notif.py>

Here is a list of available commands:

 - `quit`: stop the program (also closes the update thread)
 - `list`: list all handled channels
 - `update`: force update
 - `add`: see below

**Add a new videos series to check:** the command syntax is the following:

    notif.py>add TYPE IDENTIFIER PATTERN

To know the type and the identifier to put in, go check on YouTube the list of all videos from the channel you want to analyze:
 - if the URL is like `youtube.com/channel/UC2Qw1dzXDBAZPwS7zm37g8g/videos`, then the type is `channel` and the identifier is the channel id, in this case `UC2Qw1dzXDBAZPwS7zm37g8g`.
 - if the URL is like `youtube.com/user/username/videos`, the the type is `username` and the identifier is the given username. *Caution: the displayed username does not work, use the one in the URL*.

**Automatic start:** if you want for the script to be executed at startup silently so the update thread always runs in the background, be sure to use the command `pythonw notif.py`.

For example, on Windows, create a batch file in `%AppData%\Roaming\Microsoft\Windows\Start Menu\Programs\Startup` and write:

    @echo off
    cd C:\Path\To\The\Folder\notif.py\
    start /B pythonw notif.py
