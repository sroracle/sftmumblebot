#!/usr/bin/env python3
import html
import html.parser
import sys
from . import MumbleConnection
from . import IRCConnection
from . import ConsoleConnection
import time
import configparser
import os.path
import sftbot

irc = None
mumble = None
console = None

class TakeADump(html.parser.HTMLParser):
    def __init__(self, feed, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.url = None
        self.feed(feed)

    def handle_starttag(self, tag, attrs):
        attrs = {i: j for i, j in attrs}
        if tag == "a" and "href" in attrs:
            self.url = attrs["href"]

    def handle_data(self, data):
        self.data += data.split()

    def handle_endtag(self, tag):
        if tag == "a":
            self.url = None

def mumbleTextMessageCallback(sender, message):
    if message.startswith("!"):
        return
    if sender == "Music" and not message.startswith("Playing"):
        return
    line = f"<{sender}> "
    line += " ".join(TakeADump(message).data)
    console.sendTextMessage(line)
    irc.sendTextMessage(line)


BOTS = ("IRC", "mumsi", "Music")

def ircTextMessageCallback(sender, message):
    if message == "!mumbleusers":
        users = mumble._userlist.copy()
        for i in BOTS:
            users.discard(i)
        users = sorted(users)
        if not users:
            line = "Just bots."
        else:
            line = ", ".join([i[0] + "\u200b" + i[1:] for i in users])

        irc.sendTextMessage(line)
        return

    line = f"<{sender}> {message}"
    line = html.escape(line)
    console.sendTextMessage(line)
    mumble.sendTextMessage(line)




def mumbleConnected():
    irc.setAway()


def mumbleDisconnected():
    line = "connection to mumble lost. reconnect in 5 seconds."
    console.sendTextMessage(line)
    irc.setAway(line)
    time.sleep(5)
    mumble.start()


def mumbleConnectionFailed():
    line = "connection to mumble failed. retrying in 15 seconds."
    console.sendTextMessage(line)
    irc.setAway(line)
    time.sleep(15)
    mumble.start()


def ircConnected():
    if mumble.established:
        mumble.setComment()


def ircDisconnected():
    line = "connection to irc lost. reconnect in 15 seconds."
    console.sendTextMessage(line)
    mumble.setComment(line)
    time.sleep(15)
    irc.start()


def ircConnectionFailed():
    line = "connection to irc failed. retrying in 15 seconds."
    console.sendTextMessage(line)
    mumble.setComment(line)
    time.sleep(15)
    irc.start()


def main():
    print("sft mumble bot " + sftbot.VERSION)

    global mumble
    global irc
    global console

    loglevel = 3

    if len(sys.argv) > 1:
        # load the user-specified conffile
        conffiles = [sys.argv[1]]
    else:
        # try finding a confile at one of the default paths
        conffiles = ["sftbot.conf", "/etc/sftbot.conf"]

    # try all of the possible conffile paths
    for conffile in conffiles:
        if os.path.isfile(conffile):
            break
    else:
        if len(conffiles) == 1:
            raise Exception("conffile not found (" + conffiles[0] + ")")
        else:
            raise Exception("conffile not found at any of these paths: " +
                            ", ".join(conffiles))

    # read the conffile from the identified path
    print("loading conf file " + conffile)
    cparser = configparser.ConfigParser()
    cparser.read(conffile)

    # configuration for the mumble connection
    mblservername = cparser.get('mumble', 'server')
    mblport = cparser.getint('mumble', 'port')
    mblnick = cparser.get('mumble', 'nickname')
    mblchannel = cparser.get('mumble', 'channel')
    mblpassword = cparser.get('mumble', 'password')
    mblloglevel = cparser.getint('mumble', 'loglevel')
    mblcertfile = cparser.get('mumble', 'certfile')
    mblkeyfile = cparser.get('mumble', 'keyfile')

    # configuration for the IRC connection
    ircservername = cparser.get('irc', 'server')
    ircport = cparser.getint('irc', 'port')
    ircnick = cparser.get('irc', 'nickname')
    ircchannel = cparser.get('irc', 'channel')
    ircpassword = cparser.get('irc', 'password', fallback='')
    ircauthtype = cparser.get('irc', 'authtype')
    ircloglevel = cparser.getint('irc', 'loglevel')

    # create server connections
    # hostname, port, nickname, channel, password, name, loglevel
    mumble = MumbleConnection.MumbleConnection(
        mblservername,
        mblport,
        mblnick,
        mblchannel,
        mblpassword,
        "mumble",
        mblloglevel,
        mblcertfile,
        mblkeyfile)

    irc = IRCConnection.IRCConnection(
        ircservername,
        ircport,
        ircnick,
        ircchannel,
        ircpassword,
        ircauthtype,
        "irc",
        ircloglevel)

    console = ConsoleConnection.ConsoleConnection(
        "console",
        loglevel)

    # register text callback functions
    mumble.registerTextCallback(mumbleTextMessageCallback)
    irc.registerTextCallback(ircTextMessageCallback)

    # register connection-established callback functions
    mumble.registerConnectionEstablishedCallback(mumbleConnected)
    irc.registerConnectionEstablishedCallback(ircConnected)

    # register connection-lost callback functions
    irc.registerConnectionLostCallback(ircDisconnected)
    mumble.registerConnectionLostCallback(mumbleDisconnected)

    # register connection-failed callback functions
    irc.registerConnectionFailedCallback(ircConnectionFailed)
    mumble.registerConnectionFailedCallback(mumbleConnectionFailed)

    # start the connections.
    # they will be self-sustaining due to the callback functions.
    mumble.start()
    irc.start()

    # start the console connection, outside a thread (as main loop)
    console.run()


if __name__ == "__main__":
    main()
