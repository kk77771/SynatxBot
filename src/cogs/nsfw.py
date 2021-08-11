import discord
from discord.ext import commands
from discord.ext.commands.errors import NoPrivateMessage
import requests
import json
from bot import logger


class Nsfw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Nsfw Cog loaded")

    @commands.group(invoke_without_command=True, description="nsfw commands group")
    async def nsfw(self, ctx):
        # await ctx.send("nsfw commands: hentai, boobs, anal, pussy, solo, blowjob, lesbian")
        return 

    @nsfw.command(name="hentai", description="Sending a hentai gif.")
    async def hentai(self, ctx):
        if ctx.channel.is_nsfw():
            respose = requests.get("https://nekos.life/api/v2/img/Random_hentai_gif")
            data = json.loads(respose.text)
            await ctx.send(data["url"])
        else:
            await ctx.send("This channel has to have nsfw enabled!")

    @nsfw.command(name="boobs", description="Sending a boobs gif.")
    async def boobs(self, ctx):
        if ctx.channel.is_nsfw():
            respose = requests.get("https://nekos.life/api/v2/img/boobs")
            data = json.loads(respose.text)
            await ctx.send(data["url"])
        else:
            await ctx.send("This channel has to have nsfw enabled!")

    @nsfw.command(name="anal", description="Sending a anal gif.")
    async def anal(self, ctx):
        if ctx.channel.is_nsfw():
            respose = requests.get("https://nekos.life/api/v2/img/anal")
            data = json.loads(respose.text)
            await ctx.send(data["url"])
        else:
            await ctx.send("This channel has to have nsfw enabled!")

    @nsfw.command(name="pussy", description="Sending a pussy gif.")
    async def pussy(self, ctx):
        if ctx.channel.is_nsfw():
            respose = requests.get("https://nekos.life/api/v2/img/pussy")
            data = json.loads(respose.text)
            await ctx.send(data["url"])
        else:
            await ctx.send("This channel has to have nsfw enabled!")

    @nsfw.command(name="solo", description="Sending a girl masturbating gif.")
    async def solo(self, ctx):
        if ctx.channel.is_nsfw():
            respose = requests.get("https://nekos.life/api/v2/img/solog")
            data = json.loads(respose.text)
            await ctx.send(data["url"])
        else:
            await ctx.send("This channel has to have nsfw enabled!")

    @nsfw.command(name="blowjob", description="Sending a blowjob gif.")
    async def blowjob(self, ctx):
        if ctx.channel.is_nsfw():
            respose = requests.get("https://nekos.life/api/v2/img/bj")
            data = json.loads(respose.text)
            await ctx.send(data["url"])
        else:
            await ctx.send("This channel has to have nsfw enabled!")

    @nsfw.command(name="lesbian", description="Sending a lesbian gif.")
    async def lesbian(self, ctx):
        if ctx.channel.is_nsfw():
            respose = requests.get("https://nekos.life/api/v2/img/les")
            data = json.loads(respose.text)
            await ctx.send(data["url"])
        else:
            await ctx.send("This channel has to have nsfw enabled!")

def setup(bot):
    bot.add_cog(Nsfw(bot))