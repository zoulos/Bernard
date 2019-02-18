import bernard.config as config
import bernard.common as common
import bernard.discord as discord
import bernard.journal as journal
import bernard.database as database
import logging
import time
import asyncio

logger = logging.getLogger(__name__)
logger.info("loading...")


def user_duration_to_seconds(value):
    # figure out the conversation for the duration
    try:
        duration_value = value[-1:]
        duration_length = int(value[:-1])
    except ValueError:
        return False

    if duration_value == "s":
        duration_length = duration_length * 1
    elif duration_value == "m":
        duration_length = duration_length * 60
    elif duration_value == "h":
        duration_length = duration_length * 60 * 60
    elif duration_value == "d":
        duration_length = duration_length * 24 * 60 * 60
    elif duration_value == "w":
        duration_length = duration_length * 7 * 24 * 60 * 60
    elif duration_value == "y":
        duration_length = duration_length * 365 * 24 * 60 * 60
    else:
        return None

    return duration_length


def verify_reminder_duration_length(value):
    # check if the length is within bounds
    if value > config.cfg["scheduler"]["time_range_max_mins"] * 60:
        return False
    elif value < config.cfg["scheduler"]["time_range_min_mins"] * 60:
        return False


def set_future_task(**kwargs):
    invoker = kwargs["invoker"]
    channeltarget = kwargs["channel"]
    timetofire = kwargs["timestamp"]
    eventtype = kwargs["event"]

    try:
        target = kwargs["target"]
    except KeyError:
        target = invoker

    try:
        eventmsg = kwargs["msg"]
    except KeyError:
        eventmsg = None

    now = int(time.time())

    database.cursor.execute(
        "INSERT INTO scheduled_tasks"
        "(id_invoker, id_targeted, channel_targeted, time_invoked, time_scheduled, event_type, event_message)"
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (invoker, target, channeltarget, now, timetofire, eventtype, eventmsg),
    )
    database.connection.commit()

    return True


# the background task checking the db for things to do
async def scheduler_check_for_work():
    await discord.bot.wait_until_ready()
    while not discord.bot.is_closed:
        logger.info("Starting background task scheduler_check_for_work()")
        now = int(time.time())

        database.cursor.execute(
            "SELECT * FROM scheduled_tasks WHERE exec_run=0 AND time_scheduled < %s",
            (now,),
        )
        dbwork = database.cursor.fetchall()

        if len(dbwork) == 0:
            logger.info(
                "scheduler_check_for_work() found no work due, going back to sleep for 60 seconds"
            )
            await asyncio.sleep(60)
            continue
        else:
            logger.info(
                "scheduler_check_for_work() found {} jobs due".format(len(dbwork))
            )

        for work in dbwork:
            if work["event_type"] == "POST_MESSAGE":
                await scheduler_post_message(work)
            elif work["event_type"] == "UNBAN_MEMBER":
                await scheduler_unban_member(work)
            else:
                logger.error(
                    "ERROR: Unknown work type. POST_MESSAGE, UNBAN_MEMBER are currently supported"
                )

        await asyncio.sleep(60)


async def scheduler_mark_work_done(work):
    now = int(time.time())
    logger.info(
        "scheduler_mark_work_done() marking JOB ID {0} DONE AT {1}".format(
            work["id"], now
        )
    )
    database.cursor.execute(
        "UPDATE scheduled_tasks SET exec_run=1, exec_when=%s WHERE id=%s",
        (now, work["id"]),
    )
    database.connection.commit()


async def scheduler_post_message(work):
    now = int(time.time())
    logger.info(
        "POST_MESSAGE JOB ID {0[id]} CALLED BY {0[id_invoker]} TO POST IN CHANNEL {0[channel_targeted]}".format(
            work
        )
    )

    # build the message channel object to send in the message
    send_channel = discord.discord.Object(work["channel_targeted"])
    await discord.bot.send_message(
        send_channel,
        "<@{0[id_targeted]}> Asked for a reminder: {0[event_message]}".format(work),
    )

    # update the db that we sent this, and when it was sent
    await scheduler_mark_work_done(work)


# handles timed unbans
async def scheduler_unban_member(work):
    now = int(time.time())
    logger.info(
        "UNBAN_MEMBER JOB ID {0[id]} BANNED BY {0[id_invoker]} BAN HAS EXPIRED, UNBANNING {0[id_targeted]}".format(
            work
        )
    )

    # call the unban
    unban_status_discord = await common.unban_id(str(work["id_targeted"]))
    if unban_status_discord:
        logger.info(
            "UNBAN_MEMBER JOB ID {0[id]} USER ID {0[id_targeted]} BAN SUCCESSFULLY REMOVED FROM DISCORD.".format(
                work
            )
        )

        # update the modlog channel
        await discord.bot.send_message(
            discord.mod_channel(),
            "{0} **Scheduled Unban:** ID:`{1[id_targeted]}`)".format(
                common.bernardUTCTimeNow(), work
            ),
        )

        # set a user journal record the unban has happened
        journal.update_journal_event(
            module=__name__,
            event="ON_MEMBER_UNBAN_SCHEDULED",
            userid=work["id_targeted"],
            contents="SCHEDULER JOBID: {0[id]}".format(work),
        )

    else:
        logger.warn(
            "UNBAN_MEMBER JOB ID {0[id]} USER ID {0[id_targeted]} BAN WAS NOT REMOVED FROM DISCORD, USER ALREADY UNBANNED?".format(
                work
            )
        )

    await scheduler_mark_work_done(work)


if config.cfg["scheduler"]["enable"]:
    discord.bot.loop.create_task(scheduler_check_for_work())
