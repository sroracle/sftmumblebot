#!/usr/bin/env python2
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


def mumbleTextMessageCallback(sender, message):
    line = "mumble: " + sender + ": " + message
    console.sendTextMessage(line)
    irc.sendTextMessage(line)
    if message == 'gtfo':
        mumble.sendTextMessage("KAY CU")
        mumble.stop()


def ircTextMessageCallback(sender, message):
    line = "irc: " + sender + ": " + message
    console.sendTextMessage(line)
    mumble.sendTextMessage(line)
    if message == 'gtfo':
        irc.sendTextMessage("KAY CU")
        irc.stop()


def consoleTextMessageCallback(sender, message):
    line = "console: " + message
    irc.sendTextMessage(line)
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
    console.registerTextCallback(consoleTextMessageCallback)

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
