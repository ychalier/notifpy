import re

from notifier import *


def print_begin(msg):
    print("----- BEGIN {0} -----".format(msg))


def print_end(msg, mode=0):
    if mode == 0:
        print("----- END {0} -----".format(msg))
    elif mode == 1:
        print("----- END {0} -----\nnotif.py>".format(msg), end='')


def cmd_list(notifier):
    print_begin("CHANNEL LIST")
    print("channel id              \tchannel title\tpattern")
    notifier.list_channels()
    print_end("CHANNEL LIST")
    return 0


def cmd_update(notifier):
    print_begin("FORCED UPDATE")
    notifier.update()
    print_end("FORCED UPDATE")
    return 0


def cmd_add(notifier, args):

    if len(args) == 2:
        regexp = re.compile("youtube.com\/(\w+)\/(\w+)\/?")
        match = regexp.search(args[0])
        mode, channel, pattern = match.group(1), match.group(1), args[1:]
    elif len(args) == 3:
        mode, channel, pattern = args[0], args[1], args[2:]
    else:
        return 1

    if mode in ["id", "channel"]:
        notifier.inspect_channel(channel, " ".join(pattern))
    elif mode in ["user", "username"]:
        notifier.inspect_username(channel, " ".join(pattern))
    return 0


class Timer(threading.Thread):

    def __init__(self, refresh_rate):
        super(Timer, self).__init__()
        self.refresh_rate = refresh_rate
        self._stop_event = threading.Event()

    def run(self):
        time.sleep(1)
        notifier = Notifier(wait=True)
        while not self.stopped():
            print("")
            print_begin("SCHEDULED UPDATE")
            notifier.update()
            print_end("SCHEDULED UPDATE", mode=1)
            self._stop_event.wait(self.refresh_rate)
        notifier.close()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class UserInput(threading.Thread):

    def __init__(self):
        super(UserInput, self).__init__()
        self._stop_event = threading.Event()
        self.notifier = None
        self.commands = {
            "exit": (lambda *args: 1),
            "list": (lambda *args: cmd_list(self.notifier)),
            "update": (lambda *args: cmd_update(self.notifier)),
            "add": (lambda *args: cmd_add(self.notifier, args[0])),
        }

    def run(self):
        self.notifier = Notifier()
        while not self.stopped():
            cmd = input("notif.py>").split(" ")
            if len(cmd) > 0 and cmd[0] in self.commands.keys():
                status = self.commands[cmd[0]](cmd[1:])
                if status == 1:
                    break
            else:
                print("'" + " ".join(cmd) + "' not recognized as a command.")
        self.notifier.close()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

if __name__ == "__main__":
    timer, user = Timer(180), UserInput()
    timer.start()
    user.start()
    user.join()
    timer.stop()
