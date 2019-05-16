import dbus
from dbus import Interface
from dbus.mainloop.glib import DBusGMainLoop
from dbus import DBusException

import math

from .g15app import G15App

import subprocess

import g15daemon


class PithosApp(G15App):
    def __init__(self):
        self.lastpid = -1
        self.proxy = None
        self.player = None
        self.props = None

    @property
    def name(self):
        return "pithos"

    def _get_iface(self):
        try:
            self.proxy = dbus.SessionBus().get_object('org.mpris.MediaPlayer2.pithos', '/org/mpris/MediaPlayer2')
            self.player = dbus.Interface(self.proxy, dbus_interface='org.mpris.MediaPlayer2.Player')
            self.props = dbus.Interface(self.proxy, dbus_interface='org.freedesktop.DBus.Properties')
        except DBusException as e:
            self.proxy = None
            self.player = None
            self.props = None

    def is_running(self):
        s = subprocess.Popen(["ps cxo pid,command --sort=start_time | grep pithos | grep -v \<defunct\>"], shell=True,
                             stdout=subprocess.PIPE)

        for line in s.stdout:
            if self.lastpid != line or self.player is None:
                self.lastpid = line
                self._get_iface()

            return True

        self.lastpid = -1
        self.proxy = None
        self.player = None
        self.props = None
        return False

    def get_metadata(self):
        md = self.props.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        return {v[v.index(':') +1:].lower(): md[v] for v in md}

    def tick(self, g15):
        if self.is_running():
            position = self.props.Get('org.mpris.MediaPlayer2.Player', 'Position')
            md = self.get_metadata()

            g15.render_string("%s - %s" % (md['artist'][0], md['title']), 2, g15daemon.G15_TEXT_LARGE, 0, 0, True)
            g15.render_string("%s" % self.formatTime(position), 3, g15daemon.G15_TEXT_LARGE, 0, 0)
        else:
            g15.render_string("not running", 2, g15daemon.G15_TEXT_LARGE, 0, 0)

    def start(self):
        subprocess.Popen("/usr/bin/pithos", shell=True)

    def play_pause(self):
        if self.is_running():
            self.player.PlayPause()
        else:
            self.start()

    def stop(self):
        if self.is_running():
            self.player.Stop()

    def next(self):
        if self.is_running():
            self.player.Next()

    def previous(self):
        pass

    def volume_down(self):
        if self.is_running():
            nextvol = max(0.0, self.props.Get('org.mpris.MediaPlayer2.Player', 'Volume') - 0.1)
            self.props.Set('org.mpris.MediaPlayer2.Player', 'Volume', nextvol)

    def volume_up(self):
        if self.is_running():
            nextvol = min(1.0, self.props.Get('org.mpris.MediaPlayer2.Player', 'Volume') + 0.1)
            self.props.Set('org.mpris.MediaPlayer2.Player', 'Volume', nextvol)

    def has_l3action(self):
        return True

    def l3action(self):
        dbus.SessionBus().call_async("net.kevinmehall.Pithos", "/net/kevinmehall/Pithos", "net.kevinmehall.Pithos", "LoveCurrentSong", "", [], None, None)

    def l3pixeloverlay(self):
        return [
            0, 0, 0, 1, 0, 1, 0, 0,
            0, 0, 1, 0, 1, 0, 1, 0,
            0, 1, 0, 0, 0, 0, 0, 1,
            0, 0, 1, 0, 0, 0, 1, 0,
            0, 0, 0, 1, 0, 1, 0, 0,
            0, 0, 0, 0, 1, 0, 0, 0
        ]
