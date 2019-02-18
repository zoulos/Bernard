import bernard.config as config
import bernard.common as common
import bernard.discord as discord
import bernard.analytics as analytics
import bernard.journal as journal
import logging

logger = logging.getLogger(__name__)
logger.info("loading...")

IGNORE_IDS = []

# new member to the server. message = discord.Message
@discord.bot.event
async def on_message_delete(message):
    msgProcessStart = analytics.getEventTime()
    if common.isDiscordMainServer(message.server) is not True:
        return

    if message.author.id in IGNORE_IDS:
        logger.info(
            "on_message_delete() ignoring deleted message user id is in IGNORE_IDS variable"
        )
        return

    if message.attachments and message.content == "":
        msg = "{0.author.mention} (Name:`{0.author}` ID:`{0.author.id}`) in {0.channel.mention} \n Deleted Attachment: `{0.attachments[0][filename]}` \n URL: <{0.attachments[0][url]}>".format(
            message
        )
        journal_msg = "Attachment: {0.attachments[0][filename]} Size: {0.attachments[0][size]}".format(
            message
        )
    elif message.attachments and message.content != "":
        msg = '{0.author.mention} (Name:`{0.author}` ID:`{0.author.id}`) in {0.channel.mention} \n Message: "`{0.content}`" \n\n Deleted Attachment: `{0.attachments[0][filename]}` \n URL: <{0.attachments[0][url]}>'.format(
            message
        )
        journal_msg = "Text: {0.content} Attachment: {0.attachments[0][filename]} Size: {0.attachments[0][size]}".format(
            message
        )
    else:
        msg = '{0.author.mention} (Name:`{0.author}` ID:`{0.author.id}`) in {0.channel.mention} \n Message: "`{0.content}`" \n\n'.format(
            message
        )
        journal_msg = "Text: {0.content}".format(message)

    await discord.bot.send_message(
        discord.messages_channel(),
        "{0} **Caught Deleted Message!** {1}".format(common.bernardUTCTimeNow(), msg),
    )

    journal.update_journal_event(
        module=__name__,
        event="ON_MESSAGE_DELETE",
        userid=message.author.id,
        eventid=message.id,
        contents=journal_msg,
    )

    analytics.onMessageProcessTime(msgProcessStart, analytics.getEventTime())
