from base_subapp import Subapp
from worker import WorkerPool

import os

def get_subapp():
    class WorkSubapp(Subapp):
        def parse(self):
            parser = Subapp.parse(self)
            parser.add_argument("queue", help="The name of the queue to bind to")
            parser.add_argument("routes", nargs="+", help="A list of workers to create, by route name")
            return parser.parse_args()
        def _run(self):
            pid = os.fork()
            if pid == 0:
                with WorkerPool(self.args.queue, self.args.routes) as pool:
                    pool.listen()

    return WorkSubapp()
