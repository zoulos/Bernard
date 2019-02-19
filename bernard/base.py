from discord.ext import commands

# lmaooo
config_do_not_use = {}


def is_owner(member):
    return member.id == config_do_not_use["bernard"]["owner"]


def is_administrator(member):
    return _has_role_id(member, config_do_not_use["bernard"]["administrators"])


def is_regulator(member):
    return _has_role_id(member, config_do_not_use["bernard"]["regulators"])


def _has_role_id(member, role_ids):
    for role in member.roles:
        if role in role_ids:
            return True
    return False


def owner_command():
    def predicate(ctx):
        return is_owner(ctx.message.author)

    return commands.check(predicate)


def admin_command():
    def predicate(ctx):
        author = ctx.message.author
        return is_owner(author) or is_administrator(author)

    return commands.check(predicate)


def regulator_command():
    def predicate(ctx):
        author = ctx.message.author
        return is_owner(author) or is_administrator(author) or is_regulator(author)

    return commands.check(predicate)


class BernardCog:
    def __init__(self, bot, config):
        global config_do_not_use
        self.bot = bot
        self.config = config
        if not config_do_not_use:
            config_do_not_use = config
