import bernard.config as config
import bernard.common as common
import bernard.discord as discord
import bernard.database as database
import bernard.scheduler as scheduler
import logging
import time

logger = logging.getLogger(__name__)
logger.info("loading...")


@discord.bot.command(pass_context=True, no_pm=True)
async def remind(ctx, duration, *, text):
    if common.isDiscordMainServer(ctx.message.server) is not True:
        return

    #set a cap of max 5 currently waiting jobs, regs+ are exempt
    if not common.isDiscordRegulator(ctx.message.author):
        database.cursor.execute("SELECT * FROM scheduled_tasks WHERE exec_run=0 AND event_type='POST_MESSAGE' AND id_targeted = %s", (ctx.message.author.id,))
        waiting_work_count = database.cursor.fetchall()
        if len(waiting_work_count) >= 5:
            await discord.bot.say("⚠️{0.message.author.mention} you already have 5 waiting reminders. View them via `!todo`".format(ctx))
            return

    #get the user input to seconds
    duration_length = scheduler.user_duration_to_seconds(duration)
    if duration_length is False:
        await discord.bot.say("⚠️{0.message.author.mention} unable to decode message length. Should be `!remind 60s|1m|4d don't forget about the potatoes`".format(ctx))
        return
    elif duration_length is None:
        await discord.bot.say("⚠️{0.message.author.mention} unable to decode message length. allowed: seconds (s), minutes (m), hours (h), days (d), weeks (w), years (y)".format(ctx))
        return

    duration_inrange = scheduler.verify_reminder_duration_length(duration_length)
    if duration_inrange is False:
        await discord.bot.say("⚠️{0.message.author.mention} Reminder is out of expected range. Current Range {1}m to {2}d".format(ctx, config.cfg['scheduler']['time_range_min_mins'], int(config.cfg['scheduler']['time_range_max_mins'] / 1440)))
        return

    #dont allow abusive calls to be made, these should just make API calls to kick the user
    if "@everyone" in text.lower():
        return
    elif "@here" in text.lower():
        return
    text = text.replace("`","'")

    #limit message to have 3 mentions
    if len(ctx.message.mentions) > 3:
        return

    #calculate the time it should fire
    now = int(time.time())
    time_to_fire = now + duration_length

    #update the db
    database.cursor.execute('INSERT INTO scheduled_tasks'
                            '(id_invoker, id_targeted, channel_targeted, time_invoked, time_scheduled, event_type, event_message)'
                            'VALUES (%s,%s,%s,%s,%s,%s,%s)',
                            (ctx.message.author.id, ctx.message.author.id, ctx.message.channel.id, now, time_to_fire, "POST_MESSAGE",text))
    database.connection.commit()

    when = time.strftime("%A, %B %d %Y %H:%M %Z", time.localtime(time_to_fire))
    await discord.bot.say("✔️{0.message.author.mention} reminder set for `{1}`! I'll try not to forget about this, I promise.".format(ctx, when))
