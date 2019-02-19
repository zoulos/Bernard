import asyncio
import unittest
import aiounittest
import bernard
from bernard import HelloCog
from .util import create_context, FakeBot
from discord.ext.commands.errors import CheckFailure


config = {"bernard": {"administrators": ["1"], "regulators": ["2"], "owner": "0"}}


class TestHello(aiounittest.AsyncTestCase):
    async def test_hello(self):
        context = create_context(
            {
                "author": {"id": "1", "mention": "foo", "roles": ["1"]},
                "channel": {"is_private": False},
            }
        )
        bot = FakeBot()
        cog = HelloCog(bot, config)

        await cog.hello.invoke(context)
        self.assertEqual(
            bot.said,
            "Hello foo! I am alive and well <:DestiSenpaii:399640604557967380>",
        )

    async def test_isowner(self):
        owner_context = create_context(
            {
                "author": {"id": "0", "mention": "foo", "roles": ["1"]},
                "channel": {"is_private": False},
            }
        )
        bot = FakeBot()
        cog = HelloCog(bot, config)
        await cog.isowner.invoke(owner_context)
        self.assertEqual(
            bot.said, "I live to please foo every way possible ( ͡° ͜ʖ ͡°)"
        )

        shitter_context = create_context(
            {
                "author": {"id": "10", "mention": "foo", "roles": ["1"]},
                "channel": {"is_private": False},
            }
        )
        with self.assertRaises(CheckFailure):
            await cog.isowner.invoke(shitter_context)

    async def test_isadmin(self):
        owner_context = create_context(
            {
                "author": {"id": "0", "mention": "foo", "roles": []},
                "channel": {"is_private": False},
            }
        )
        bot = FakeBot()
        cog = HelloCog(bot, config)
        await cog.isadmin.invoke(owner_context)
        self.assertEqual(
            bot.said, "Somehow Destiny let you have administrator in here... foo"
        )

        admin_context = create_context(
            {
                "author": {"id": "10", "mention": "foo2", "roles": ["1"]},
                "channel": {"is_private": False},
            }
        )
        await cog.isadmin.invoke(admin_context)
        self.assertEqual(
            bot.said, "Somehow Destiny let you have administrator in here... foo2"
        )

        shitter_context = create_context(
            {
                "author": {"id": "10", "mention": "foo", "roles": ["2"]},
                "channel": {"is_private": False},
            }
        )
        with self.assertRaises(CheckFailure):
            await cog.isadmin.invoke(shitter_context)

    async def test_isregulator(self):
        owner_context = create_context(
            {
                "author": {"id": "0", "mention": "foo", "roles": ["1"]},
                "channel": {"is_private": False},
            }
        )
        bot = FakeBot()
        cog = HelloCog(bot, config)
        await cog.isregulator.invoke(owner_context)
        self.assertEqual(
            bot.said,
            "foo is a regulator, and is ready to abuse all powers granted by the admins™.",
        )

        regulator_context = create_context(
            {
                "author": {"id": "2", "mention": "foo2", "roles": ["2"]},
                "channel": {"is_private": False},
            }
        )
        await cog.isregulator.invoke(regulator_context)
        self.assertEqual(
            bot.said,
            "foo2 is a regulator, and is ready to abuse all powers granted by the admins™.",
        )

        shitter_context = create_context(
            {
                "author": {"id": "10", "mention": "foo", "roles": ["3"]},
                "channel": {"is_private": False},
            }
        )
        with self.assertRaises(CheckFailure):
            await cog.isregulator.invoke(shitter_context)
