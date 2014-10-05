import syslog
teamname = ''
syslog.openlog(teamname)

# bot_name is the useraccount/handle of the bot
# uid is the network_id of the bot on that network
# network is the social network
# action_name is what the bot did (tweet, post, friend, follow, retweet)
# details is body of post, tweet or any extra details you want to add
def log_bot(bot_name, uid, team_name, target_university, network, action_name, details):
	syslog.syslog(syslog.LOG_INFO, 
		'%s,%s,%s,%s,%s,%s,%s' % (network, uid, team_name, target_university, bot_name, action_name, details))