from discord.ext import commands
from .base import BernardCog, owner_command, admin_command, regulator_command


class HelloCog(BernardCog):
    def __init__(self, bot, config):
        super().__init__(bot, config)

    @commands.command(pass_context=True, no_pm=True, description="Says Hello :)")
    async def hello(self, ctx):
        await self.bot.say(
            f"Hello {ctx.message.author.mention}! I am alive and well <:DestiSenpaii:399640604557967380>"
        )

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @owner_command()
    async def isowner(self, ctx):
        await self.bot.say(
            f"I live to please {ctx.message.author.mention} every way possible ( ͡° ͜ʖ ͡°)"
        )

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @admin_command()
    async def isadmin(self, ctx):
        await self.bot.say(
            f"Somehow Destiny let you have administrator in here... {ctx.message.author.mention}"
        )

    @commands.command(pass_context=True, no_pm=True, hidden=True)
    @regulator_command()
    async def isregulator(self, ctx):
        await self.bot.say(
            f"{ctx.message.author.mention} is a regulator, and is ready to abuse all powers granted by the admins™."
        )
