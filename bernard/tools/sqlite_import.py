import sqlite3
import argparse
import mysql.connector as mariadb

#get args
ap = argparse.ArgumentParser()
ap.add_argument("--host", required=True, help="MySQL/MariaDB Server")
ap.add_argument("--user", required=True, help="MySQL/MariaDB Username")
ap.add_argument("--password", required=True, help="MySQL/MariaDB Password")
ap.add_argument("--db", required=True, help="Bot Database")
ap.add_argument("--sqlite", required=True, help="Bernard DB file")
args = vars(ap.parse_args())

#establish mariadb connection
mariadb_conn = mariadb.connect(
    host=args['host'],
    user=args['user'],
    password=args['password'],
    database=args['db'])
mariadb_cursor = mariadb_conn.cursor(dictionary=True, buffered=True)

#establish sqlite connection
sqlite_conn = sqlite3.connect(args['sqlite'], check_same_thread=False)
sqlite_cursor = sqlite_conn.cursor()

#get everything from journal_events
print("----- STARTING EVENTS -----")
rows = sqlite_cursor.execute("SELECT * From journal_events ORDER BY time ASC LIMIT 50")
for row in rows:
    print(row)
    mariadb_cursor.execute('INSERT INTO journal_events'
                        '(module, event, time, userid, eventid, contents)'
                        'VALUES (%s,%s,%s,%s,%s,%s)',
                        (row[0], row[1], row[2], row[3], row[4], row[5]))
    mariadb_conn.commit()

#get everything from journal_regualators
print("----- STARTING REGULATORS -----")
rows = sqlite_cursor.execute("SELECT * From journal_regulators ORDER BY time ASC LIMIT 50")
for row in rows:
    print(row)
    mariadb_cursor.execute('INSERT INTO journal_regulators'
                        '(id_invoker, id_targeted, id_message, action, time, event)'
                        'VALUES (%s,%s,%s,%s,%s,%s)',
                        (row[0], row[1], row[2], row[3], row[4], row[5]))
    mariadb_conn.commit()

print("----- STARTING SUBS -----")
rows = sqlite_cursor.execute("SELECT * From subscribers LIMIT 50")
for row in rows:
    print(row)
    mariadb_cursor.execute('INSERT INTO subscribers'
                        '(userid, roleid, tier, last_updated, expires_epoch, expires_day)'
                        'VALUES (%s, %s, %s, %s, %s, %s) ',
                        (row[0], row[1], row[2], row[3], row[4], row[5]))
    mariadb_conn.commit()
