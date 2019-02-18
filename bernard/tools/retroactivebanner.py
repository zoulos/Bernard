import codecs
import sqlite3
import requests
import time
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--token", required=True, help="Discord Token")
ap.add_argument("--db", required=True, help="DB file")
ap.add_argument("--out", required=True, help="Log file")

args = vars(ap.parse_args())

discordHeaders = {"Authorization": "Bot " + args["token"]}

# sqlite
db = sqlite3.connect(args["db"])
curr = db.cursor()


def load():
    with codecs.open(args["out"], "r", encoding="utf8") as f:
        lines = f.readlines()

    for line in lines:
        a = line.split("ID:")
        # print(a)
        b = a[1].split("Reason:")
        ID = b[0].strip()

        c = a[0].split("User:")
        NAME = c[1].strip()

        REASON = b[1].replace("\n", "").strip()

        print(ID, NAME, REASON)

        curr.execute(
            """INSERT OR IGNORE INTO bans_retroactive(id, name, reason) VALUES(?,?,?)""",
            (ID, NAME, REASON),
        )

    db.commit()


def ban():
    LAST = "0"
    while True:
        # print("GETTING 1000 USERS FROM LAST ID "+ LAST)
        req = requests.get(
            "https://discordapp.com/api/guilds/265256381437706240/members?limit=1000&after="
            + LAST,
            headers=discordHeaders,
        )
        users = req.json()

        for user in users:
            LAST = user["user"]["id"]

            curr.execute(
                """SELECT * FROM bans_retroactive WHERE id=?""", (user["user"]["id"],)
            )
            retdb = curr.fetchone()

            if retdb is not None:
                print(
                    "USER FOUND IN RETROACTIVE LIST ON SERVER: WAS {0} NOW {1} ID {2}".format(
                        retdb[1], user["user"]["username"], user["user"]["id"]
                    )
                )
                req = requests.put(
                    "https://discordapp.com/api/guilds/265256381437706240/bans/"
                    + user["user"]["id"],
                    headers=discordHeaders,
                )
                if req.status_code == 204:
                    print("BANNED: " + user["user"]["username"])
                    time.sleep(1)


load()
ban()
