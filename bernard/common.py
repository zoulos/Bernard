print("Importing... %s" % __name__)
from . import config

import datetime
import time
import json

global config

bernardMessageProcessTimes = [] #def bernardMessageProcessTime(start, end):
bernardStartTimeSets = 0

def isDiscordBotOwner(id):
	return id == config.cfg['bernard']['owner']

def isDiscordAdministrator(roles):
	for role in roles:
		if role.id == config.cfg['bernard']['administrators']: return True

def datetimeObjectToString(timestamp):
	return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def bernardMessageProcessTime(start, end):
	global bernardMessageProcessTimes
	#pop the oldest in the array
	if len(bernardMessageProcessTimes) >= 20:
		bernardMessageProcessTimes.pop(0)
	bernardMessageProcessTimes.append(round(end - start, 3))

def bernardStartTimeSet():
	global bernardStartTimeSets
	bernardStartTimeSets = time.time()

def packageMessageToQueue(msg):
	msgDict = {
		"timestamp":datetimeObjectToString(msg.timestamp),
		"content":msg.content,
		"embeds":msg.embeds,
		"attachments":msg.attachments,
		"member": {
			"joined":datetimeObjectToString(msg.author.joined_at),
			"nick":msg.author.nick,
			"author": str(msg.author),
			"top_role":msg.author.top_role.id,
			},
		"scored":0,
		"score":0
	}
	msgToQueue = json.dumps(msgDict)
	return(msgToQueue)