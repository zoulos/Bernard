import bernard.config as config
import bernard.redundancy as redundancy
import asyncio
import discord
import logging
import subprocess
from discord.ext import commands
from discord import embeds

logger = logging.getLogger(__name__)
logger.info("loading...")

bot_jobs_ready = False

evtloop = asyncio.get_event_loop()

bot = commands.Bot(command_prefix='!', max_messages=config.cfg['bernard']['messagecache'], description='Bernard, for Discord. Made with love by ILiedAboutCake', loop=evtloop)

@bot.event
async def on_ready():
    global bot_jobs_ready
    global default_server
    logger.info('Logged in as {0.user.name} ID:{0.user.id}'.format(bot))

    await verify_primary()

    #make an object available of this Server
    default_server = bot.get_server(config.cfg['discord']['server'])

    await asyncio.sleep(5)

    if config.cfg['bernard']['debug']:
        gitcommit = subprocess.check_output(['git','rev-parse','--short','HEAD']).decode(encoding='UTF-8').rstrip()
        await bot.change_presence(game=discord.Game(name="Debug: {}".format(gitcommit)))
    else:
        logger.info('Setting game status as in as "{0}"'.format(config.cfg['bernard']['gamestatus']))
        await bot.change_presence(game=discord.Game(name=config.cfg['bernard']['gamestatus']))

    bot.remove_command('help')

    await asyncio.sleep(30)
    logger.info('Setting internal bot_jobs_ready flag to True')
    bot_jobs_ready = True

if config.cfg['bernard']['debug'] is False:
    @bot.event
    async def on_command_error(error, ctx):
        logger.info("Uncaught command triggered: \"{0}\" {1}".format(error, ctx))

def objectFactory(snowflake):
    return discord.Object(snowflake)

def mod_channel():
    return discord.Object(config.cfg['bernard']['channel'])

async def update_heartbeat():
    await bot.wait_until_ready()
    while not bot.is_closed:
        #update our own heartbeat
        redundancy.update_heartbeat()

        #if we are running as secondary poll for the master being available again
        if config.cfg['redundancy']['role'] == "secondary":
            partner = redundancy.get_partner_status(config.cfg['redundancy']['partner_uid'])
            if partner['current_state'] == "RUNNING_PRIMARY":
                logger.warn("Primary bot is detected to be back. Returning to STAY_SECONDARY state.")
                redundancy.update_status("STAY_SECONDARY", config.cfg['redundancy']['self_uid'])
                await bot.logout()

        await asyncio.sleep(5)

#background task to update ha status if enabled
async def verify_primary():
    if config.cfg['redundancy']['enable']:
        #start heartbeating
        bot.loop.create_task(update_heartbeat())

        if redundancy.HA_STATUS == "RUNNING_PRIMARY":
            return True
        elif redundancy.HA_STATUS == "BECOME_PRIMARY":
            #send a chat message the partner is looking for as a last resort before hitting runtime
            logger.warn("Bot started as BECOME_PRIMARY. Trying last effort to verify primary before starting processing.")
            redundancy.update_status("RUNNING_SECONDARY", config.cfg['redundancy']['self_uid'])
            await bot.send_message(mod_channel(), "{0.user.mention} HA failover started! Secondary server is now RUNNING_SECONDARY. Partner {1} is at the last chance to announce itself as alive.".format(bot, config.cfg['redundancy']['partner_uid']))
        elif redundancy.HA_STATUS == "STAY_SECONDARY":
            #if we are supposed to be secondary, peace out and reload to pre bot state
            await bot.logout()
