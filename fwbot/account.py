from TwitterAPI import TwitterAPI
from pymongo import MongoClient
from bs4 import BeautifulSoup
from datetime import datetime
import random
import syslog_func
import json
import requests

TEAM = 'failwhale'
TARGET_UNIV = 'Georgia Tech'

class Account(object):
    def __init__(self, api):
        self.api = api
    def log(self,network,action,details):
        syslog_func.log_bot(self.name,self.uid,TEAM,TARGET_UNIV,network,action,details)

class TwitterAccount(Account):
    def __init__(self, con_key=None, con_sec=None, acc_key=None, acc_sec=None,name=None,ty=None):
        Account.__init__(self,TwitterAPI(con_key,con_sec,acc_key,acc_sec))
        self.ck = con_key
        self.cs = con_sec
        self.ak = acc_key
        self._as = acc_sec
        self.name = name

        soup = BeautifulSoup(requests.get('http://gettwitterid.com',params={'user_name':self.name,'submit':'GET USER ID'}).text)
        self.uid = soup.find_all('td')[1].p.text
        self.ty = ty
        self._friends = None

    def log(self,action,details):
        Account.log(self,'twitter',action,details)

    def json(self):
        return {
            'con_key': self.ck,
            'con_sec': self.cs,
            'acc_key': self.ak,
            'acc_sec': self._as,
            'name': self.name,
            'ty':self.ty}

    @property
    def friends(self):
        if self._friends is None:
            self._friends = self.api.request('friends/list',{'screen_name':self.name})
            self._friends = json.loads(self._friends.text)['users']
        return self._friends

    # Post a single tweet.
    def make_tweet(self, msg):
        self.log("tweet",str(datetime.today())+',"'+msg+'"')
        self.api.request('statuses/update',{'status': msg})

    # Pick a friend of a friend and follow them.
    def friend_branch(self):
        friends = self.friends
        if len(friends) > 0:
            uname = random.choice(friends)['screen_name']
            other_friends = json.loads(self.api.request('friends/list',{'screen_name':uname}).text)['users']
            djf = self.disjoint_friend(other_friends)['screen_name']
            self.log("make friends",str(datetime.today())+','+djf)
            friend = self.api.request('friendships/create',{'screen_name':djf})
            print friend.text
            return uname

    # Pick a friend who isn't in other_friends.
    def disjoint_friend(self, other_friends,r=True):
        friends = self.friends
        if r:
            random.shuffle(friends)

        for f in other_friends:
            if f not in friends:
                return f

    # retweet the most recent thing from specified user
    def retweet(self, twid,auto=False):
        if not auto:
            self.log('retweet',str(datetime.today())+','+str(twid))
        self.api.request('statuses/retweet',{'id':twid})

    # Retweet the last post by given user
    def retweet_last(self, un):
        self.log('auto-retweet',str(datetime.today())+','+str(un))
        tweets = self.api.request('statuses/user_timeline',{'screen_name':un})
        if len(tweets) > 0:
            self.retweet(tweets[0]['id'],auto=True)

    # Given another TwitterAccount object, make an 'inconspicuous' copycat tweet
    def copycat_tweet(self, autoacc):
        friend = autoacc.disjoint_friend(self.friends)
        self.log('copycat-tweet',str(datetime.today())+','+str(friend['screen_name']))
        tweets = self.api.request('statuses/user_timeline',{'screen_name':friend['screen_name']})
        if len(tweets) > 0:
            for t in tweets:
                e = t['entities']
                for tag in e['hashtags']:
                    self.notice_tag(tag)
                if len(e['user_mentions']) == 0: # don't start awkward conversations...
                    self.make_tweet(t['text'])
                    return t['text']

def get_twitter_account(name):
    twitter_coll = MongoClient('localhost:27017').fwbots.twitter
    acc = twitter_coll.find_one({'name':name})
    del acc['_id']
    del acc['pw']
    if not acc:
        raise NameError("%s is not an existing bot name"%name)
    return TwitterAccount(**acc)
