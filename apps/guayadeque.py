import dbus
from dbus import Interface
from dbus.mainloop.glib import DBusGMainLoop
from dbus import DBusException

from .g15app import G15App

import subprocess

import g15daemon


class GuayadequeApp(G15App):
    def __init__(self):
        self.lastpid = -1
        self.proxy = None
        self.player = None

    @property
    def name(self):
        return "guayadeque"

    def _get_iface(self):
        try:
            self.proxy = dbus.SessionBus().get_object('org.mpris.guayadeque', '/Player')
            self.player = dbus.Interface(self.proxy, dbus_interface='org.freedesktop.MediaPlayer')
        except DBusException:
            self.proxy = None
            self.player = None

    def is_running(self):
        s = subprocess.Popen(["ps cxo pid,command --sort=start_time | grep guayadeque | grep -v \<defunct\>"], shell=True,
                             stdout=subprocess.PIPE)

        for line in s.stdout:
            if self.lastpid != line or self.player is None:
                self.lastpid = line
                self._get_iface()

            return True

        self.lastpid = -1
        self.proxy = None
        self.player = None
        return False

    def get_metadata(self):
        return self.player.GetMetadata()

    def tick(self, g15):
        if self.is_running():
            position = self.player.PositionGet() * 1000
            md = self.get_metadata()

            g15.render_string("%s - %s" % (md['artist'][0], md['title']), 2, g15daemon.G15_TEXT_LARGE, 0, 0, True)
            g15.render_string("%s / %s" % (self.formatTime(position), self.formatTime(md['mtime'])), 3, g15daemon.G15_TEXT_LARGE, 0, 0)
        else:
            g15.render_string("not running", 2, g15daemon.G15_TEXT_LARGE, 0, 0)

    def start(self):
        subprocess.Popen("/usr/bin/guayadeque", shell=True)

    def play_pause(self):
        if self.is_running():
            self.player.Pause()
        else:
            self.start()

    def stop(self):
        if self.is_running():
            self.player.Stop()

    def next(self):
        if self.is_running():
            self.player.Next()

    def previous(self):
        if self.is_running():
            self.player.Prev()

    def volume_down(self):
        if self.is_running():
            nextvol = max(0, self.player.VolumeGet() -1)
            self.player.VolumeSet(nextvol)

    def volume_up(self):
        if self.is_running():
            nextvol = min(100, self.player.VolumeGet() +1)
            self.player.VolumeSet(nextvol)
