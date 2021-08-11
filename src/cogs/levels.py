import discord
from discord import colour
from discord.ext import commands, tasks
import asyncio
from discord.utils import get
import logging
import psycopg2
from bot import DB_NAME, DB_PASS, DB_HOST, DB_USER, logger, private_message


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Levels Cog loaded")

    def get_prefix(self, message):
        try:
            conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
            cur = conn.cursor()
            cur.execute(f"SELECT guild_prefix FROM prefix WHERE guild_id = '{message.guild.id}'")
            result = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            if result is None:
                return ';'
            else:
                return result[0]
        except AttributeError as e:
            return ';'

    @commands.command(name='rank', description="Getting specific user rank.")
    @commands.check(private_message)
    async def rank(self, ctx, memeber: discord.Member = None):
        main = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = main.cursor()
        if memeber is None:
            cur.execute(f"SELECT xp FROM levels WHERE guild_id = '{ctx.guild.id}' AND user_id = '{ctx.author.id}'")
            result = cur.fetchone()
            cur.execute(f"SELECT level FROM levels WHERE guild_id = '{ctx.guild.id}' AND user_id = '{ctx.author.id}'")
            result2 = cur.fetchone()
            if result is None:
                return await ctx.send(f"{ctx.author.mention} don't have any xp.")
            await ctx.send(f"{ctx.author.mention}, level: {result2[0]} xp: {result[0]}/{100 * (int(result2[0]) + 1) if result2[0] != 0 else 100}")
        else:
            cur.execute(f"SELECT xp FROM levels WHERE guild_id = '{memeber.guild.id}' AND user_id = '{memeber.id}'")
            result = cur.fetchone()
            cur.execute(f"SELECT level FROM levels WHERE guild_id = '{memeber.guild.id}' AND user_id = '{memeber.id}'")
            result2 = cur.fetchone()
            if result is None:
                return await ctx.send(f"{memeber.ention} don't have any xp.")
            await ctx.send(f"{memeber.mention}, level: {result2[0]} xp: {result[0]}/{100 * (int(result2[0]) + 1) if result2[0] != 0 else 100}")

    # @commands.command(name="top", description="Returns the leaderboard for the users in the top.", aliases=["leaderboard"])
    # async def top(self, ctx):
    #     conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    #     cur = conn.cursor()
    #     cur.execute(f"SELECT level FROM levels WHERE guild_id = '{ctx.guild.id}'")
    #     levels = cur.fetchall()
    #     embed = discord.Embed(title=f"{ctx.guild.name} top", colour=discord.Colour.green())
    #     description = ""
    #     levels_data = [int(list(data)[0]) for data in levels]
    #     levels_data.sort(reverse=True)
    #     top_ten = levels_data[:10]
    #     for level in top_ten:
    #         cur.execute(f"SELECT xp, user_id FROM levels WHERE guild_id = '{ctx.guild.id}' AND level = '{level}'")
    #         result = cur.fetchall()
    #         print(result)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content.startswith(self.get_prefix(message)):
            return
        if message.content.startswith("https://"):
            return
        if not message.channel:
            return

        try:
            main = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
            cur = main.cursor()
            cur.execute(f"SELECT xp FROM levels WHERE guild_id = '{message.guild.id}' AND user_id = '{message.author.id}'")
            result = cur.fetchone()
            cur.execute(f"SELECT level FROM levels WHERE guild_id = '{message.guild.id}' AND user_id = '{message.author.id}'")
            result2 = cur.fetchone()
            if result is None:
                current_xp = len(message.content) if len(message.content) <= 100 else 70
                sql = ("INSERT INTO levels(xp, level, user_id, guild_id) VALUES(%s,%s,%s,%s)")
                val = (current_xp, 0, message.author.id, message.guild.id)
            else:
                current_level = int(result2[0])
                current_xp = int(result[0]) + 5
                if current_xp >= ( 100 if current_level == 0 else current_level * 100):
                    current_level += 1
                    current_xp = 0
                    await message.channel.send(f"{message.author.mention}, ranked up.")

                sql = ("UPDATE levels SET xp = %s, level = %s WHERE user_id = %s AND guild_id = %s")
                val = (current_xp, current_level, str(message.author.id), str(message.guild.id))

            cur.execute(sql, val)
            main.commit()
            cur.close()
            main.close()
        except AttributeError as e:
            return


def setup(bot):
    bot.add_cog(Levels(bot))
