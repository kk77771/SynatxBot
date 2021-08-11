import discord
from discord.ext import commands
from discord import Embed
import asyncio
import random
from datetime import datetime
from bot import logger, private_message


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Giveaway Cog loaded")

    @commands.command(name='gstart', aliases=["giveaway_start", "gs"], description="Starting giveaway.")
    @commands.has_permissions(manage_guild=True)
    @commands.check(private_message)
    async def gstart(self, ctx, time: str = None, *, prize: str = None):
        def convert(time):
            pos = ['s', 'm', 'h', 'd']

            time_dict = {"s": 1, "m": 60, "h": 3600, "d": 24*3600}

            # getting what type
            unit = time[-1]

            if unit not in pos:
                return -1
            try:
                # get the value until the last num
                value = int(time[:-1])
            except Exception as e:
                return -2

            return value * time_dict[unit]

        if time is None and prize is None:
            questions = ["How much time do you want the giveaway to be continued (s | m | h | d)?",
                         "What prize do you want for the giveaway ?"]
            answers = []

            def check(m):
                return m.author.id == ctx.message.author.id and m.channel == ctx.channel

            await ctx.send("Answer this questions.")
            for question in questions:
                await ctx.send(question)
                answer = await self.bot.wait_for('message', check=check)
                answers.append(answer.content)

            time = convert(answers[0])
            if time == -1:
                await ctx.send(f"You did not answer the time with a proper units. Use (s | m | h | d)")
                return
            elif time == -2:
                await ctx.send(f"The time must be an integer. Please enter an integer next time.")
                return

            prize = answers[1]

            embed = Embed(title=prize, colour=discord.Colour.blue())
            embed.description = f"React with 🎉 to enter!\nEnds {convert(answers[0])}s from {str(datetime.utcnow()).split('.')[0]}\nHosted by: {ctx.author.mention}"
            msg = await ctx.send(embed=embed)

            await msg.add_reaction("🎉")

            await asyncio.sleep(time)

            new_msg = await ctx.fetch_message(msg.id)
            users = await new_msg.reactions[0].users().flatten()
            users.pop(users.index(self.bot.user))

            try:
                winner = random.choice(users)
            except Exception as e:
                await ctx.send("No one has been participant in the giveaway.")
                return

            await ctx.send(f"Congratulations! {winner.mention} won {prize}.")

        else:
            giveaway_time = convert(time)
            embed = Embed(title=prize, colour=discord.Colour.blue())
            embed.description = f"React with 🎉 to enter!\nEnds {time} from {str(datetime.utcnow()).split('.')[0]}\nHosted by: {ctx.author.mention}"

            msg = await ctx.send(embed=embed)
            await msg.add_reaction("🎉")

            await asyncio.sleep(giveaway_time)

            new_msg = await ctx.fetch_message(msg.id)
            users = await new_msg.reactions[0].users().flatten()
            users.pop(users.index(self.bot.user))

            try:
                winner = random.choice(users)
            except Exception as e:
                await ctx.send("No one has been participant in the giveaway.")
                return

            await ctx.send(f"Congratulations! {winner.mention} won {prize}.")

    @commands.command(name='reroll', description="rerolling giveaway")
    @commands.has_permissions(manage_messages=True)
    @commands.check(private_message)
    async def reroll(self, ctx, id_: int, channel: discord.TextChannel = None):
        if channel is None:
            msg = await ctx.fetch_message(id_)
            users = await msg.reactions[0].users().flatten()
            users.pop(users.index(self.bot.user))

            try:
                winner = random.choice(users)
            except Exception as e:
                await ctx.send("No one has been participant in the giveaway.")
                return

            await ctx.send(f"Congratulations! {winner.mention} won!")
        else:
            msg = await channel.fetch_message(id_)
            users = await msg.reactions[0].users().flatten()
            users.pop(users.index(self.bot.user))

            try:
                winner = random.choice(users)
            except Exception as e:
                await ctx.send("No one has been participant in the giveaway.")
                return

            await channel.send(f"Congratulations! {winner.mention} won!")


def setup(bot):
    bot.add_cog(Giveaway(bot))
