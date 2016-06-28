import abc


class PluginMount(type):
    def __init__(cls, name, bases, attrs):
        super(PluginMount, cls).__init__(name, bases, attrs)
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
            cls._activePlugin = -1
        else:
            cls.plugins.append(cls())
            if cls._activePlugin == -1:
                cls._activePlugin = 0


class G15App(object, metaclass=PluginMount):
    @classmethod
    def pluginCount(cls):
        return len(cls.plugins)

    @classmethod
    def nextPlugin(cls):
        if len(cls.plugins) > 0:
            cls._activePlugin = (cls._activePlugin +1) % len(cls.plugins)

    @classmethod
    def previousPlugin(cls):
        if len(cls.plugins) > 0:
            cls._activePlugin = (cls._activePlugin -1) % len(cls.plugins)

    @classmethod
    def activePlugin(cls):
        if len(cls.plugins) > 0:
            return cls.plugins[cls._activePlugin]
        else:
            raise Exception()

    @classmethod
    def setPlugin(cls, name):
        for i, p in enumerate(cls.plugins):
            if p.name == name:
                cls._activePlugin = i
                return True

        return False

    @staticmethod
    def formatTime(msecs):
        secs = int(msecs / 1000000);
        mins = int(secs / 60);
        secs = secs % 60;
        hours = int(mins / 60);
        mins = mins % 60;
        days = int(hours / 24);
        hours = hours % 24;
        return "%s%s%s:%s" % (str(days).zfill(2) + ":" if days > 0 else "", str(hours).zfill(2) + ":" if hours > 0 else "", str(mins).zfill(2), str(secs).zfill(2))

    @abc.abstractproperty
    @property
    def name(self):
        return "__g15app__"

    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def is_running(self):
        return False

    @abc.abstractmethod
    def tick(self, g15):
        pass

    @abc.abstractmethod
    def play_pause(self):
        pass


    @abc.abstractmethod
    def stop(self):
        pass

    @abc.abstractmethod
    def next(self):
        pass

    @abc.abstractmethod
    def previous(self):
        pass

    @abc.abstractmethod
    def volume_down(self):
        pass

    @abc.abstractmethod
    def volume_up(self):
        pass

    def has_l3action(self):
        return False

    def l3action(self):
        pass

    def l3pixeloverlay(self):
        return list()

    def has_l4action(self):
        return False

    def l4action(self):
        pass

    def l4pixeloverlay(self):
        pass
