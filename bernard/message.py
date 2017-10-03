print("Importing... %s" % __name__)

from . import config
from . import common
from . import discord
from . import database
from . import auditing
from . import analytics

@discord.bot.event
async def on_message(message):
	msgProcessStart = analytics.getEventTime()
	#only reply to the guild set in config file
	if common.isDiscordMainServer(message.server.id) is not True:
		return

	#package the message as a json object, add to a redis DB and set it to expire to anti-spam calculations
	database.rds.set(message.channel.id +":"+ message.id, common.packageMessageToQueue(message))
	database.rds.expire(message.channel.id +":"+ message.id, 360)

	#handoff the message to a function dedicated to its feature see also https://www.youtube.com/watch?v=ekP0LQEsUh0
	await auditing.attachments(message) #message attachment auditing

	#print the message to the console
	print("Channel: {0.channel} User: {0.author} (ID:{0.author.id}) Message: {0.content}".format(message))

	#handle message processing per rate limit
	if analytics.rateLimitAllowProcessing(message):
		await discord.bot.process_commands(message)

	#set the rate limit
	if message.author.id == discord.bot.user.id:
		analytics.rateLimitNewMessage(message.channel.id, analytics.getEventTime())

	#message processing timings
	analytics.onMessageProcessTime(msgProcessStart, analytics.getEventTime())