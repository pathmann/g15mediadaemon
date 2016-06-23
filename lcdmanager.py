from threading import Thread

import g15daemon

from apps.g15app import G15App
from apps import *

class LCDKeyWatcher(Thread):
    def __init__(self, g15):
        super(LCDKeyWatcher, self).__init__()

        self._keys = 0
        self.g15 = g15
        self.stop_thread = False

    def run(self):
        while not self.stop_thread:
            key = self.g15.get_key()
            if key is not None:
                changed = self._keys ^ key
                pressed = self._keys
                self._keys = key

                if pressed:
                    if not key & g15daemon.G15_KEY_LIGHT:
                        if changed & g15daemon.G15_KEY_L2:
                            G15App.previousPlugin()
                        elif changed & g15daemon.G15_KEY_L3:
                            G15App.nextPlugin()
                        elif changed & g15daemon.G15_KEY_L4 and G15App.activePlugin().has_l3action():
                            G15App.activePlugin().l3action()
                        elif changed & g15daemon.G15_KEY_L5 and G15App.activePlugin().has_l4action():
                            G15App.activePlugin().l4action()

    def stop(self):
        self.stop_thread = True
