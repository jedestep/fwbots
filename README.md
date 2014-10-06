#FWBOTS
Delivering pumpkin spice lattes.

###Running bots
Since this is designed as a special purpose application that need not be extensible, a fair amount of information is hard coded. These bots will connect to ```#fwbots``` on ```irc.freenode.net```. You can start them as follows:
```bash
$ ./app.py work <bot_name> <account_names>
```

The account names are loaded from a Mongo database. At the moment this database needs to be manually populated with account information. The required information looks like this:

```python
 # twitter
{'name': 'hi',
 'acc_key': 'asdf',
 'acc_sec': 'asdf',
 'con_key': 'asdf',
 'con_sec': 'asdf',
 'ty': <'manual' | 'auto'>
}

 # instagram
{'name': 'hi',
 'client_id': 'asdf',
 'client_secret': 'asdf',
 'redirect_url': 'http://example.com', # needs to be a working url
 'ty': <'manual' | 'auto'>
}
```
Instagram accounts will be populated with a field called ```access_token``` when they auth the first time.
Anyway, a bot with the name <bot_name> will eventually join the IRC channel if it connects successfully (it may never connect. at the moment there is no timeout, it just hangs). You can address it to issue commands.
```
 # twitter
botname: tweet <name> <msg> # tweets msg from name's account
botname: fbranch <name> # causes name to become friends with a friend of a friend
botname: copycat <name> # makes a generic copycat tweet
botname: rtl <name> # retweets the last thing one of its friends posted

 # instagram
botname: folbranch <name> # follows a follower of a follower
botname: dolikes <name> # likes some things on the most popular list
botname: likefriend <name> # likes something that a random friend posted
```

It is simple to add additional functionality.

###Running the scheduler
```bash
$ ./app.py schedule
```
It will immediately launch a random action for every bot, then schedule additional actions for some random time between 30 minutes and 4 hours in the future. Right now its timing behaviors are very simple; all bots act at the same time and regardless of wall clock time. This is planned for improvement to make the bots more realistic.

If the scheduler needs to be stopped, cleanup can be messy. Due to an unresolved issue with the ```KillableTimer``` class, it does not die as cleanly as others and will probably require a ```kill -9``` to stop.
