# -*- coding: utf-8 -*-
from persistence import get_backend
from util.log import Logger
from util.thread import KillableThread, TriggeredInterrupt

from account import get_twitter_account,get_instagram_account
from ircbot import IrcListener

from time import sleep

import signal
import sys
import os
import socket
import traceback
import random

import json
import logging

class Worker(object):
    def __init__(self, queue_name, route, persister, wnum, port,
            logfile=sys.stdout):
        self.queue_name = queue_name
        self.route = route
        self.persister = persister
        self.stop = False
        self.pid = os.getpid()
        self.worker_id = '-'.join(['worker', str(wnum), queue_name, route, str(self.pid)])
        self.log = Logger(self.worker_id,logfile=logfile, loglevel=logging.DEBUG)
        self.log.info("starting")

        self.host = socket.gethostbyname(socket.gethostname())
        self.port = port
        self.register()
        self.todo = None
        self.stop = False

    def register(self):
        self.persister.add_worker(self.worker_id, self.host, self.port)

    def unregister(self):
        self.persister.delete_worker(self.worker_id)

    def start_worker(self):
        while not self.stop:
            if self.todo:
                yield self.work(self.todo)
                self.todo = None

    def stop_worker(self):
        self.log.info("shutting down")
        self.unregister()
        self.stop = True

    def work(self, f):
        self.persister.set_working()
        ret = f()
        self.persister.unset_working()
        return ret

class WorkerPool(object):
    def __init__(self, queue_name, routing_keys=None,
            backend='mongodb', conn_url='localhost:27017',
            dbname='fwbots', logfile=sys.stdout,
            pidfile=None):
        """
        routing_keys are a required parameter to specify an n-length list
        of routing keys, which will each be assigned to one worker

        FWBOTS: we are using routing_keys as the account names to load
        """
        self.stop = False
        self.name = queue_name
        self.log = Logger('pool-'+queue_name, logfile=logfile)
        self.persister = get_backend(backend)(conn_url,dbname)

        self.port = -1 # too lazy to actually remove this

        self.workers = {}
        self.manual = {}
        self.auto = {}
        self.insta = {}

        if pidfile:
            self.log.info("writing to pidfile %s" % pidfile)
            with open(pidfile) as f:
                f.write(str(self.pid))
                f.close()

        # TODO this needs to be in shared memory
        wnums = {}

        self.ircbot = IrcListener(self,"#fwbots",self.name,"irc.freenode.net")

        for key in routing_keys:
            errnum = 0
            try:
                acc = get_twitter_account(key)
                if acc.ty == 'auto':
                    self.log.info('found auto for %s' % key)
                    self.auto[acc.name] = acc
                # if there are multiple manual accs defined, pick only the last one
                elif acc.ty == 'manual':
                    self.log.info('found manual for %s' % key)
                    self.manual[acc.name] = acc
            except NameError:
                errnum += 1
            try:
                acc = get_instagram_account(key)
                self.insta[acc.name] = acc
            except NameError:
                errnum += 1
            if errnum > 1:
                self.log.warn("Could not find any account called %s"%key)

            if key not in wnums:
                wnums[key] = 0
            wnums[key] += 1
            worker = Worker(queue_name, key,
                    self.persister, wnums[key], self.port, logfile)

            thread = KillableThread(target=worker.start_worker)
            thread.start()
            self.workers[worker.worker_id] = (worker, thread)
        # lastly, register yourself
        self.persister.add_pool(self)

    def __enter__(self, *args, **kwargs):
        self.log.info("starting")
        def gentle(signum, frame):
            self.log.info("Received gentle shutdown signal %d" % signum)
            self.shutdown()
            sys.exit(0)
        def rough(signum, frame):
            self.log.warn("Received non-gentle kill signal %d" % signum)
            self.die()
            sys.exit(0)

        signal.signal(signal.SIGINT,  rough )
        signal.signal(signal.SIGHUP,  gentle)
        signal.signal(signal.SIGTERM, gentle)
        signal.signal(signal.SIGALRM, gentle)
        signal.signal(signal.SIGQUIT, gentle)
        return self

    def __exit__(self, *args, **kwargs):
        self.shutdown()

    def shutdown(self):
        for _id in self.workers.keys():
            worker = self.workers[_id]
            worker[0].stop_worker()
            del self.workers[_id]
        self.stop = True
        self.persister.delete_pool(self.name)

    def die(self):
        for _id in self.workers.keys():
            worker = self.workers[_id]
            try:
                worker[1].raise_exc(TriggeredInterrupt)
                self.log.warn("raised an exception in %s" % str(_id))
                del self.workers[_id]
            except ValueError: # it was dead already
                self.log.debug("ignored killing thread %s" % str(_id))
                continue
        self.stop = True

    def work(self, f):
        w = self.persister.get_avail_workers()[0]
        w.todo = f

    def run_cmd(self, terminate=None, kill=None, suicide=None,
            tweet=None,rtp=None):
        # requests a termination
        # terminate looks like: <worker_id>
        if terminate:
            self.workers[terminate][0].stop_worker()
            del self.workers[terminate]

        # performs a hard kill
        # kill looks like: <worker_id> 
        if kill:
            try:
                self.workers[kill][1].raise_exc(TriggeredInterrupt)
                del self.workers[kill]
            except ValueError: # it was already dead
                self.log.warn("tried to kill a thread when it was dead already")

        # shuts down the entire pool
        # suicide looks like: 1 
        if suicide == 1:
            self.stop = True

        # sends a tweet from self.manual
        # tweet looks like: <msg>
        if tweet:
            self.log.info("tweeting with manual account %s: '%s'"%(self.manual.name,tweet))
            self.work(lambda: self.manual.make_tweet(tweet))
            # if rtp is set, have dummies retweet it with probability rtp
            if rtp:
                def f():
                    for a in self.auto:
                        if rtp < random.random():
                            a.retweet_last(self.manual.name)
                self.work(f)

    def listen(self):
        self.ircbot.start()
