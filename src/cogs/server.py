import discord
from discord.ext import commands
import psycopg2
from bot import DB_NAME, DB_PASS, DB_HOST, DB_USER, logger, private_message


class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Server Cog loaded")

    def get_prefix(self, guild_id):
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        cur.execute(f"SELECT guild_prefix FROM prefix WHERE guild_id = '{guild_id}'")
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if result is None:
            return ';'
        else:
            return result[0]

    @commands.command(name='change_prefix', aliases=["set_prefix"], description="Changing server deafult prefix ;")
    @commands.has_permissions(administrator=True)
    @commands.check(private_message)
    async def change_prefix(self, ctx, prefix):
        if len(prefix) > 2: await ctx.send("Your prefix must be smaller or equal to 2 letters.")
        else:
            main = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
            cur = main.cursor()
            cur.execute(f"SELECT guild_prefix FROM prefix WHERE guild_id = '{ctx.guild.id}'")
            result = cur.fetchone()
            if result is None:
                sql = ("INSERT INTO prefix(guild_prefix, guild_id) VALUES(%s,%s)")
                val = (prefix, str(ctx.guild.id))
            else:
                sql = ("UPDATE prefix SET guild_prefix = %s WHERE guild_id = %s")
                val = (prefix, str(ctx.guild.id))
            await ctx.send(f"Prefix changed to `{prefix}`.")
            cur.execute(sql, val)
            main.commit()
            cur.close()
            main.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content == "<@!744552627878232085>":
            await message.channel.send(f"My Prefix is: `{self.get_prefix(message.guild.id)}`")


def setup(bot):
    bot.add_cog(Server(bot))
