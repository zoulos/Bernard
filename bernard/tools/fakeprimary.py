import argparse
import time
import random
import mysql.connector as mariadb

# get args
ap = argparse.ArgumentParser()
ap.add_argument("--host", required=True, help="MySQL/MariaDB Server")
ap.add_argument("--user", required=True, help="MySQL/MariaDB Username")
ap.add_argument("--password", required=True, help="MySQL/MariaDB Password")
ap.add_argument("--db", required=True, help="Bot Database")
ap.add_argument("--uuid", required=True, help="Fake master UUID to update")
args = vars(ap.parse_args())

# establish mariadb connection
conn = mariadb.connect(
    host=args["host"], user=args["user"], password=args["password"], database=args["db"]
)
cursor = conn.cursor(dictionary=True, buffered=True)

while True:
    now = time.mktime(time.gmtime())
    print(now)
    cursor.execute(
        "UPDATE ha SET last_heartbeat=%s, current_state='RUNNING_PRIMARY' WHERE uid=%s",
        (now, args["uuid"]),
    )
    conn.commit()

    rnd = random.randint(1, 20)
    time.sleep(rnd)
