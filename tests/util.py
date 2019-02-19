from unittest import mock


class FakeBot(object):
    def __init__(self):
        self.said = None

    async def say(self, msg):
        self.said = msg


def create_context(cfg):
    context = mock.Mock()
    message = mock.Mock()
    author = mock.Mock()
    author.id = cfg["author"]["id"]
    author.mention = cfg["author"]["mention"]
    author.roles = cfg["author"]["roles"]
    message.author = author
    channel = mock.Mock()
    channel.is_private = cfg["channel"]["is_private"]
    message.channel = channel
    context.message = message
    return context
