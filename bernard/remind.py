import bernard.config as config
import bernard.common as common
import bernard.discord as discord
import bernard.database as database
import bernard.scheduler as scheduler
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)
logger.info("loading...")


@discord.bot.command(pass_context=True, no_pm=True)
async def todo(ctx):
    database.cursor.execute(
        "SELECT * FROM scheduled_tasks WHERE exec_run=0 AND event_type='POST_MESSAGE' AND id_targeted = %s ORDER BY time_scheduled ASC",
        (ctx.message.author.id,),
    )
    waiting_work_count = database.cursor.fetchall()

    if len(waiting_work_count) == 0:
        await discord.bot.say(
            "⚠️{0.message.author.mention} Doesn't look like you have anything to be reminded of? Make one with `!remind 2d call destiny a betamale`".format(
                ctx
            )
        )
        return

    emd = discord.embeds.Embed(
        title="__Pending Reminders (Times {})__".format(time.localtime().tm_zone),
        colour=discord.discord.Color.green(),
        timestamp=datetime.utcnow(),
    )

    emd.set_author(
        name="{0}     (ID: {1})".format(ctx.message.author.name, ctx.message.author.id),
        icon_url=ctx.message.author.avatar_url,
    )
    emd.set_thumbnail(url=ctx.message.author.avatar_url)

    for waiting_work in waiting_work_count:
        time_friendly = time.strftime(
            "%m/%d/%Y %H:%M", time.localtime(waiting_work["time_scheduled"])
        )
        emd.add_field(
            name="{0} (ID:{1})".format(time_friendly, waiting_work["id"]),
            value=waiting_work["event_message"],
            inline=False,
        )

    await discord.bot.say(embed=emd)


@discord.bot.command(pass_context=True, no_pm=True)
async def unremind(ctx, reminder_id):
    database.cursor.execute(
        "SELECT * FROM scheduled_tasks WHERE exec_run=0 AND event_type='POST_MESSAGE' AND id_targeted = %s AND id = %s",
        (ctx.message.author.id, reminder_id),
    )
    id_to_remove = database.cursor.fetchone()

    if id_to_remove is None:
        await discord.bot.say(
            "⚠️{0.message.author.mention} I couldn't find that reminder ID. Are you sure it's yours?".format(
                ctx
            )
        )
        return
    else:
        await scheduler.scheduler_mark_work_done(id_to_remove)
        await discord.bot.say(
            "✔️{0.message.author.mention} Reminder removed! You will not be bothered about this task.".format(
                ctx
            )
        )


@discord.bot.command(pass_context=True, no_pm=True)
async def remind(ctx, duration, *, text):
    if common.isDiscordMainServer(ctx.message.server) is not True:
        return

    # set a cap of max 5 currently waiting jobs, regs+ are exempt
    if not common.isDiscordRegulator(ctx.message.author):
        database.cursor.execute(
            "SELECT * FROM scheduled_tasks WHERE exec_run=0 AND event_type='POST_MESSAGE' AND id_targeted = %s",
            (ctx.message.author.id,),
        )
        waiting_work_count = database.cursor.fetchall()
        if len(waiting_work_count) >= 5:
            await discord.bot.say(
                "⚠️{0.message.author.mention} you already have 5 waiting reminders. View them via `!todo`".format(
                    ctx
                )
            )
            return

    # get the user input to seconds
    duration_length = scheduler.user_duration_to_seconds(duration)
    if duration_length is False:
        await discord.bot.say(
            "⚠️{0.message.author.mention} unable to decode message length. Should be `!remind 60s|1m|4d don't forget about the potatoes`".format(
                ctx
            )
        )
        return
    elif duration_length is None:
        await discord.bot.say(
            "⚠️{0.message.author.mention} unable to decode message length. allowed: seconds (s), minutes (m), hours (h), days (d), weeks (w), years (y)".format(
                ctx
            )
        )
        return

    duration_inrange = scheduler.verify_reminder_duration_length(duration_length)
    if duration_inrange is False:
        await discord.bot.say(
            "⚠️{0.message.author.mention} Reminder is out of expected range. Current Range {1}m to {2}d".format(
                ctx,
                config.cfg["scheduler"]["time_range_min_mins"],
                int(config.cfg["scheduler"]["time_range_max_mins"] / 1440),
            )
        )
        return

    # dont allow abusive calls to be made, these should just make API calls to kick the user
    if "@everyone" in text.lower():
        return
    elif "@here" in text.lower():
        return
    else:
        text = text.replace("`", "'")

    # limit message to have 3 mentions
    if len(ctx.message.mentions) > 3:
        return

    # calculate the time it should fire
    now = int(time.time())
    time_to_fire = now + duration_length

    # set the reminder
    scheduler.set_future_task(
        invoker=ctx.message.author.id,
        channel=ctx.message.channel.id,
        timestamp=time_to_fire,
        event="POST_MESSAGE",
        msg=text,
    )

    when = time.strftime("%A, %B %d %Y %H:%M %Z", time.localtime(time_to_fire))
    await discord.bot.say(
        "✔️{0.message.author.mention} reminder set for `{1}`! I'll try not to forget about this, I promise.".format(
            ctx, when
        )
    )
