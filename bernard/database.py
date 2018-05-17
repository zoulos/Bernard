import bernard.config as config
import sqlite3
import logging
import time
import asyncio
import mysql.connector as mariadb

logger = logging.getLogger(__name__)
logger.info("loading...")

#mariadb
try:
    logger.info("Attempting to establish DB connection to {0[server]} to database {0[database]}".format(config.cfg['bernard']['database']))
    connection = mariadb.connect(
        host=config.cfg['bernard']['database']['server'],
        user=config.cfg['bernard']['database']['username'],
        password=config.cfg['bernard']['database']['password'],
        database=config.cfg['bernard']['database']['database'])
except Exception as err:
    logger.critical("Bot unable to connect to DB! Error: {}".format(err))
    exit()

cursor = connection.cursor(dictionary=True, buffered=True)

#check if the db is really connected
def check_db_ready():
    if connection.is_connected():
        logger.info("Successfully connected to MySQL/MariaDB!")
    else:
        logger.critical("Unable to start bot: MySQL/MariaDB is not connected. Halting bot.")
        exit()

check_db_ready()

#this is called as an async task in discord.py with verify_database()
async def check_db_process():
    while True:
        if connection.is_connected():
            await asyncio.sleep(config.cfg['bernard']['database']['checkrate'])
        else:
            logger.critical("Database is no longer reachable! This is a fatal error. Halting bot.")
            exit()
