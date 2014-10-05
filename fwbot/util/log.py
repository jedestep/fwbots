import logging
import sys

"""Wrapper around logging."""
class Logger(object):
    def __init__(self, name, logfile=sys.stdout, loglevel=logging.INFO):
        self._log = logging.getLogger(name)
        so = None
        if isinstance(logfile, basestring):
            so = logging.FileHandler(logfile)
        else:
            so = logging.StreamHandler(logfile)
        so.setFormatter(
            logging.Formatter('[%(levelname)s] %(asctime)s %(name)s: %(message)s'))
        self._log.addHandler(so)
        self._log.setLevel(loglevel)

    def set_level(self, level):
        self._log.setLevel(level)

    def error(self, msg):
        self._log.error(msg)
    def warn(self, msg):
        self._log.warn(msg)
    def info(self, msg):
        self._log.info(msg)
    def debug(self, msg):
        self._log.debug(msg)
