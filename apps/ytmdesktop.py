import dbus
from dbus import Interface
from dbus.mainloop.glib import DBusGMainLoop
from dbus import DBusException

from .g15app import G15App

import subprocess

import g15daemon

APP_PATH = "/home/thomas/Applications/ytmdesktop/run.sh"


class YoutubeMusicDesktopApp(G15App):
    def __init__(self):
        print("starting")

    @property
    def name(self):
        return "youtubemusicdesktop"

    def is_running(self):
        s = subprocess.Popen(["ps xo pid,command --sort=start_time | grep %s | grep -v \<defunct\>" % APP_PATH], shell=True,
                             stdout=subprocess.PIPE)

        for line in s.stdout:
            if b"grep" not in line:
                return True

        return False

    def tick(self, g15):
        if self.is_running():
            pass
        else:
            g15.render_string("not running", 2, g15daemon.G15_TEXT_LARGE, 0, 0)

    def start(self):
        subprocess.Popen(APP_PATH, shell=True)

    def play_pause(self):
        if not self.is_running():
            self.start()

    def stop(self):
        pass

    def next(self):
        pass

    def previous(self):
        pass

    def volume_down(self):
        pass

    def volume_up(self):
        pass
