# -*- coding: utf-8 -*-

from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

import time

default_cfg = {
    'backend': 'mongodb',
    'conn_url': 'localhost:27017',
    'dbname': 'fwbots'
}

class MongoDBPersister(object):
    def __init__(self,
                 conn_url='localhost:27017',
                 dbname='fwbots'):

        self.conn_url=conn_url
        self.dbname=dbname

        self.fwdb = MongoClient(conn_url)[dbname]
        self.access_collection = self.fwdb['access']
        self.jobs_collection = self.fwdb['jobs']
        self.worker_collection = self.fwdb['workers']
        self.result_collection = self.fwdb['result']
        
    ### Basic information ###

    def get_location(self):
        return self.conn_url + '/' + self.dbname

    def get_backend_type(self):
        return 'mongodb'

    def get_version(self):
        return self.fwdb.command({'buildInfo': 1})['version']

    ### Worker manipulation ###

    def add_worker(self, worker_id, host, port):
        self.worker_collection.insert({
            'worker_id': worker_id,
            'host': host,
            'port': port,
            'state': 'waiting'
            })

    def delete_worker(self, worker_id):
        self.worker_collection.remove(dict(worker_id=worker_id))

    def delete_monitor(self, host):
        self.worker_collection.remove({'monitor': 1, 'host': host})

    def set_working(self, worker_id):
        self.worker_collection.update(
                dict(worker_id=worker_id),
                {'$set': {
                    'state': 'working',
                    'start': datetime.utcnow()
                    }}, True)

    def unset_working(self, worker_id):
        self.worker_collection.update(
                dict(worker_id=worker_id),
                {'$set': {
                    'state': 'waiting',
                    }}, True)

    def get_all_workers(self):
        return [w for w in self.worker_collection.find()]

    def get_avail_workers(self):
        return [w for w in self.worker_collection.find({'state':'waiting'})]
