from base_subapp import Subapp
from schedbot import IrcScheduler
from persistence import get_backend

import os

def get_subapp():
    class ScheduleSubapp(Subapp):
        def __init__(self,conn_url='localhost:27017',dbname='fwbots'):
            Subapp.__init__(self)
            self.persister = get_backend('mongodb')(conn_url,dbname)
        def parse(self):
            parser = Subapp.parse(self)
            # no additional args
            return parser.parse_args()
        def _run(self):
            bots = self.persister.get_all_pools()
            pid = os.fork()
            if pid == 0:
                IrcScheduler(bots)
    return ScheduleSubapp()
