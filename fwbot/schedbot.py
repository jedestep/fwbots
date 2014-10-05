import irc.bot
import random
from threading import Timer
from datetime import timedelta

#bots format:
#{'name': {'manual':[names...],'auto':[names...]}}

'''Schedules the copycat tweets for automated bots'''
class IrcScheduler(irc.bot.SingleServerIRCBot):
    def __init__(self, bots, chan='#fwbots', nick='fwscheduler', server='irc.freenode.net', port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server,port)],nick,nick)
        self.chan = chan
        self.bots = bots
        self.stop = False
        self.threads = []
        """launch a tweet from each auto bot"""
        try:
            self.start()
        except:
            print 'connecting didn\'t work, giving up :('
            for t in self.threads:
                t.cancel()

    def on_welcome(self,c,e):
        print 'welcomed!'
        c.join(self.chan)

    def on_pubmsg(self,c,e):
        a = e.arguments[0].split(":",1)
        if len(a) > 1 and a[0].lower() == self.connection.get_nickname().lower():
            cmd = a[1].strip().split(" ")
            if cmd[0] == 'go':
                for n,b in self.bots.iteritems():
                    for autoname in b['auto']:
                        self.rand_action_repeat(n,autoname)

    def rand_action_repeat(self,botname,accname):
        n = random.randint(0,2)
        if n == 0: # retweet last
            self.msg(botname,accname,'rtl')
        elif n == 1: # copycat tweet
            self.msg(botname,accname,'copycat',args=random.choice(self.bots[botname]['manual']))
        elif n == 2: # friend branch
            self.msg(botname,accname,'fbranch')
        tm = 60*random.randint(30,240)
        t = Timer(tm,self.rand_action_repeat,args=(botname,accname))
        print 'launching in %s minutes' % (tm/60)
        try:
            t.start()
        except KeyboardInterrupt:
            t.cancel()
        print 'exiting rand_action_repeat'

    def msg(self,botname,accname,cmdname,args=None):
        s = '{0}:{1} {2}'.format(botname,cmdname,accname)
        if args:
            s += ' {0}'.format(args)
        self.connection.privmsg(self.chan,s)

