from configparser import ConfigParser

import os

class AppConfig(object):
    def __init__(self, path, options):
        self.userdir = path
        self.path = os.path.join(path, "config.ini")
        self.sec = "g15mediadaemon"

        cfg = ConfigParser()
        cfg.read(self.path)

        if not cfg.has_section(self.sec):
            cfg.add_section(self.sec)

        #first, set options from config
        for op in cfg.options(self.sec):
            setattr(self, op, cfg.get(self.sec, op))

        #next, overwrite from optionparser
        for op, value in options.__dict__.items():
            if value is not None:
                setattr(self, op, value)
                cfg.set(self.sec, op, str(value))

        with open(self.path, "w") as f:
            cfg.write(f)

    def save(self):
        cfg = ConfigParser()
        cfg.add_section(self.sec)

        for op, value in self.__dict__.items():
            if value is not None and op not in ["sec", "userdir", "path"]:
                cfg.set(self.sec, op, value)

        with open(self.path, "w") as f:
            cfg.write(f)
