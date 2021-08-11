import discord
from discord.ext import commands
from discord import Embed
from discord.utils import get
import datetime
import psycopg2
from bot import DB_NAME, DB_PASS, DB_HOST, DB_USER, logger, private_message


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Welcome Cog loaded")

    @commands.group(invoke_without_command=True, description="Welcome group command")
    @commands.check(private_message)
    async def welcome(self, ctx):
        await ctx.send("Welcome commands: set_channel, set_message, message_type and auto_role")

    @welcome.command(name='channel', aliases=['setChannel'], description="Setting the welcomew channel where all the messages will be sent.")
    @commands.has_permissions(manage_guild=True)
    @commands.check(private_message)
    async def channel(self, ctx):
        async def ask_channel():
            def check(m):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
            
            try:
                msg = await self.bot.wait_for("message", check=check)
                return await commands.TextChannelConverter().convert(ctx, msg.content)
            except commands.errors.ChannelNotFound as e:
                await ctx.send(f"Invalid channel `{e.argument}`. Please enter a channel name again.")
                return await ask_channel()

        await ctx.send("Please enter the channel name where all the welcome messages will be sent.")
        channel = await ask_channel()

        main = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = main.cursor()
        cur.execute(f"SELECT channel_id FROM welcome WHERE guild_id = '{ctx.guild.id}'")
        result = cur.fetchone()

        if result is None:
            sql = ("INSERT INTO welcome(guild_id, channel_id) VALUES(%s,%s)")
            val = (str(ctx.guild.id), channel.id)
        else:
            sql = ("UPDATE welcome SET channel_id = %s WHERE guild_id = %s")
            val = (channel.id, str(ctx.guild.id))

        cur.execute(sql, val)
        main.commit()
        cur.close()
        main.close()
        await ctx.send(f"Set welcome channel to: {channel.mention}")

    @welcome.command(name='set_message', aliases=['set_msg', 'setMessage', 'text', 'message'], description="Setting the welcome message.")
    @commands.has_permissions(manage_guild=True)
    @commands.check(private_message)
    async def set_message(self, ctx):
        async def ask_msg():
            def check(m):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            message = await self.bot.wait_for("message", check=check)

            return message.content

        await ctx.send("Please enter the message that will show up for every welcome message.")
        message = await ask_msg()

        main = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = main.cursor()
        cur.execute(f"SELECT msg FROM welcome WHERE guild_id = '{ctx.guild.id}'")
        result = cur.fetchone()
        if result is None:
            sql = ("INSERT INTO welcome(guild_id, msg) VALUES(%s,%s)")
            val = (str(ctx.guild.id), message)
        else:
            sql = ("UPDATE welcome SET msg = %s WHERE guild_id = %s")
            val = (message, str(ctx.guild.id))
        cur.execute(sql, val)
        main.commit()
        cur.close()
        main.close()
        await ctx.send(f"Message has been set: `{message}`")

    @welcome.command(name='message_type', aliases=['msg_type', 'MessageType', 'type'], description="Setting welcome message type embed or text.")
    @commands.has_permissions(manage_guild=True)
    @commands.check(private_message)
    async def message_type(self, ctx):
        async def ask_type():
            def check(m):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            msg_type = await self.bot.wait_for("message", check=check)

            if msg_type.content.lower() != "embed" and msg_type.content.lower() != "text":
                await ctx.send("Invalid type! You only have 2 types of messages: embed and text. Please a message type again.")
                return await ask_type()
            return msg_type.content.lower()

        await ctx.send("Please enter the message type that will show up for every welcome message. (text | embed)")
        msg_type = await ask_type()


        main = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = main.cursor()
        cur.execute(f"SELECT msg_type FROM welcome WHERE guild_id = '{ctx.guild.id}'")
        result = cur.fetchone()
        if result is None:
            sql = ("INSERT INTO welcome(guild_id, msg_type) VALUES(%s,%s)")
            val = (str(ctx.guild.id), msg_type)
        else:
            sql = ("UPDATE welcome SET msg_type = %s WHERE guild_id = %s")
            val = (msg_type, str(ctx.guild.id))
        cur.execute(sql, val)
        main.commit()
        cur.close()
        main.close()
        await ctx.send(f"Welcome message type has been set: `{msg_type}`")

    @welcome.command(name='auto_role', aliases=['auto_roles', 'autoRoles'], description="Setting auto role that will be given to a new users.")
    @commands.has_permissions(manage_guild=True)
    @commands.check(private_message)
    async def auto_role(self, ctx, *, roles_id=None):
        main = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = main.cursor()
        cur.execute(f"SELECT roles_id FROM welcome WHERE guild_id = '{ctx.guild.id}'")
        result = cur.fetchone()
        if result is None:
            cur.execute(f"INSERT INTO welcome(roles_id, guild_id) VALUES(%s,%s)", (f"{roles_id}", f"{ctx.guild.id}"))
        else:
            cur.execute("UPDATE welcome SET roles_id = %s WHERE guild_id = %s", (f"{roles_id}", f"{ctx.guild.id}"))
        main.commit()
        cur.close()
        main.close()
        await ctx.send(f"Welcome roles id's set to: {roles_id}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        main = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = main.cursor()
        cur.execute(f"SELECT channel_id FROM welcome WHERE guild_id = '{member.guild.id}'")
        result = cur.fetchone()
        if result is None:
            return
        else:
            cur.execute(f"SELECT roles_id FROM welcome WHERE guild_id = '{member.guild.id}'")
            result3 = cur.fetchone()
            try:
                for role_id in result3[0].split(" "):
                    role = get(member.guild.roles, id=int(role_id))
                    await member.add_roles(role)
            except AttributeError as e:
                pass
            except ValueError:
                pass

            members_count = member.guild.member_count
            mention = member.mention
            user = member.name
            guild = member.guild.name
            cur.execute(f"SELECT msg_type FROM welcome WHERE guild_id = '{member.guild.id}'")
            result1 = cur.fetchone()
            cur.execute(f"SELECT msg FROM welcome WHERE guild_id = '{member.guild.id}'")
            result2 = cur.fetchone()
            if result1 is None:
                if result2 is None:
                    embed = Embed(
                        description=f"Welcome to my server! your are the {member.guild.member_count} member in the server")
                else:

                    embed = Embed(
                        description=f"{result2[0]}".format(
                            members_count=members_count, mention=mention, user=user, guild=guild))
                embed.set_thumbnail(url=f"{member.avatar_url}")
                embed.set_author(name=f"{member.name}", icon_url=f"{member.avatar_url}")
                embed.set_footer(text=f"{member.guild}", icon_url=f"{member.guild.icon_url}")
                embed.timestamp = datetime.datetime.utcnow()
                channel = self.bot.get_channel(id=int(result[0]))

                await channel.send(embed=embed)
            else:
                if result1[0].lower() == "embed":
                    if result2 is None:
                        embed = Embed(
                            description=f"Welcome to my server! your are the {member.guild.member_count} member in the server")
                    else:
                        embed = Embed(
                            description=f"{result2[0]}".format(
                                members_count=members_count, mention=mention, user=user, guild=guild))
                    embed.set_thumbnail(url=f"{member.avatar_url}")
                    embed.set_author(name=f"{member.name}", icon_url=f"{member.avatar_url}")
                    embed.set_footer(text=f"{member.guild}", icon_url=f"{member.guild.icon_url}")
                    embed.timestamp = datetime.datetime.utcnow()
                    channel = self.bot.get_channel(id=int(result[0]))
                    await channel.send(embed=embed)
                else:
                    channel = self.bot.get_channel(id=int(result[0]))
                    await channel.send(f"{result2[0]}".format(members_count=members_count, mention=mention, user=user, guild=guild))

        cur.close()
        main.close()


def setup(bot):
    bot.add_cog(Welcome(bot))
