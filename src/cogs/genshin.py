import discord
from discord.ext import commands
import requests
from bot import logger, private_message

class Genshin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Genshin impact Cog loaded")
        self.colour_dict = {5: discord.Colour.gold(), 4: discord.Colour.purple(), 3: discord.Colour.blue(), 2: discord.Colour.green(), 1: discord.Colour.light_gray()}

    @commands.group(invoke_without_command=True, description="Genshin impact group commands.")
    @commands.check(private_message)
    async def genshin(self, ctx):
        pass

    @genshin.group(name="character", description="Sending genshin impact character data")
    async def character(self, ctx, character: str):
        response = requests.get(f"https://api.genshin.dev/characters/{character.lower()}")
        if response.status_code == 404:
            raise commands.BadArgument(message=f"no character named {character}.")
        json = response.json()
        embed = discord.Embed(title=f"{json['name']} information", description=json["description"], colour=self.colour_dict[json["rarity"]])
        embed.add_field(name="Vision", value=json["vision"], inline=True)
        embed.add_field(name="Nation", value=json["nation"], inline=True)
        embed.add_field(name="Affiliation", value=json["affiliation"], inline=True)
        embed.add_field(name="Rarity", value=json["rarity"], inline=True)
        embed.add_field(name="Constellation", value=json["constellation"], inline=True)
        embed.add_field(name="Birthday", value=json["birthday"], inline=True)
        await ctx.send(embed=embed)

    @character.error
    async def character_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"Error: `{error}`")

    @genshin.group(name="artifact", description="Sending genshin impact artifact data")
    async def artifact(self, ctx, artifact: str):
        response = requests.get(f"https://api.genshin.dev/artifacts/{artifact.lower()}")
        if response.status_code == 404:
            raise commands.BadArgument(message=f"no artifact named {artifact}.")
        json = response.json()
        embed = discord.Embed(title=f"{json['name']} information", description=json["description"], colour=self.colour_dict[json["max_rarity"]])
        embed.add_field(name="Max rarity", value=json["max_rarity"], inline=True)
        embed.add_field(name="2 piece bonus", value=json["2-piece_bonus"], inline=True)
        embed.add_field(name="4 piece bonus", value=json["4-piece_bonu"], inline=True)
        await ctx.send(embed=embed)

    @artifact.error
    async def artifact_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"Error: `{error}`")
    
        

def setup(bot):
    bot.add_cog(Genshin(bot))
