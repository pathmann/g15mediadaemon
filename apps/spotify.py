import dbus
from dbus import Interface
from dbus.mainloop.glib import DBusGMainLoop
from dbus import DBusException

import re
import g15daemon

from pulsectl import Pulse

import subprocess

from .g15app import G15App


class SpotifyApp(G15App):
    def __init__(self):
        self.pulse = Pulse("g15mediadaemon-spotifyapp")
        self.lastpid = -1
        self.proxy = None
        self.player = None
        self.props = None
        self.sink = None

        if self.is_running():
            pass

    def _get_iface(self):
        try:
            self.proxy = dbus.SessionBus().get_object('org.mpris.MediaPlayer2.spotify', '/org/mpris/MediaPlayer2')
            self.player = dbus.Interface(self.proxy, dbus_interface='org.mpris.MediaPlayer2.Player')
            self.props = dbus.Interface(self.proxy, dbus_interface='org.freedesktop.DBus.Properties')
        except DBusException:
            self.proxy = None
            self.player = None
            self.props = None

        return True

    def _get_sink(self):
        if self.sink is None:
            for s in self.pulse.sink_input_list():
                if s.name.lower() == "spotify":
                    self.sink = s

    @property
    def name(self):
        return "spotify"

    def is_running(self):
        s = subprocess.Popen(["ps cxo pid,command --sort=start_time | grep spotify | grep -v \<defunct\>"], shell=True, stdout=subprocess.PIPE)

        for line in s.stdout:
            if self.lastpid != line or self.player is None or self.sink is None:
                self.lastpid = line
                self._get_iface()
                self._get_sink()

            return True

        self.lastpid = -1
        self.proxy = None
        self.player = None
        self.props = None
        return False

    def get_metadata(self):
        if self.is_running():
            md = self.props.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
            return {v[6:].lower(): md[v] for v in md}

        return {}

    def tick(self, g15):
        if self.is_running():
            position = self.props.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
            md = self.get_metadata()

            g15.render_string("%s - %s" % (md['artist'][0], md['title']), 2, g15daemon.G15_TEXT_LARGE, 0, 0, True)
            g15.render_string("%s / %s" % (position, self.formatTime(md['length'])), 3, g15daemon.G15_TEXT_LARGE, 0, 0)
        else:
            g15.render_string("not running", 2, g15daemon.G15_TEXT_LARGE, 0, 0)

    def start(self):
        subprocess.Popen("/usr/bin/spotify", shell=True)

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
        if self.is_running():
            self.player.Previous()

    def volume_down(self):
        if self.is_running():
            nextvol = max(0.0, self.sink.volume.value_flat - 0.1)
            self.pulse.volume_set_all_chans(self.sink, nextvol)

    def volume_up(self):
        if self.is_running():
            nextvol = min(1.0, self.sink.volume.value_flat + 0.1)
            self.pulse.volume_set_all_chans(self.sink, nextvol)
