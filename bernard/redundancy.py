import bernard.config as config
import bernard.database as database
import logging
import time
import platform
import subprocess

logger = logging.getLogger(__name__)
logger.info("loading...")

IS_PRIMARY = False
HA_STATUS = ""

def get_partner_status(uuid):
    database.cursor.execute('SELECT * FROM ha WHERE uid=%s', (uuid,))
    res = database.cursor.fetchone()
    database.connection.commit() #clears the cache

    #if the db is even configured for HA
    if res is None:
        logger.critical("Unable to find parter {} in HA database configuration! Stopping bot.".format(uuid))
        exit()
    else:
        return res

def follow_primary(uuid):
    primary_db = get_partner_status(uuid)
    #if the bot is known as RUNNING_PRIMARY, lets confirm its health state. It should be updating its heartbeat within the minute
    if primary_db['current_state'] == "RUNNING_PRIMARY":
        last_alive = (time.mktime(time.gmtime()) - primary_db['last_heartbeat'])
        if last_alive <= config.cfg['redundancy']['grace']:
            logger.info("Primary is healthy. Last known alive {}".format(last_alive))
            return "STAY_SECONDARY"
        else:
            logger.warn("Primary is marked as RUNNING_PRIMARY but has not had a heartbeat in {} seconds. Assuming dead and signaling BECOME_PRIMARY".format(last_alive))
            return "BECOME_PRIMARY"
    elif primary_db['current_state'] == "BECOME_SECONDARY":
        logger.warn("Primary node is requesting to become the secondary and relinquish primary control.")
        return "BECOME_PRIMARY"
    elif primary_db['current_state'] == "SWITCH_PRIMARY":
        logger.warn("Primary node requested to go into secondary mode via !ha switch")
        return "BECOME_PRIMARY"
    else:
        return "STAY_SECONDARY"

def update_heartbeat():
    gitcommit = subprocess.check_output(['git','rev-parse','--short','HEAD']).decode(encoding='UTF-8').rstrip()
    database.cursor.execute("UPDATE ha SET last_heartbeat=%s, hostname=%s, current_version=%s WHERE uid=%s", (time.mktime(time.gmtime()), platform.node(), gitcommit, config.cfg['redundancy']['self_uid']))
    database.connection.commit()

def update_status(status, uuid):
    database.cursor.execute("UPDATE ha SET current_state=%s WHERE uid=%s", (status, uuid))
    database.connection.commit()

#if we are configured to be secondary, don't even start the bot code
if config.cfg['redundancy']['role'] == "secondary":
    logger.warn("Bot starting as a secondary role in HA pair. Primary is set as {}".format(config.cfg['redundancy']['partner_uid']))
    IS_PRIMARY = False
    while IS_PRIMARY is False:
        own_status = get_partner_status(config.cfg['redundancy']['self_uid'])
        HA_STATUS = follow_primary(config.cfg['redundancy']['partner_uid'])
        if HA_STATUS == "STAY_SECONDARY":
            update_heartbeat()
            update_status("STAY_SECONDARY", config.cfg['redundancy']['self_uid'])
            time.sleep(config.cfg['redundancy']['heartrate'])
        elif HA_STATUS == "BECOME_PRIMARY":
            update_status(HA_STATUS, config.cfg['redundancy']['self_uid'])
            update_status("FAILING_PRIMARY", config.cfg['redundancy']['partner_uid'])
            logger.info("HA_STATUS is now BECOME_PRIMARY. Leaving passive mode and attempting to enter an active state (bot should start here)")
            IS_PRIMARY = True

        if own_status['current_state'] == "FAILED_SECONDARY":
            logger.critical("Bot was reset due to a potential split brain condition. Dumping cluster info")
            logger.critical(get_partner_status(config.cfg['redundancy']['self_uid']))
            logger.critical(get_partner_status(config.cfg['redundancy']['partner_uid']))
            time.sleep(60 * 60 * 6) #60 secs for 60 mins for 6 hours
elif config.cfg['redundancy']['role'] == "primary":
    while IS_PRIMARY is False:
        own_status = get_partner_status(config.cfg['redundancy']['self_uid'])
        HA_STATUS = own_status['current_state']

        #if we are holding the start
        if HA_STATUS == "SWITCH_PRIMARY":
            logger.warn("Bot started but was signaled as SWITCH_MASTER. This mean !ha switch was invoked and the secondary is forced to run.")
            time.sleep(30) #sleep for 30 seconds. eventually
        else:
            IS_PRIMARY = True
            logger.info("HA_STATUS is now RUNNING_PRIMARY. Starting bot.")
            update_status(HA_STATUS, config.cfg['redundancy']['self_uid'])
            update_status("STAY_SECONDARY", config.cfg['redundancy']['partner_uid'])
