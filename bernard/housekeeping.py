import bernard.config as config
import bernard.common as common
import bernard.discord as discord
import bernard.analytics as analytics
import bernard.journal as journal
import bernard.database as database
import logging
import asyncio


logger = logging.getLogger(__name__)
logger.info("loading...")

#cleans up the server of users who have not signed into discord in x days as defined in config.cfg -> purge_inactive_users
async def purge_inactive_users():
    await discord.bot.wait_until_ready()
    while not discord.bot.is_closed:
        job_start = analytics.getEventTime()
        logger.info("Starting background task purge_inactive_users() - Interval {0}".format(config.cfg['housekeeping']['purge_inactive_users']['interval']))

        est = await discord.bot.estimate_pruned_members(server=discord.objectFactory(config.cfg['discord']['server']), days=config.cfg['housekeeping']['purge_inactive_users']['inactive_days'])
        if est > 0:
            #send the cleanup
            pruned = await discord.bot.prune_members(server=discord.objectFactory(config.cfg['discord']['server']), days=config.cfg['housekeeping']['purge_inactive_users']['inactive_days'])

            #notify via mod room and console log whos getting purged
            logger.warn("Purging {0} inactive users via purge_inactive_users() background job".format(pruned))
            await discord.bot.send_message(discord.mod_channel(), "{0} **Pruned Inactive Users:** {1} users removed for inactivity of {2} days".format(common.bernardUTCTimeNow(), pruned, config.cfg['housekeeping']['purge_inactive_users']['inactive_days']))

        logger.info("Sleeping background task purge_inactive_users() - Interval {0}".format(config.cfg['housekeeping']['purge_inactive_users']['interval']))
        journal.update_journal_job(module=__name__, job="purge_inactive_users", start=job_start, result=est)
        await asyncio.sleep(config.cfg['housekeeping']['purge_inactive_users']['interval'])

async def journal_events_cleanup():
    await discord.bot.wait_until_ready()
    while not discord.bot.is_closed:
        logger.info("Starting background task journal_events_cleanup() - Interval {0}".format(config.cfg['housekeeping']['journal_events_cleanup']['interval']))

        #get the current time, and our tareted lookup time for the database query
        utc_now = common.bernardUTCEpochTimeNow()
        seconds_grace = 86400 * config.cfg['housekeeping']['journal_events_cleanup']['days_to_keep']
        db_cutoff = int(utc_now - seconds_grace)
        logger.info("journal_events_cleanup() attempting purge of deleted messages older than {0} seconds ({1}) days".format(seconds_grace, config.cfg['housekeeping']['journal_events_cleanup']['days_to_keep']))

        #delete the records for deleted and edited messages over configured date
        database.cursor.execute("DELETE from journal_events where event='ON_MESSAGE_DELETE' OR event = 'ON_MESSAGE_EDIT' and time<%s order by time desc", (db_cutoff,))
        deleted_records_count = database.cursor.rowcount

        #log internally and update the modlog channel
        if deleted_records_count > 0:
            logger.warn("journal_events_cleanup() purging {0} deleted messages from journal_events".format(deleted_records_count))
            await discord.bot.send_message(discord.mod_channel(), "{0} **Pruned Deleted Messages:** {1} messages removed from journal for being older than {2} days".format(common.bernardUTCTimeNow(), deleted_records_count, config.cfg['housekeeping']['journal_events_cleanup']['days_to_keep']))
        else:
            logger.warn("journal_events_cleanup() nothing to delete at this time.")

        await asyncio.sleep(config.cfg['housekeeping']['journal_events_cleanup']['interval'])


if config.cfg['housekeeping']['purge_inactive_users']['enable']:
    discord.bot.loop.create_task(purge_inactive_users())

if config.cfg['housekeeping']['journal_events_cleanup']['enable']:
    discord.bot.loop.create_task(journal_events_cleanup())
