import discord
from discord.ext import commands
from discord.ext.tasks import loop
import os
import psycopg2
from discord_slash import SlashCommand
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")

file_handler = logging.FileHandler("bot.log")
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


initial_cogs = ['cogs.music',
                'cogs.moderation', 
                'cogs.giveaway',
                'cogs.genshin', 
                'cogs.memes', 
                'cogs.server',  
                'cogs.welcome', 
                'cogs.activities', 
                'cogs.levels',
                'cogs.admin',
                ]

DB_NAME = os.getenv("DB_NAME")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")

TOKEN = os.getenv("TOKEN")


def private_message(ctx):
    if ctx.guild is None:
        raise commands.NoPrivateMessage()
        return False
    return True


class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    def get_prefix(self, message):
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        cur.execute(f"SELECT guild_prefix FROM prefix WHERE guild_id = '{message.guild.id}'")
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if result is None: return ';'
        else: return result[0]

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help Command", colour=discord.Colour.blue())
        try:
            for cog in mapping:
                embed.add_field(name=f"{cog.qualified_name}", value=f"{', '.join([command.name for command in mapping[cog]])}", inline=True)
            
        except commands.errors.CommandInvokeError as e:
            logger.exception(e)
            pass
        except AttributeError as e:
            # logger.exception(e)
            pass
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(title=f"{cog.qualified_name} cog commands", description=f"use the command help with a command name specified in here.", colour=discord.Colour.blue())
        for command in cog.get_commands():
            embed.add_field(name=f"{command.name}", value=f"{command.description}", inline=False)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=f"{group.name} commands", description=f"use the command help with a command name specified in here.", colour=discord.Colour.blue())
        for index, command in enumerate(group.commands):
            embed.add_field(name=f"{command.name}", value=f"{command.description}", inline=False)
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=f"{command.name}", description=f"{self.get_prefix(self.get_destination())}[{command.name}{'' if len(command.aliases) == 0 else ' | ' + ' | '.join(command.aliases)}] <{', '.join([param for param in command.clean_params.keys()]) if command.clean_params != {} else 'None'}>",
        colour=discord.Colour.blue())
        await self.get_destination().send(embed=embed)


def get_prefix(client, message):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT guild_prefix FROM prefix WHERE guild_id = '{message.guild.id}'")
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if result is None: return ';'
        else: return result[0]
    except AttributeError as e:
        return ';'


class Syntax(commands.Bot):
    def __init__(self):
        intents = discord.Intents(
            guilds=True,
            members=True,
            bans=True,
            emojis=True,
            voice_states=True,
            messages=True,
            reactions=True,
        )
        allowed_mentions = discord.AllowedMentions(roles=False, everyone=False, users=True)
        super().__init__(command_prefix=get_prefix, help_command=CustomHelpCommand(), intents=intents,
                         allowed_mentions=allowed_mentions)

    @loop(seconds=30)
    async def status(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{sum([x.member_count for x in self.guilds])} users"))  

    async def on_ready(self):
        self.status.start()
        logger.info(f'{self.user} is online')
        try:
            for ext in initial_cogs:
                self.load_extension(ext)
        except Exception as e:
            print(e)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(error)
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(error)
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(error)

    async def on_guild_remove(self, guild):
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        cur.execute(f"DELETE FROM prefix WHERE guild_id = '{guild.id}'")
        conn.commit()
        cur.close()
        conn.close()


client = Syntax()
slash = SlashCommand(client, sync_commands=True)


if __name__ == '__main__':
    client.run(os.getenv('TOKEN'))
