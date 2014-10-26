from TwitterAPI import TwitterAPI
from pymongo import MongoClient
from bs4 import BeautifulSoup
from datetime import datetime
from instagram.client import InstagramAPI
import random
import syslog_func
import json
import requests
import subprocess

TEAM = 'failwhale'
TARGET_UNIV = 'Georgia Tech'

POSITIVE = ['wow',
        'incredible',
        'very impressive',
        'nice',
        'love it']

db = MongoClient('localhost:27017').fwbots

class Account(object):
    def __init__(self, api):
        self.api = api
    def log(self,network,action,details):
        syslog_func.log_bot(self.name,self.uid,TEAM,TARGET_UNIV,network,action,details)

class TwitterAccount(Account):
    def __init__(self, con_key=None, con_sec=None, acc_key=None, acc_sec=None,name=None,ty=None,**kwargs):
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
        self.api.request('statuses/retweet/:'+str(twid)+'.json',{'id':twid})

    # Retweet the last post by given user
    def retweet_last(self, un):
        self.log('auto-retweet',str(datetime.today())+','+str(un))
        tweets = json.loads(self.api.request('statuses/user_timeline',{'screen_name':un}).text)
        if len(tweets) > 0:
            self.retweet(tweets[0]['id'],auto=True)

    # Given another TwitterAccount object, make an 'inconspicuous' copycat tweet
    def copycat_tweet(self, autoacc):
        friend = autoacc.disjoint_friend(self.friends)
        self.log('copycat-tweet',str(datetime.today())+','+str(friend['screen_name']))
        tweets = json.loads(self.api.request('statuses/user_timeline',{'screen_name':friend['screen_name']}).text)
        if len(tweets) > 0:
            for t in tweets:
                e = t['entities']
                for tag in e['hashtags']:
                    self.notice_tag(tag)
                if len(e['user_mentions']) == 0: # don't start awkward conversations...
                    self.make_tweet(t['text'])
                    return t['text']

    def dm_followers(self,msg):
        uids = json.loads(self.api.request('followers/ids',{'screen_name':self.name}).text)['ids']
        for uid in uids:
            self.log('dm-user',str(datetime.today())+','+str(uid))
            self.api.request('direct_messages/new',{'user_id':uid,'text':msg})

class InstagramAccount(Account):
    def __init__(self, client_id=None,client_secret=None,redirect_url=None,access_token=None,name=None,ty=None,**kwargs):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect = redirect_url
        self.name = name
        self.ty = ty
        if access_token:
            self.access_token = access_token
            self.api = InstagramAPI(access_token=access_token)
        else:
            self.api = InstagramAPI(client_id=client_id,client_secret=client_secret,redirect_uri=redirect_url)
            url = self.api.get_authorize_login_url(scope=['basic','likes','comments','relationships'])
            print 'This account needs to be authenticated. Visit this url:'
            print url
            code = raw_input('Please enter the result code:').strip()
            self.access_token, user_info = self.api.exchange_code_for_access_token(code)
            db.instagram.update({'name':self.name},{'$set':{'access_token':self.access_token}})
            self.api = InstagramAPI(access_token = access_token)
        self.uid = self._get_uid(self.name)

    def log(self,action,details):
        Account.log(self,'instagram',action,details)

    # Pick a popular thing and like it.
    def like_popular(self):
        self.log("like-popular",str(datetime.today()))
        popular = self.api.media_popular(count='20')
        for i in xrange(8):
            p = random.choice(popular)
            self.api.like_media(p.id)

    # Follow someone.
    def follow(self,un):
        uid = self._get_uid(un)
        # Bug in the official API call for this one. Needs direct HTTP
        payload = {'ACCESS_TOKEN':self.access_token,'action':'follow'}
        r = requests.post('https://api.instagram.com/v1/users/'+uid+'/relationship?access_token='+self.access_token,data=payload)
        return r

    # Follow a friend of a friend.
    def follow_branch(self):
        friends = self.api.user_follows(self.uid)
        f = random.choice(friends[0])
        other_friends = self.api.user_follows(f.id)
        f2 = random.choice(other_friends[0])
        self.log("follow-branch",str(datetime.today())+','+f2.username)
        self.follow(f2.username)
        return f2

    # make a generic comment
    # for now these comments are just positive
    def generic_comment_friend(self):
        #1. pick a friend
        friends = self.api.user_follows(self.uid)[0]
        f = random.choice(friends)

        #2. pick a dumb comment
        comment = random.choice(POSITIVE)

        #3. pick something they posted
        recent = self.api.user_recent_media(f.id)
        print recent
        post = random.choice(recent)
        self.log("generic-comment-friend",str(datetime.today())+','+str(post)+','+str(comment))

        #4. make a dumb comment on their dumb post
        self.api.create_media_comment(post.id,comment)

        return (post,comment)

    def generic_comment_feed(self):
        comment = random.choice(POSITIVE)
        post = random.choice(self.api.user_media_feed()[0])
        self.log("generic-comment-friend",str(datetime.today())+','+str(post)+','+str(comment))
        self.api.create_media_comment(post.id,comment)

    # like something a friend posted recently
    def like_friend(self):
        friends = self.api.user_follows(self.uid)[0]
        f = random.choice(friends)

        recent = self.api.user_recent_media(user_id=f.id,count=20)
        self.log("like-friends-post",str(datetime.today())+','+f.username)
        post = random.choice(recent[0])
        self.api.like_media(post.id)
        return post

    # Helper to turn a username into a user id
    def _get_uid(self,un):
        uid = self.api.user_search(q=un)
        uid = uid[0]
        uid = uid.id
        return uid

def get_twitter_account(name):
    twitter_coll = db.twitter
    acc = twitter_coll.find_one({'name':name})
    del acc['_id']
    del acc['pw']
    if not acc:
        raise NameError("%s is not an existing bot name"%name)
    return TwitterAccount(**acc)

def get_instagram_account(name):
    ig_coll = db.instagram
    acc = ig_coll.find_one({'name':name})
    if not acc:
        raise NameError("%s is not an existing bot name"%name)
    return InstagramAccount(**acc)
