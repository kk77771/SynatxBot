import discord
from discord.ext import commands
from discord import Embed
import requests
import json
from bot import TOKEN, logger, private_message
from discord_slash import SlashCommand, SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option, create_choice


class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Activities Cog loaded")

    @cog_ext.cog_slash(name='activity',
        description='Start or join a vc activity.', 
        options=[
        create_option(
            name="activity_type",
            description="Activity Type",
            required=True,
            option_type=3,
            choices=[
                create_choice(
                    name="Youtube Together",
                    value="ytt"
                ),
                create_choice(
                    name="Poker Night",
                    value="poker-night"
                ),
                create_choice(
                    name="Betrayal.io",
                    value="betrayal"
                ),
                create_choice(
                    name="Fishington.io",
                    value="fishington"
                ),
                create_choice(
                    name="Chess",
                    value="chess"
                )
            ]
        )
    ])
    async def activity(self, ctx: SlashContext, activity_type: str):
        data = {"ytt": "755600276941176913", "poker-night": "755827207812677713", "betrayal": "773336526917861400",
        "fishington": "814288819477020702", "chess": "832012586023256104"}
        channel = ctx.author.voice.channel
        if channel is None:
            await ctx.send("You have to be in vc.")
            return
        body = json.dumps({
                "max_age": 100000,
                "max_uses": 0,
                "target_application_id": data[activity_type],
                "target_type": 2,
                "temporary": False,
                "validate": None
                    })
        response = requests.post(f"https://discord.com/api/v8/channels/{channel.id}/invites", data=body,
                                    headers={
                                        "Authorization": f"Bot {TOKEN}",
                                        "Content-Type": "application/json",
                                    })
        res = response.json()
        if res["code"] is None:
            await ctx.send("Sadly I can't start youtube together.")
            return
        embed = Embed()
        embed.description = f"[Click Here to join {activity_type}](https://discord.com/invite/{res['code']})"
        await ctx.send(embed=embed)

    @commands.command(name='activity', description="Sending activity link for you connected channel.")
    @commands.check(private_message)
    async def activity(self, ctx, activity_type):
        data = {"ytt": "755600276941176913", "poker-night": "755827207812677713", "betrayal": "773336526917861400",
        "fishington": "814288819477020702", "chess": "832012586023256104"}
        channel = ctx.author.voice.channel
        if channel is None:
            await ctx.send("You have to be in vc.")
            return
        body = json.dumps({
                "max_age": 100000,
                "max_uses": 0,
                "target_application_id": data[activity_type],
                "target_type": 2,
                "temporary": False,
                "validate": None
                    })
        response = requests.post(f"https://discord.com/api/v8/channels/{channel.id}/invites", data=body,
                                    headers={
                                        "Authorization": f"Bot {TOKEN}",
                                        "Content-Type": "application/json",
                                    })
        res = response.json()
        if res["code"] is None:
            await ctx.send("Sadly I can't start youtube together.")
            return
        embed = Embed()
        embed.description = f"[Click Here to join {activity_type}](https://discord.com/invite/{res['code']})"
        await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(Activities(bot))
