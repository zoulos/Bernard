import logging

import bernard.analytics as analytics
import bernard.common as common
import bernard.discord as discord
import bernard.journal as journal

logger = logging.getLogger(__name__)
logger.info("loading...")

IGNORE_IDS = []


# new member to the server. message = discord.Message
@discord.bot.event
async def on_message_edit(before, after):
    msgProcessStart = analytics.getEventTime()
    if common.isDiscordMainServer(before.server) is not True:
        return

    if before.content != after.content:
        if len(before.content) + len(after.content) < 1800:
            msg = "{0} **Caught Edited Message!**" \
                  "{1.author.mention} (Name:`{1.author}` ID:`{1.author.id}`) in {1.channel.mention} \n" \
                  "  Original: \"`{1.content}`\" \n\n" \
                  "  Edited: \"`{2.content}`\" \n".format(common.bernardUTCTimeNow(), before, after)
            msg_sent = await discord.bot.send_message(discord.messages_channel(), msg)
        else:
            msgs = [
                "{0} **Caught Edited Message! (WARNING: may be truncated)** {1.author.mention} (Name:`{1.author}` ID:`{1.author.id}`) in {1.channel.mention}".format(
                    common.bernardUTCTimeNow(), before),
                "  Original:```{0}```".format(before.content[:1980]),
                "  Edited:```{0}```".format(after.content[:1980])
            ]

            for msg in msgs:
                msg_sent = await discord.bot.send_message(discord.messages_channel(), msg)

        journal_msg = "https://discordapp.com/channels/{0.channel.server.id}/{0.channel.id}/{0.id}".format(msg_sent)
        journal.update_journal_event(module=__name__, event="ON_MESSAGE_EDIT", userid=before.author.id,
                                     eventid=before.id, contents=journal_msg)

    analytics.onMessageProcessTime(msgProcessStart, analytics.getEventTime())
