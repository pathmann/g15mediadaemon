from threading import Thread

from Xlib import X, XK, display
from Xlib.ext import record
from Xlib.protocol import rq

class XKeyRecorder(Thread):
    def __init__(self, handler):
        if not 'record' in display.ext.__all__:
            raise Exception("XDisplay does not support record extension")

        super(XKeyRecorder, self).__init__()
        self.handler = handler

        self.localdp = display.Display()
        self.recorddp = display.Display()

        self.context = self.recorddp.record_create_context(
            0,
            [record.AllClients],
            [{
                'core_requests': (0, 0),
                'core_replies': (0, 0),
                'ext_requests': (0, 0, 0, 0),
                'ext_replies': (0, 0, 0, 0),
                'delivered_events': (0, 0),
                'device_events': (X.KeyPress, X.KeyPress),
                'errors': (0, 0),
                'client_started': False,
                'client_died': False,
            }]
        )

    def __del__(self):
        self.recorddp.record_free_context(self.context)

    def run(self):
        self.recorddp.record_enable_context(self.context, self.callback)

    def stop(self):
        self.localdp.record_disable_context(self.context)
        self.localdp.flush()

    @staticmethod
    def lookup_keysym(keysym):
        for name in dir(XK):
            if name[:3] == "XK_" and getattr(XK, name) == keysym:
                return name[3:]
        return "[%d]" % keysym

    def keycode_to_keysym(self, code):
        keysym = self.localdp.keycode_to_keysym(code, 0)
        if not keysym:
            return None
        else:
            return XKeyRecorder.lookup_keysym(keysym)

    def callback(self, reply):
        if reply.category != record.FromServer:
            return

        if reply.client_swapped:
            #received swapped protocol data, cowardly ignored
            return

        if not len(reply.data) or reply.data[0] < 2:
            # not an event
            return

        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(data, self.recorddp.display, None, None)

            if event.type in [X.KeyPress, X.KeyRelease]:
                pr = event.type == X.KeyPress and "Press" or "Release"

                self.handler(event.detail)
