#!/usr/bin/env python3
import sys, os

import logging
import time

from optparse import OptionParser

from multiprocessing.connection import Listener, Client
import socket

sys.path.append(os.path.join(os.path.dirname(__file__), "include"))
import g15daemon
import xrecorder

from config import AppConfig
from lcdmanager import LCDKeyWatcher

KEYS = {"XK_VOLUMEDOWN": 122, "XK_VOLUMEUP": 123, "XK_NEXT": 171, "XK_PLAYPAUSE": 172, "XK_PREVIOUS": 173, "XK_STOP": 174}
ACTIONS = {KEYS["XK_VOLUMEDOWN"]: "volume_down", KEYS["XK_VOLUMEUP"]: "volume_up", KEYS["XK_NEXT"]: "next", KEYS["XK_PLAYPAUSE"]: "play_pause", KEYS["XK_PREVIOUS"]: "previous", KEYS["XK_STOP"]: "stop"}

from apps.g15app import G15App
from apps import *

arrow_right = [0, 0, 0, 0, 1, 0, 0, 0,
               0, 0, 0, 0, 0, 1, 1, 0,
               1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1,
               0, 0, 0, 0, 0, 1, 1, 0,
               0, 0, 0, 0, 1, 0, 0, 0]
arrow_left = list(reversed(arrow_right))

SOCK_ADDR = ('/tmp/g15mediadaemon.socket', 'AF_UNIX')

class G15MediaDaemon():
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('g15mediadaemon')

        if config.app is None:
            #is any app running?
            found = False
            for p in G15App.plugins:
                if p.is_running():
                    G15App.setPlugin(p.name)
                    found = True
                    break

            if not found:
                G15App.setPlugin(G15App.plugins[0].name)
        elif not G15App.setPlugin(config.app):
            self.logger.error("Could not find plugin %s" % config.app)

        self.recorder = xrecorder.XKeyRecorder(self.key_handler)

        self.g15 = None
        if not config.nog15:
            self.reconnect()

            self.lcd = LCDKeyWatcher(g15=self.g15)

    def reconnect(self):
        try:
            self.g15 = g15daemon.g15screen(g15daemon.SCREEN_PIXEL)
            self.g15.display()
            self.g15.request_key_handler()
        except ConnectionRefusedError as e:
            self.g15 = None

    def handleRPCMessage(self, msg):
        msg = msg.lower()
        if msg == "next":
            G15App.nextPlugin()
        elif msg == "previous":
            G15App.previousPlugin()
        elif msg.startswith("app="):
            G15App.setPlugin(msg[4:])
        elif msg == "stop":
            self.stop()

    def run(self):
        self.stopped = False
        pidpath = os.path.join(self.config.userdir, "g15mediadaemon.pid")
        pid = os.getpid()
        with open(pidpath, "w") as pidfile:
            pidfile.write(str(pid))

        if not self.config.nog15:
            self.lcd.start()

        self.recorder.start()

        try:
            self.listener = Listener(*SOCK_ADDR)
        except Exception:
            os.remove(SOCK_ADDR[0])
            self.listener = Listener(*SOCK_ADDR)
        self.listener._listener._socket.settimeout(1)

        while not self.stopped:
            try:
                try:
                    con = self.listener.accept()
                    msg = con.recv()
                    self.handleRPCMessage(msg)
                    con.close()
                except socket.timeout:
                    pass

                if not self.config.nog15:
                    self.timer_tick()
                    time.sleep(int(self.config.tick) / 1000)
            except KeyboardInterrupt:
                self.logger.info("KeyboardInterrupt")
                self.stop()
                os.remove(pidpath)
                return
            except:
                self.logger.error("Error in mainthread: %s" % sys.exc_info())

    def stop(self):
        self.stopped = True
        if not self.config.nog15:
            self.g15.close()
            self.lcd.stop()

        self.recorder.stop()

        if not self.config.nog15:
            self.lcd.join()

        self.recorder.join()

        self.config.app = G15App.activePlugin().name
        self.config.save()

    def key_handler(self, keycode):
        if keycode in ACTIONS:
            try:
                getattr(G15App.activePlugin(), ACTIONS[keycode])()
            except Exception:
                self.logger.error("Error in plugin action %s in plugin %s: %s" % (ACTIONS[keycode], G15App.activePlugin().name, sys.exc_info()))

    def timer_tick(self):
        if not self.g15:
            self.reconnect()

        try:
            self.g15.clear()
            self.g15.render_string(time.strftime("%a %d. %b %H:%M:%S"), 0, g15daemon.G15_TEXT_LARGE, 0, 0)
            self.g15.render_string(G15App.activePlugin().name, 1, g15daemon.G15_TEXT_LARGE, 0, 0)

            if G15App.pluginCount() > 1:
                self.g15.pixel_overlay(12, 35, 8, 6, arrow_left)
                self.g15.pixel_overlay(42, 35, 8, 6, arrow_right)

            if G15App.activePlugin().has_l3action():
                self.g15.pixel_overlay(106, 35, 8, 6, G15App.activePlugin().l3pixeloverlay())

            try:
                G15App.activePlugin().tick(self.g15)
            except Exception:
                self.logger.error("Error in timerevent in plugin %s: %s" % (G15App.activePlugin().name, sys.exc_info()))
                pass
            finally:
                self.g15.display()
        except BrokenPipeError as e:
            self.reconnect()

        return True


def getUserDir():
    path = os.path.join(os.getenv("HOME"), ".g15mediadaemon")

    if not os.path.exists(path):
        os.mkdir(path)

    return path


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-a", "--app", action="store", dest="app", help="App to start with")
    parser.add_option("-t", "--tick", action="store", dest="tick", default="500", help="Ticks to update the lcd in ms")
    parser.add_option("-l", "--list-apps", action="store_true", dest="list", help="List all available apps")
    parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Enable debug logging")
    parser.add_option("--no-g15", action="store_true", dest="nog15", help="Disable all g15 features and just listen to keys on XServer")
    parser.add_option("-n", "--next", action="store_true", dest="next", help="Switch to next app")
    parser.add_option("-p", "--previous", action="store_true", dest="previous", help="Switch to the previous app")
    parser.add_option("-s", "--stop", action="store_true", dest="stop", help="Stop the daemon and shutdown")

    (options, args) = parser.parse_args()

    try:
        # if we are the server (no g15mediadaemon running), this will throw
        rpcclient = Client(*SOCK_ADDR)
        if options.stop:
            rpcclient.send("stop")
        elif options.next:
            rpcclient.send("next")
        elif options.previous:
            rpcclient.send("previous")
        elif options.app != "":
            rpcclient.send("app=%s" % options.app)
        sys.exit(0)
    except Exception:
        pass

    if options.list:
        print("Available apps:")
        for p in G15App.plugins:
            print("  %s" % p.name)

        sys.exit(0)

    logger = logging.getLogger('g15mediadaemon')
    streamlogger = logging.StreamHandler()
    logger.addHandler(streamlogger)
    if options.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    try:
        userdir = getUserDir()
        logger.debug("Using userdir %s" % userdir)
    except Exception:
        logger.error("Error getting userdir: %s" % sys.exc_info())
        sys.exit(1)

    filelogger = logging.FileHandler(os.path.join(userdir, "g15mediadaemon.log"))
    logger.addHandler(filelogger)

    if len(G15App.plugins) == 0:
        logger.info("No plugins available, exiting")
        sys.exit(0)

    config = AppConfig(userdir, options)

    daemon = G15MediaDaemon(config)
    daemon.run()
