import bernard.config as config
import bernard.common as common
import bernard.discord as discord
import bernard.journal as journal
import bernard.database as database
import asyncio
import aiohttp
import logging
import time

logger = logging.getLogger(__name__)
logger.info("loading...")

"""
TODO:
- Silence users in text, write to eventS_regulators
- publish events done via bot to #bernard
- public command to query reuglator actions
"""

#function to build the roles list allowed to be punished, this is kinda hacky
async def get_allowed_groups():
    global untouchable_roles
    untouchable_roles = []

    await discord.bot.wait_until_ready()
    await asyncio.sleep(1)

    #get all the roles, and make a list of them
    all_roles = discord.default_server.roles
    for role in all_roles:
        untouchable_roles.append(role.id)

    #remove default role
    untouchable_roles.remove(discord.default_server.default_role.id)

    #remove twitch role
    untouchable_roles.remove(config.cfg['discord']['twitch_managed_role'])

    #remove destinygg subscriber roles
    for feature in config.cfg['subscriber']['features']:
        untouchable_roles.remove(config.cfg['subscriber']['features'][feature]['roleid'])

#this starts get_allowed_groups() at startup, but requires the bot to be ready
discord.bot.loop.create_task(get_allowed_groups())

#use the same check across all commands to see if the regulator is allowed to preform the action based on permission, role, status
def allow_regulation(ctx):
    #has to be a regulator+
    if common.isDiscordRegulator(ctx.message.author) == True:
        pass
    else:
        logger.info("Attempted to call allow_regulation but was rejected for: no permission")
        return False

    #has to be a mention, not just typing a username
    if len(ctx.message.mentions) == 0:
        logger.info("Attempted to call allow_regulation but was rejected for: no mention")
        return False
    else:
        target = ctx.message.mentions[0]

    #dont let the user try to play themselves
    if target.id == ctx.message.author.id:
        logger.info("Attempted to call allow_regulation but was rejected for: self harm")
        return False

    #if the user is an admin process it bypassing permissions
    if common.isDiscordAdministrator(ctx.message.author) == True:
        return True

    #get the assigned role IDs
    target_roles = []
    for role in target.roles:
        target_roles.append(role.id)

    #convert the lists to sets
    target_set = set(target_roles)
    untouchable_set = set(untouchable_roles)

    #if they intersect, they should not be touched
    allowed_set = untouchable_set.intersection(target_set)
    if len(allowed_set) == 0:
        return True
    else:
        logger.info("Attempted to call allow_regulation but was rejected for: untouchable role")
        return False

    #failsafe to no if my bad logic fails
    logger.info("Attempted to call allow_regulation but was rejected for: failsafe")
    return False


#kick a user from the server, must supply a user mention and string longer than 4 chars to land
@discord.bot.command(pass_context=True, no_pm=True, hidden=True)
async def kick(ctx, target, *, reason):
    if common.isDiscordRegulator(ctx.message.author) != True:
        return

    #ban reason has to have at least a word in it
    if len(reason) < 4:
        await discord.bot.say("⚠️ Kick reason must be longer than 4 characters. `!kick @username reason goes here`")
        return

    if allow_regulation(ctx):
        #return what is happening in the same channel to alert the user, wait 5 seconds and fire the kick command
        await discord.bot.say("✔️ {} is kicking {} with the reason of `{}`.".format(ctx.message.author.mention, ctx.message.mentions[0].mention, reason))
        await asyncio.sleep(5)
        await discord.bot.kick(ctx.message.mentions[0])

        #update the internal bot log, since we cant send kick reasons via this api version #TODO: in rewrite add that
        journal.update_journal_regulator(invoker=ctx.message.author.id, target=ctx.message.mentions[0].id, eventdata=reason, action="KICK_MEMBER", messageid=ctx.message.id)
    else:
        await discord.bot.say("🛑 {} unable to moderate user. Either you failed to tag the user properly or the member is protected from regulators.".format(ctx.message.author.mention))


#kick a user from the server, must supply a user mention and string longer than 4 chars to land
@discord.bot.command(pass_context=True, no_pm=True, hidden=True)
async def ban(ctx, target, *, reason):
    if common.isDiscordRegulator(ctx.message.author) != True:
        return

    #ban reason has to have at least a word in it
    if len(reason) < 10:
        await discord.bot.say("⚠️ ban reason must be longer than 10 characters. `!ban @username reason goes here`")
        return

    if allow_regulation(ctx):
        await discord.bot.say("✔️ {} is **BANNING** {} with the reason of `{}`.".format(ctx.message.author.mention, ctx.message.mentions[0].mention, reason))
        await asyncio.sleep(5)
        res = await common.ban_verbose(ctx.message.mentions[0], "{} - '{}'".format(ctx.message.author.name, reason))
        if res == False:
            await discord.bot.say("❓ Something's fucked! Unable to issue ban to Discord API. Bother cake.")
        else:
            journal.update_journal_regulator(invoker=ctx.message.author.id, target=ctx.message.mentions[0].id, eventdata=reason, action="BAN_MEMBER", messageid=ctx.message.id)
    else:
        #if a raw mention exists but not the Member object, handle it as retroactive and log who did it.
        if len(ctx.message.raw_mentions) == 1 and len(ctx.message.mentions) == 0:
            await discord.bot.say("✔️ {} is (retroactive) **BANNING** userid `{}` with the reason of `{}`.".format(ctx.message.author.mention, ctx.message.raw_mentions[0], reason))

            journal.update_journal_regulator(invoker=ctx.message.author.id, target=ctx.message.raw_mentions[0], eventdata=reason, action="BAN_MEMBER_RETROACTIVE", messageid=ctx.message.id)

            retroactive_reason = "VIA_RETROACTIVE: {} - '{}'".format(ctx.message.author.name, reason)
            database.cursor.execute('INSERT INTO bans_retroactive (id, name, reason) VALUES (%s,%s,%s)',(ctx.message.raw_mentions[0], "N/A", retroactive_reason))
            database.connection.commit()
        else:
            await discord.bot.say("🛑 {} unable to moderate user. Either you failed to tag the user properly or the member is protected from regulators.".format(ctx.message.author.mention))

#anti-raid/easy cleanup code, used to mass ban my ingress point
@discord.bot.command(pass_context=True, no_pm=True, hidden=True)
async def inviteban(ctx, target, *, reason):
    if common.isDiscordRegulator(ctx.message.author) != True:
        return

    #get anyone who joined via the invite
    database.cursor.execute("SELECT * FROM journal_events WHERE event='ON_MEMBER_JOINED_WITH_INVITE' AND contents=%s", (target,))
    invitees =  database.cursor.fetchall()

    #if there is not anyone, dont even do anything
    if len(invitees) == 0 or target.lower() == "none":
        await discord.bot.say("⚠️ {} Invalid invite code! 0 members joined via internal journal. Retype invite or bother Cake.".format(ctx.message.author.mention))
        return

    #get the invite data, make sure it is valid and then get who made it. They purge first.
    try:
        invite = await discord.bot.get_invite(target)
    except Exception as e:
        invite = None
        await discord.bot.say("⚠️ {} unable to look up invite code: {} for ownership! Moving on to blind mode!".format(ctx.message.author.mention, e))

    #ban the inviter if we know who they are
    if invite is not None:
        banned_inviter = await common.ban_verbose(invite.inviter, "{} from invite {} - '{}'".format(ctx.message.author.name, target, reason))
        if banned_inviter == False:
            pass
            await discord.bot.say("❓ Something's fucked! Unable to issue ban to Discord API for root invite creator. Bother cake. (protected user?)")
        else:
            journal.update_journal_regulator(invoker=ctx.message.author.id, target=invite.inviter.id, eventdata=target, action="BAN_MEMBER_VIA_INVITE_MAKER", messageid=ctx.message.id)
            await discord.bot.say("✔️ {} is dropping the hammer on {} and anyone who joined via their invite `{}`. Let the bombs drop! ".format(ctx.message.author.mention, invite.inviter.mention, target))

    for invited in invitees:

        #attempt to turn the ID into a valid member object
        server = discord.bot.get_server(config.cfg['discord']['server'])
        invited_member = server.get_member(str(invited['userid']))

        #if that cant happen, the user probably left or was banned already. Add to retroactive table (TODO)
        if invited_member == None:
                database.cursor.execute('INSERT IGNORE INTO bans_retroactive(id, name, reason) VALUES(%s,%s,%s)', (invited['userid'], "UNKNOWN_INVITEBAN_CALLED", reason))
                database.connection.commit()
                await discord.bot.say("⚠️ `{}` is getting banned for joining on invite `{}` (retroactive fallback. User either left or already banned) ".format(invited['userid'], target))
        else:
            banned_inviter = await common.ban_verbose(invited_member, "{} inviteban via {} - '{}'".format(ctx.message.author.name, target, reason))
            if banned_inviter == False:
                await discord.bot.say("❓ Something's fucked! Unable to issue ban to Discord API for {}. Bother cake.".format(invited_member.mention))
            else:
                await discord.bot.say("✔️ {} is getting banned for joining on invite `{}` ".format(invited_member.mention, target))

        #take a break between to prevent r8 limited
        await asyncio.sleep(2)

    await discord.bot.say("Invite ban completed. {} members removed. Thanks for playing!".format(len(invitees)))

# handle unbans of regs own bans, also allow admins to unban anyone by id
@discord.bot.command(pass_context=True, no_pm=True, hidden=True)
async def unban(ctx, target):
    if common.isDiscordAdministrator(ctx.message.author):
        #if the user is an admin, let them blindly call IDs, unban blindly from discord
        unban_status_discord = await common.unban_id(target)

        #also check the retroactive table, this can be useful if the user was retro banned but never rejoied
        database.cursor.execute('SELECT * FROM bans_retroactive WHERE id=%s', (target,))
        unban_status_retroactive = database.cursor.fetchone()
        if unban_status_retroactive is None:
            unban_status_retroactive = False
        else:
            database.cursor.execute('DELETE FROM bans_retroactive WHERE id=%s', (target,))
            database.connection.commit()

        #unban message logic
        if unban_status_discord is False and unban_status_retroactive is False:
            await discord.bot.say("⚠️ Unable to find ID in either Discord or Retroactive table. Try again?")
        elif unban_status_discord is True and unban_status_retroactive is False:
            await discord.bot.say("✔️ User was found banned on Discord. Removed ban.")
        elif unban_status_discord is False and unban_status_retroactive is True:
            await discord.bot.say("✔️ User was found banned in Retroactive table. Removed from database.")
        else:
            await discord.bot.say("✔️ User was found banned on Discord and Retroactive ban table. Removed ban and database entry.")
    elif common.isDiscordRegulator(ctx.message.author):
        #regulators have a slightly different logic to follow to allow. Use internal audit log to make decisions
        database.cursor.execute('SELECT * FROM journal_regulators WHERE id_targeted=%s AND id_invoker=%s AND action="BAN_MEMBER" ORDER BY time ASC', (target, ctx.message.author.id))
        regulator_target_history = database.cursor.fetchone()

        #if there is nothing in the database there is no reason to even try with the logic
        if regulator_target_history is None:
            logger.warn("{0} attempted unban of {1} ID but failed due to reason: DB_RETURNED_NONE".format(ctx.message.author.id, target))
            await discord.bot.say("⚠️ {0.message.author.mention} Unable to find any record of you banning ID `{1}` (ever). You can only unban people you yourself banned.".format(ctx, target))
            return

        #get how many mins ago the ban was to see if they are able to be unbanned
        banned_mins_ago = int((time.time() - regulator_target_history['time']) / 60)

        #handle if we should process the unban_id()
        if banned_mins_ago > config.cfg['regulators']['unban_grace_mins']:
            over_grace_mins = int(banned_mins_ago - config.cfg['regulators']['unban_grace_mins'])
            logger.warn("{0} attempted unban of {1} ID but failed due to reason: OVER_GRACE_PERIOD by {2} minutes".format(ctx.message.author.id, target, over_grace_mins))
            await discord.bot.say("⚠️ {0.message.author.mention} The user ID `{1}` is over the grace period for regulator unbans by `{2}` minutes. Contact an Administrator.".format(ctx, target, over_grace_mins))
        else:
            unban_status_discord = await common.unban_id(target)
            if unban_status_discord is False:
                logger.warn("{0} attempted unban of {1} ID but failed due to reason: DISCORD_RETURNED_NOT_BANNED".format(ctx.message.author.id, target))
                await discord.bot.say("⚠️ {0.message.author.mention}  Discord returned no ban found for ID `{1}` (ever). The user was already unbanned or something is wrong :/".format(ctx, target))
            else:
                logger.info("{0} unbanned {1}. Time elapsed since ban {2}".format(ctx.message.author.id, target, banned_mins_ago))
                await discord.bot.say("✔️ {0.message.author.mention} ID `{1}` has been unbanned!".format(ctx, target))
                journal.update_journal_regulator(invoker=ctx.message.author.id, target=target, eventdata=banned_mins_ago, action="UNBAN_MEMBER_GRACE", messageid=ctx.message.id)

#strip member of rights to talk in voice rooms
@discord.bot.command(pass_context=True, no_pm=True, hidden=True)
async def silence(ctx, target, *, reason):
    if common.isDiscordRegulator(ctx.message.author) != True:
        return

    #ban reason has to have at least a word in it
    if len(reason) < 4:
        await discord.bot.say("⚠️ Silence reason must be longer than 4 characters. `!silence @username reason goes here`")
        return

    if allow_regulation(ctx):
        await discord.bot.server_voice_state(ctx.message.mentions[0], mute=1)
        journal.update_journal_regulator(invoker=ctx.message.author.id, target=ctx.message.mentions[0].id, eventdata=reason, action="VOICE_SILENCE", messageid=ctx.message.id)
        await discord.bot.say("✔️ {} was silenced by {} in voice chat!".format(ctx.message.mentions[0].mention, ctx.message.author.mention))
    else:
        await discord.bot.say("🛑 {} unable to moderate user. Either you failed to tag the user properly or the member is protected from regulators.".format(ctx.message.author.mention))

#return member rights to talk in voice rooms
@discord.bot.command(pass_context=True, no_pm=True, hidden=True)
async def unsilence(ctx, target):
    if common.isDiscordRegulator(ctx.message.author) != True:
        return

    if allow_regulation(ctx):
        await discord.bot.server_voice_state(ctx.message.mentions[0], mute=0)
        journal.update_journal_regulator(invoker=ctx.message.author.id, target=ctx.message.mentions[0].id, eventdata="None", action="VOICE_UNSILENCE", messageid=ctx.message.id)
        await discord.bot.say("✔️ {} was unsilenced by {} in voice chat!".format(ctx.message.mentions[0].mention, ctx.message.author.mention))
    else:
        await discord.bot.say("🛑 {} unable to moderate user. Either you failed to tag the user properly or the member is protected from regulators.".format(ctx.message.author.mention))
