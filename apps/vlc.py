import dbus
from dbus import Interface
from dbus.mainloop.glib import DBusGMainLoop
from dbus import DBusException

from .g15app import G15App

import subprocess

import g15daemon


class VLCApp(G15App):
    def __init__(self):
        self.lastpid = -1
        self.proxy = None
        self.player = None
        self.props = None

    @property
    def name(self):
        return "vlc"

    def _get_iface(self):
        try:
            self.proxy = dbus.SessionBus().get_object('org.mpris.MediaPlayer2.vlc', '/org/mpris/MediaPlayer2')
            self.player = dbus.Interface(self.proxy, dbus_interface='org.mpris.MediaPlayer2.Player')
            self.props = dbus.Interface(self.proxy, dbus_interface='org.freedesktop.DBus.Properties')
        except DBusException:
            self.proxy = None
            self.player = None
            self.props = None

    def is_running(self):
        s = subprocess.Popen(["ps cxo pid,command --sort=start_time | grep vlc | grep -v \<defunct\>"], shell=True,
                             stdout=subprocess.PIPE)

        for line in s.stdout:
            # should anyways loop only one time
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
        md = self.props.Get("org.mpris.MediaPlayer2.Player", "Metadata")
        return {v[v.index(':') + 1:].lower(): md[v] for v in md}

    def tick(self, g15):
        if self.is_running():
            position = self.props.Get("org.mpris.MediaPlayer2.Player", "Position")
            md = self.get_metadata()

            if "url" in md:
                g15.render_string(md['url'], 2, g15daemon.G15_TEXT_LARGE, 0, 0, True)
                g15.render_string("%s / %s" % (self.formatTime(position), self.formatTime(md['length'])), 3, g15daemon.G15_TEXT_LARGE, 0, 0)
            else:
                g15.render_string("no file loaded", 2, g15daemon.G15_TEXT_LARGE, 0, 0)
        else:
            g15.render_string("not running", 2, g15daemon.G15_TEXT_LARGE, 0, 0)

    def start(self):
        subprocess.Popen("/usr/bin/vlc", shell=True)

    def play_pause(self):
        if self.is_running():
            pass
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
            self.player.Previous()

    def volume_down(self):
        pass

    def volume_up(self):
        pass
