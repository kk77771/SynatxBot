from logging import log
import discord
from discord.ext import commands
import praw
import random
from bot import logger, client_id, client_secret, user_agent


class Memes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reddit = praw.Reddit(
            client_id='client_id',
            client_secret='client_secret',
            user_agent='user_agent',
            check_for_async=False)
        self.subreddit = self.reddit.subreddit('memes')
        logger.info("Memes Cog loaded")
        
    @commands.command(name="meme", description="Sending random meme from specific subreddit.")
    async def meme(self, ctx, sub_reddit=None):
        if sub_reddit is None:
            submissions_links = []
            for submission in self.subreddit.hot(limit=25):
                submissions_links.append(submission.url)
            await ctx.send(random.choice(submissions_links))
        else:
            try:
                self.subreddit = self.reddit.subreddit(sub_reddit)
                submissions_links = []
                for submission in self.subreddit.hot(limit=25):
                    submissions_links.append(submission.url)
                await ctx.send(random.choice(submissions_links))
            except Exception as e:
                await ctx.send("Invalid sub reddit.")


def setup(bot):
    bot.add_cog(Memes(bot))
