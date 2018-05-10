import bernard.config as config
import sqlite3
import logging
import time
import mysql.connector as mariadb

logger = logging.getLogger(__name__)
logger.info("loading...")

#mariadb
connection = mariadb.connect(
    host=config.cfg['bernard']['database']['server'],
    user=config.cfg['bernard']['database']['username'],
    password=config.cfg['bernard']['database']['password'],
    database=config.cfg['bernard']['database']['database'])

cursor = connection.cursor(dictionary=True, buffered=True)

#check if the db is locked
def check_db_ready():
    if connection.is_connected() is False:
        logger.critical("Unable to start bot: MySQL/MariaDB is not connected. Halting bot.")
        exit()

check_db_ready()
