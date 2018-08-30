import bernard.config as config
import bernard.common as common
#import bernard.redundancy as redundancy
import bernard.discord as discord
import bernard.auditing as auditing
import bernard.analytics as analytics
import bernard.antispam as antispam
import logging

logger = logging.getLogger(__name__)
logger.info("loading...")

@discord.bot.event
async def on_message(message):
	msgProcessStart = analytics.getEventTime()
	#only reply to the guild set in config file
	try:
		if common.isDiscordMainServer(message.server) is not True:
			await discord.bot.process_commands(message)
			return
	except AttributeError: #process messages anyway
		await discord.bot.process_commands(message)
		return

	#scan the message for spammy content
	antispam_obj = antispam.antispam_auditor(message)
	antispam_obj.score()

	#get some basic stats of message sending
	analytics.setMessageCounter(message)

	#handoff the message to a function dedicated to its feature see also https://www.youtube.com/watch?v=ekP0LQEsUh0 DO NOT AUDIT OURSELVES BAD THINGS HAPPEN
	if message.author.id != discord.bot.user.id:
		await auditing.attachments(message) #message attachment auditing
		await auditing.discord_invites(message) #discord invites
		await auditing.blacklisted_domains(message) #url blacklisting

	#print the message to the console
	if config.cfg['bernard']['debug']:
		logger.info("Channel: {0.channel} User: {0.author} (ID:{0.author.id}) Message: {0.content}".format(message))

	#handle message processing per rate limit, do not reply to ourselves
	if analytics.rateLimitAllowProcessing(message):
		if message.author.id != discord.bot.user.id:
			await discord.bot.process_commands(message)

	#set the rate limit
	if message.author.id == discord.bot.user.id:
		analytics.rateLimitNewMessage(message.channel.id, analytics.getEventTime())

	#handle high availibity checks
	if config.cfg['redundancy']['enable']:
		#if we see our own UUID in the mod room, check our partner status to make sure we didnt get demoted
		if config.cfg['redundancy']['self_uid'] in message.content:
			status = redundancy.get_partner_status(config.cfg['redundancy']['self_uid'])
			if status['current_state'] == "FAILING_PRIMARY":
				await discord.bot.send_message(discord.mod_channel(),"<@{0}> CRITCAL (Primary): Secondary server started but the primary is still running! Setting secondary to FAILED_SECONDARY.".format(config.cfg['bernard']['owner']))
				await discord.bot.send_message(discord.mod_channel(), "CRITICAL (Primary): Secondary server {0} is expected to shut down.".format(config.cfg['redundancy']['partner_uid']))
				redundancy.update_status("RUNNING_MASTER", config.cfg['redundancy']['self_uid'])
				redundancy.update_status("FAILING_SECONDARY", config.cfg['redundancy']['partner_uid'])
			elif status['current_state'] == "RUNNING_SECONDARY":
				await discord.bot.send_message(discord.mod_channel(), "CRITICAL (Secondary): Primary is still up but health checks have partner as down (split brain?) Shutting down until manual intervention.")
				redundancy.update_status("FAILED_SECONDARY", config.cfg['redundancy']['self_uid'])
				await discord.bot.logout()

	#message processing timings
	analytics.onMessageProcessTime(msgProcessStart, analytics.getEventTime())
