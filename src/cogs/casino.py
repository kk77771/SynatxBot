import discord
from discord.ext import commands


class Casino(commands.Cog):
    def __init__(self, client):
        self.client = client

    # TODO: Do all commands


def setup(client):
    print('Crypto has been loaded.')
    client.add_cog(Casino(client))
