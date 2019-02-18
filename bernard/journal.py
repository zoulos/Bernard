import bernard.config as config
import bernard.common as common
import bernard.discord as discord
import bernard.database as database
import logging
import asyncio
import time
from datetime import datetime

logger = logging.getLogger(__name__)
logger.info("loading...")

# handle auditing_blacklist_domains control
@discord.bot.command(pass_context=True, hidden=True)
async def journal(ctx, user: str):
    if common.isDiscordRegulator(ctx.message.author) is False:
        return

    target_id = discord.get_targeted_id(ctx)
    target_member = await discord.get_user_info(target_id)

    if target_id is None:
        database.cursor.execute(
            "SELECT * from journal_events WHERE userid=%s ORDER BY time DESC LIMIT 5",
            (target_id,),
        )
        emd = discord.embeds.Embed(
            title="Last 5 events for ({0})".format(user), color=0xE79015
        )
    else:
        database.cursor.execute(
            "SELECT * from journal_events WHERE userid=%s ORDER BY time DESC LIMIT 5",
            (target_id,),
        )
        emd = discord.embeds.Embed(
            title='Last 5 events for "{0.name}" ({0.id})'.format(target_member),
            color=0xE79015,
        )

    dbres = database.cursor.fetchall()

    if len(dbres) == 0:
        await discord.bot.say("Not found in my journal :(")
        return
    else:
        for row in dbres:
            emd.add_field(
                inline=False,
                name="{}".format(
                    datetime.fromtimestamp(float(row["time"])).isoformat()
                ),
                value="{0[event]} ({0[module]}) Result: {0[contents]}\n".format(row),
            )
        await discord.bot.say(embed=emd)


@discord.bot.command(pass_context=True, hidden=True)
async def rapsheet(ctx):
    if common.isDiscordRegulator(ctx.message.author) is False:
        return

    # Get the member
    target_id = discord.get_targeted_id(ctx)
    target_member = await discord.get_user_info(target_id)

    # Pull all their regulator actions, ignoring un-silence events.
    database.cursor.execute(
        "SELECT * from journal_regulators WHERE id_targeted=%s AND NOT action = 'VOICE_UNSILENCE' ORDER BY time DESC",
        (target_id,),
    )
    dbres = database.cursor.fetchall()

    # Get the first event in the logs for the user as a "first seen" date
    database.cursor.execute(
        "SELECT MIN(time) AS 'time' FROM journal_events WHERE userid = %s", (target_id,)
    )
    first_seen = database.cursor.fetchall()

    # If no events are returned, generate and send a clean rapsheet
    if len(dbres) == 0:
        emd = discord.embeds.Embed(
            title="__Moderation Statistics__",
            colour=discord.discord.Color.green(),
            timestamp=datetime.utcnow(),
        )

        emd.set_author(
            name="{0}     (ID: {1})".format(target_member.name, target_member.id),
            icon_url=target_member.avatar_url,
        )
        emd.set_thumbnail(url=target_member.avatar_url)

        if first_seen[0]["time"] is None:
            emd.add_field(
                name="No previous moderation actions found for user.",
                value="First Seen - Unknown",
            )
        else:
            emd.add_field(
                name="No previous moderation actions found for user.",
                value="First Seen - {0}".format(
                    datetime.fromtimestamp(first_seen[0]["time"]).strftime(
                        "%Y-%m-%d @ %H:%M:%S"
                    )
                ),
            )

        await discord.bot.say(embed=emd)
        return
    # Otherwise, total up all the events, generate, and send a dirty rapsheet
    else:
        emd = discord.embeds.Embed(
            title="__Moderation Statistics__",
            colour=discord.discord.Color.red(),
            timestamp=datetime.utcnow(),
        )

        emd.set_author(
            name="{0}     (ID: {1})".format(target_member.name, target_member.id),
            icon_url=target_member.avatar_url,
        )
        emd.set_thumbnail(url=target_member.avatar_url)

        warnCount, muteCount, kickCount, banCount = 0, 0, 0, 0
        warns, mutes, kicks, bans = "", "", "", ""
        for row in dbres:
            invoker = await discord.get_user_info(row["id_invoker"])
            if row["action"] == "WARN_MEMBER":
                warnCount += 1
                warns += "{0} - {1} --- *{2}*\n".format(
                    datetime.fromtimestamp(float(row["time"])).date().isoformat(),
                    invoker.mention,
                    row["id_message"],
                )
            elif row["action"] == "VOICE_SILENCE":
                muteCount += 1
                mutes += "{0} - {1} --- *{2}*\n".format(
                    datetime.fromtimestamp(float(row["time"])).date().isoformat(),
                    invoker.mention,
                    row["id_message"],
                )
            elif row["action"] == "KICK_MEMBER":
                kickCount += 1
                kicks += "{0} - {1} --- *{2}*\n".format(
                    datetime.fromtimestamp(float(row["time"])).date().isoformat(),
                    invoker.mention,
                    row["id_message"],
                )
            elif row["action"] == "BAN_MEMBER":
                banCount += 1
                bans += "{0} - {1} --- *{2}*\n".format(
                    datetime.fromtimestamp(float(row["time"])).date().isoformat(),
                    invoker.mention,
                    row["id_message"],
                )

        if warns == "":
            emd.add_field(
                name="Warnings: {0}".format(warnCount), value="N/A", inline=False
            )
        else:
            emd.add_field(
                name="Warnings: {0}".format(warnCount), value=warns, inline=False
            )

        if mutes == "":
            emd.add_field(
                name="Mutes: {0}".format(muteCount), value="N/A", inline=False
            )
        else:
            emd.add_field(
                name="Mutes: {0}".format(muteCount), value=mutes, inline=False
            )

        if kicks == "":
            emd.add_field(
                name="Kicks: {0}".format(kickCount), value="N/A", inline=False
            )
        else:
            emd.add_field(
                name="Kicks: {0}".format(kickCount), value=kicks, inline=False
            )

        if bans == "":
            emd.add_field(name="Bans: {0}".format(banCount), value="N/A", inline=False)
        else:
            emd.add_field(name="Bans: {0}".format(banCount), value=bans, inline=False)

        emd.add_field(
            name="First Seen",
            value=datetime.fromtimestamp(first_seen[0]["time"]).strftime(
                "%Y-%m-%d @ %H:%M:%S"
            ),
            inline=True,
        )
        emd.add_field(
            name="Time Since Moderation",
            value=str(
                datetime.now() - datetime.fromtimestamp(float(dbres[0]["time"]))
            ).split(".")[0],
            inline=True,
        )

        await discord.bot.say(embed=emd)


def update_journal_job(**kwargs):
    module = kwargs["module"]
    job = kwargs["job"]
    start = kwargs["start"]
    result = kwargs["result"]
    runtime = round(time.time() - start, 4)

    database.cursor.execute(
        "INSERT INTO journal_jobs"
        "(module, job, time, runtime, result)"
        "VALUES (%s,%s,%s,%s,%s)",
        (module, job, time.time(), runtime, result),
    )
    database.connection.commit()


def update_journal_event(**kwargs):
    module = kwargs["module"]
    event = kwargs["event"]
    userid = kwargs["userid"]
    try:
        eventid = kwargs["eventid"]
    except KeyError:
        eventid = None
    contents = kwargs["contents"]

    database.cursor.execute(
        "INSERT INTO journal_events"
        "(module, event, time, userid, eventid, contents)"
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (module, event, time.time(), userid, eventid, contents),
    )
    database.connection.commit()


def update_journal_regulator(**kwargs):
    invoker = kwargs["invoker"]
    target = kwargs["target"]
    eventdata = kwargs["eventdata"]
    action = kwargs["action"]
    try:
        message = kwargs["messageid"]
    except KeyError:
        message = None

    database.cursor.execute(
        "INSERT INTO journal_regulators"
        "(id_invoker, id_targeted, id_message, action, time, event)"
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (invoker, target, eventdata, action, time.time(), message),
    )
    database.connection.commit()
