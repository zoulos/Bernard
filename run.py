#!/usr/bin/env python3
import asyncio
import sys
import os
import json
import logging

from discord.ext import commands
from bernard import HelloCog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Loading...")

CONFIG_FILE = "config.json"


def read_config(path):
    if not os.path.isfile(path):
        raise RuntimeError(f"Unable to locate config file {path}")
    with open(path, "r") as f:
        return json.load(f)


def main():
    config = read_config(CONFIG_FILE)
    bernard = commands.Bot(
        command_prefix="!",
        max_messages=config["bernard"]["messagecache"],
        description="Bernard, for Discord. Made with love by ILiedAboutCake",
        loop=asyncio.get_event_loop(),
    )

    bernard.add_cog(HelloCog(bernard, config))

    @bernard.event
    async def on_ready():
        logger.info(f"Logged in as {bernard.user.name} ID: {bernard.user.id}")

    bernard.run(config["discord"]["token"])


if __name__ == "__main__":
    main()
