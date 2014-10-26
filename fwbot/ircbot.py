import irc.bot
import random

class IrcListener(irc.bot.SingleServerIRCBot):
    def __init__(self, wpool, chan, nick, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server,port)],nick,nick)
        self.chan = chan
        self.wpool = wpool

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self,c,e):
        print 'welcomed!'
        c.join(self.chan)

    def msg_channel(self,c,msg):
        if len(msg) > 512:
            for chunk in self.chunk_msg(msg):
                c.privmsg(self.chan,chunk)
        else:
            c.privmsg(self.chan,msg)

    def chunk_msg(self,msg,chunksize=511):
        for i in xrange(0,len(msg),chunksize):
            yield msg[i:i+chunksize]

    def on_pubmsg(self,c,e):
        a = e.arguments[0].split(":",1)
        if len(a) > 1 and a[0].lower() == self.connection.get_nickname().lower():
            self.do_command(c, e, a[1].strip())

    def _error(self,c,acc):
        self.msg_channel(c,'could not find account %s' % acc)

    def _exec(self, f, c, n):
        try:
            f()
        except KeyError:
            self._error(c,n)

    def do_command(self, c, e, cmd):
        cmd = cmd.split(" ")
        cmdname = cmd[0]
        cmdargs = cmd[1:]
        executed = False

        ### Twitter ###
        if cmdname == 'tweet': # tweet
            acc = cmdargs[0]
            msg = ' '.join(cmdargs[1:])
            try:
                self.wpool.manual[acc].make_tweet(msg)
            except KeyError:
                try:
                    self.wpool.auto[acc].make_tweet(msg)
                except ValueError:
                    self.msg_channel(c,'could not find account %s' % acc)
            executed = True

        if cmdname == 'fbranch': # friend branch
            acc = cmdargs[0]
            if acc in self.wpool.manual:
                self._exec(lambda:self.wpool.manual[acc].friend_branch(),c,acc)
            elif acc in self.wpool.auto:
                self._exec(lambda:self.wpool.auto[acc].friend_branch(),c,acc)
            executed = True

        if cmdname == 'copycat': # copycat tweet
            acc = cmdargs[0]
            if len(cmdargs) > 1:
                self._exec(lambda:self.wpool.auto[acc].copycat_tweet(self.wpool.manual[cmdargs[1]]),c,acc)
            else:
                self._exec(lambda:self.wpool.auto[acc].copycat_tweet(random.choice(self.wpool.manual.values())),c,acc)
            executed = True

        if cmdname == 'rtl': # retweet last
            acc = cmdargs[0]
            self._exec(lambda:self.wpool.auto[acc].retweet_last(random.choice(self.wpool.manual.values()).name),c,acc)
            executed = True

        if cmdname == 'dmall': # dm all followers
            acc = cmdargs[0]
            msg = ' '.join(cmdargs[1:])
            try:
                self.wpool.manual[acc].dm_followers(msg)
            except KeyError:
                try:
                    self.wpool.auto[acc].dm_followers(msg)
                except ValueError:
                    self.msg_channel(c, 'could not find account %s' % acc)
            executed = True

        ### Instagram ###
        if cmdname == 'follow': # follow
            acc = cmdargs[0]
            target = cmdargs[1]
            self._exec(lambda:self.wpool.insta[acc].follow(target))
            executed = True

        if cmdname == 'folbranch': # follow
            acc = cmdargs[0]
            self._exec(lambda:self.wpool.insta[acc].follow_branch(),c,acc)
            executed = True

        if cmdname == 'dolikes': # like popular stuff
            acc = cmdargs[0]
            self._exec(lambda:self.wpool.insta[acc].like_popular(),c,acc)
            executed = True

        if cmdname == 'likefriend': # likes a friend's post
            acc = cmdargs[0]
            self._exec(lambda:self.wpool.insta[acc].like_friend(),c,acc)
            executed = True


        if executed:
            c.privmsg(self.chan,"ok")
