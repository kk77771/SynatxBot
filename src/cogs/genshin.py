import discord
from discord.ext import commands
import requests
from bot import logger, private_message

class Genshin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Genshin impact Cog loaded")

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
        embed = discord.Embed(title=f"{json['name']} information", description=json["description"], colour=discord.Colour.gold() if json["rarity"] == 5 else discord.Colour.purple())
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
    
        

def setup(bot):
    bot.add_cog(Genshin(bot))
