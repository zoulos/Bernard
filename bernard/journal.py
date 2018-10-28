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

#handle auditing_blacklist_domains control
@discord.bot.command(pass_context=True, hidden=True)
async def journal(ctx, user: str):
    if common.isDiscordRegulator(ctx.message.author) is False:
        return

    try:
        member = ctx.message.mentions[0]
    except IndexError:
        member = ctx.message.server.get_member(user)
        if member is None:
            member = ctx.message.server.get_member_named(user)

    if member is None:
        database.cursor.execute('SELECT * from journal_events WHERE userid=%s ORDER BY time DESC LIMIT 5', (user,))
        emd = discord.embeds.Embed(title='Last 5 events for ({0})'.format(user), color=0xE79015)
    else:
        database.cursor.execute('SELECT * from journal_events WHERE userid=%s ORDER BY time DESC LIMIT 5', (member.id,))
        emd = discord.embeds.Embed(title='Last 5 events for "{0.name}" ({0.id})'.format(member), color=0xE79015)

    dbres = database.cursor.fetchall()

    if len(dbres) == 0:
        await discord.bot.say("Not found in my journal :(")
        return
    else:
        for row in dbres:
            emd.add_field(inline=False,name="{}".format(datetime.fromtimestamp(float(row['time'])).isoformat()), value="{0[event]} ({0[module]}) Result: {0[contents]}\n".format(row))
        await discord.bot.say(embed=emd)


@discord.bot.command(pass_context=True, hidden=True)
async def rapsheet(ctx, user: str):
    if common.isDiscordRegulator(ctx.message.author) is False:
        return
    try:
        member = ctx.message.mentions[0]
    except IndexError:
        member = ctx.message.server.get_member(user)
        if member is None:
            member = ctx.message.server.get_member_named(user)

    emd = discord.embeds.Embed(title="__Moderation Statistics__",
                               colour=discord.discord.Color.red(),
                               timestamp=datetime.utcnow())
    if member is None:
        database.cursor.execute('SELECT * from journal_regulators WHERE id_targeted=%s ORDER BY time DESC', (user,))
        emd.set_author(name="User {0}".format(user))
    else:
        database.cursor.execute('SELECT * from journal_regulators WHERE id_targeted=%s ORDER BY time DESC', (member.id,))
        emd.set_author(name=member.name, icon_url=member.avatar_url)
        emd.set_thumbnail(url=member.avatar_url)

    dbres = database.cursor.fetchall()

    if len(dbres) == 0:
        await discord.bot.say("No previous moderation actions found for user.")
        return
    else:
        warnCount, muteCount, kickCount, banCount = 0, 0, 0, 0
        warns, mutes, kicks, bans = "", "", "", ""
        for row in dbres:
            if row['action'] == "WARN_MEMBER":
                warnCount += 1
                warns += "{0} - *{1}*\n".format(datetime.fromtimestamp(float(row['time'])).date().isoformat(), row['id_message'])
            elif row['action'] == "VOICE_SILENCE":
                muteCount += 1
                mutes += "{0} - *{1}*\n".format(datetime.fromtimestamp(float(row['time'])).date().isoformat(), row['id_message'])
            elif row['action'] == "KICK_MEMBER":
                kickCount += 1
                kicks += "{0} - *{1}*\n".format(datetime.fromtimestamp(float(row['time'])).date().isoformat(), row['id_message'])
            elif row['action'] == "BAN_MEMBER":
                banCount += 1
                bans += "{0} - *{1}*\n".format(datetime.fromtimestamp(float(row['time'])).date().isoformat(), row['id_message'])

        if warns == "":
            emd.add_field(name="Warnings: {0}".format(warnCount), value="N/A", inline=False)
        else:
            emd.add_field(name="Warnings: {0}".format(warnCount), value=warns, inline=False)
        
        if mutes == "":
            emd.add_field(name="Mutes: {0}".format(muteCount), value="N/A", inline=False)
        else:
            emd.add_field(name="Mutes: {0}".format(muteCount), value=mutes, inline=False)
        
        if kicks == "":
            emd.add_field(name="Kicks: {0}".format(kickCount), value="N/A", inline=False)
        else:
            emd.add_field(name="Kicks: {0}".format(kickCount), value=kicks, inline=False)

        if bans == "":
            emd.add_field(name="Bans: {0}".format(banCount), value="N/A", inline=False)
        else:
            emd.add_field(name="Bans: {0}".format(banCount), value=bans, inline=False)

        emd.add_field(name="First Moderation", value=datetime.fromtimestamp(float(dbres[-1]['time'])).isoformat(), inline=True)
        emd.add_field(name="Most Recent Moderation", value=datetime.fromtimestamp(float(dbres[0]['time'])).isoformat(), inline=True)
        emd.set_footer(text="Generated", icon_url="https://cdn.discordapp.com/emojis/399640604755361792.png?v=1")
        await discord.bot.say(embed=emd)


def update_journal_job(**kwargs):
    module = kwargs['module']
    job = kwargs['job']
    start = kwargs['start']
    result = kwargs['result']
    runtime = round(time.time() - start, 4)

    database.cursor.execute('INSERT INTO journal_jobs'
                            '(module, job, time, runtime, result)'
                            'VALUES (%s,%s,%s,%s,%s)',
                            (module, job, time.time(), runtime, result))
    database.connection.commit()

def update_journal_event(**kwargs):
    module = kwargs['module']
    event = kwargs['event']
    userid = kwargs['userid']
    try:
        eventid = kwargs['eventid']
    except KeyError:
        eventid = None
    contents = kwargs['contents']

    database.cursor.execute('INSERT INTO journal_events'
                            '(module, event, time, userid, eventid, contents)'
                            'VALUES (%s,%s,%s,%s,%s,%s)',
                            (module, event, time.time(), userid, eventid, contents))
    database.connection.commit()

def update_journal_regulator(**kwargs):
    invoker = kwargs['invoker']
    target = kwargs['target']
    eventdata = kwargs['eventdata']
    action = kwargs['action']
    try:
        message = kwargs['messageid']
    except KeyError:
        message = None

    database.cursor.execute('INSERT INTO journal_regulators'
                            '(id_invoker, id_targeted, id_message, action, time, event)'
                            'VALUES (%s,%s,%s,%s,%s,%s)',
                            (invoker, target, eventdata, action, time.time(), message))
    database.connection.commit()
