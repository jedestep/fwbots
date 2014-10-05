import argparse
from util import log

class Subapp(object):
    def __init__(self):
        self.args = None
        self.log = log.Logger('fwb')
    def run(self):
        self.args = self.parse()
        self._run()
    def parse(self):
        parser = argparse.ArgumentParser()
        # the subapp argument is still present i think, ignore it
        parser.add_argument("subapp")
        return parser
    def _run(self):
        pass
