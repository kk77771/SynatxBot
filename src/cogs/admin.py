import discord
from discord.ext import commands
from bot import logger


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Admin Cog loaded")

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(name="load", hidden=True)
    async def _load(self, ctx, module):
        try:
            self.bot.load_extension(f"cogs.{module}")
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')

    @commands.command(name="unload", hidden=True)
    async def _unload(self, ctx, module):
        try:
            self.bot.unload_extension(f"cogs.{module}")
            await ctx.send(f"Unload cogs.{module}")
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')

    @commands.command(name="reload", hidden=True, invoke_without_command=True)
    async def _reload(self, ctx, module):
        try:
            self.bot.reload_extension(f"cogs.{module}")
            await ctx.send(f"Reload cogs.{module}")
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')


def setup(bot):
    bot.add_cog(Admin(bot))
