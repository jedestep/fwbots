#!/usr/bin/env python
import cli.work as work
import cli.schedule as schedule
import sys

if __name__ == '__main__':
    subapp = globals()[sys.argv[1]].get_subapp()
    subapp.run()
