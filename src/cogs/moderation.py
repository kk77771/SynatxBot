import discord
from discord.ext import commands, tasks
import asyncio
from discord import Permissions
from discord.utils import get
import psycopg2
from bot import DB_NAME, DB_PASS, DB_HOST, DB_USER, logger, private_message


class TimeConverter(commands.Converter):
    def convert(self, ctx, argument):
        pos = ['s', 'm', 'h', 'd']

        time_dict = {"s": 1, "m": 60, "h": 3600, "d": 24 * 3600}

        # getting what type
        unit = argument[-1]

        if unit not in pos:
            return -1
        try:
            # get the value until the last num
            value = int(argument[:-1])
        except Exception as e:
            return -2

        return value * time_dict[unit]


class Moderation(commands.Cog):
    def __init__(self, client):
        self.client = client
        logger.info("Moderation Cog loaded")

    def get_prefix(self, message):
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

    @commands.command(name='kick', description="Kicking specific user.")
    @commands.has_permissions(kick_members=True)
    @commands.check(private_message)
    async def kick(self, ctx, member: commands.MemberConverter, *, reason=None):
        no_reason = 'No reason given'
        if ctx.author.top_role.position < member.top_role.position:
            await ctx.send('You can not kick users with role above you.')
        else:
            await member.send('You have been kicked from {0}, reason: {1}. {2} kicked you.'.format(ctx.guild.name, reason if reason is not None else no_reason, ctx.author.mention))
            await member.kick(reason=reason)
            await ctx.send('Kicked {0}. Reason: {1}'.format(member.mention, reason if reason is not None else no_reason, ctx.author.mention))

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.mention}, wrong syntax use: {self.get_prefix(ctx.guild.id)}kick <user> <reason>.')

    @commands.command(name='ban', description="Banning specific user.")
    @commands.has_permissions(ban_members=True)
    @commands.check(private_message)
    async def ban(self, ctx, member: commands.MemberConverter, *, reason=None):
        no_reason = 'No reason given.'
        if ctx.author.top_role.position < member.top_role.position:
            await ctx.send('You can not kick users with role above you.')
        else:
            await member.send('You have been banned from {0}, reason: {1}. {2} banned you.'.format(ctx.guild.name, reason if reason is not None else no_reason, ctx.author.mention))
            await member.ban(reason=reason)
            await ctx.send('Banned {0}. Reason: {1}'.format(member.mention, reason if reason is not None else no_reason, ctx.author.mention))
        
    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.mention}, wrong syntax use: {self.get_prefix(ctx.guild.id)}ban <user> <reason>.')

    @commands.command(name='unban', description="Unbanning specific user.")
    @commands.has_permissions(ban_members=True)
    @commands.check(private_message)
    async def unban(self, ctx, user: commands.UserConverter):
        await ctx.guild.unban(user)
        await ctx.send('Unbanned {0}.'.format(user.name))

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            await ctx.send('The user is not banned.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.mention}, wrong syntax use: {self.get_prefix(ctx.guild.id)}unban <user>')

    @commands.command(name='clear', pass_context=True, aliases=['purge'], description="Deleting sum of messages.")
    @commands.has_permissions(manage_messages=True)
    @commands.check(private_message)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount)

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.mention}, wrong syntax use: {self.get_prefix(ctx.guild.id)}clear <amount of messages>')

    @commands.command(name='warn', description="Warning specific user.")
    @commands.has_permissions(manage_messages=True)
    @commands.check(private_message)
    async def warn(self, ctx, member: commands.MemberConverter, *, reason=None):
        print('warn msg')
        no_reason = 'No reason given'
        main = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cursor = main.cursor()
        cursor.execute(f"SELECT warn_case FROM main WHERE guild_id = '{ctx.guild.id}'")
        result = cursor.fetchone()
        if result is None:
            warn_case = '1'
        else:
            warn_case = f'{int(result[-1]) + 1}'
        
        sql = ("INSERT INTO main(guild_id,user_id,warn_author_id,warn_msg,warn_case) VALUES(%s,%s,%s,%s,%s)")
        val = (str(ctx.guild.id), str(member.id), str(ctx.author.id), str(reason) if reason is not None else str(no_reason), str(warn_case))
        cursor.execute(sql, val)
        await ctx.send(f'{ctx.author.mention}, warned {member.mention} reason: {reason if reason is not None else no_reason}, case = {warn_case}')
        await member.send(f'you were warned in {ctx.guild.name}. Reason: {reason if reason is not None else no_reason}')
        main.commit()
        cursor.close()
        main.close()

    '''
    @commands.command(name='warns')
    @commands.has_permissions(manage_messages=True)
    async def warns(self, ctx, member: discord.Member):
        main = sqlite3.connect('main.sqlite')
        cur = main.cursor()
        cur.execute(f"SELECT warn_case, warn_msg, warn_author_id FROM main WHERE guild_id = '{ctx.guild.id}' and user_id = '{member.id}'")
        result = cur.fetchone()
        if result is None:
            await ctx.send("This user does not have any warns.")
        else:
            print(result)
    '''

    @commands.command(name='nuke', description="Nuking channel.")
    @commands.has_permissions(administrator=True)
    @commands.check(private_message)
    async def nuke(self, ctx):
        def check(m):
            return m.author.id == ctx.message.author.id and m.channel == ctx.channel
        await ctx.send('Are you sure you want to nuke this room? yes/no.')
        answer = await self.client.wait_for('message', check=check)
        if answer.content == 'yes':
            await ctx.channel.delete()
            nuked_channel = await ctx.channel.clone()
            nuked_msg = await nuked_channel.send('Channel nuked\nhttps://tenor.com/view/explosion-explode-clouds-of-smoke-gif-17216934')
            await asyncio.sleep(5)
            await nuked_msg.delete()
        elif answer.content == 'no':
            await ctx.send("cancelled.")
        else:
            await ctx.send('You troller.')

    # TODO: Fix this shit bug with mute_members

    @commands.command(name="mute", description="Giving muted role to specific user.")
    @commands.has_permissions(manage_roles=True)
    @commands.check(private_message)
    async def mute(self, ctx, member: commands.MemberConverter, *, reason=None):
        if ctx.author.top_role.position > member.top_role.position:
            mute_role = get(ctx.guild.roles, name="Muted")
            if mute_role is None:
                mute_role = await ctx.guild.create_role(name='Muted')
                perms = Permissions()
                perms.update(send_messages=False, send_tts_messages=False)
                await mute_role.edit(reason=None, permissions=perms)
                await member.add_roles(mute_role)
                await ctx.send(f"Muted: {member.mention}, reason: {'None' if reason is None else ''.join(reason)}.")
                for channel in ctx.guild.text_channels:
                    await channel.set_permissions(mute_role, send_messages=False)
            else:
                await member.add_roles(mute_role)
                await ctx.send(f"Muted: {member.mention}, reason: {'None' if reason is None else ''.join(reason)}.")
        else:
            await ctx.send("You cannot mute someone with role above you.")

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You must mention the member you want to mute.")

    @commands.command(name='unmute', description="Unmuting specific user.")
    @commands.has_permissions(manage_roles=True)
    @commands.check(private_message)
    async def unmute(self, ctx, member: commands.MemberConverter):
        if ctx.author.top_role.position > member.top_role.position:
            mute_role = get(ctx.guild.roles, name="Muted")
            await member.remove_roles(mute_role)
            await ctx.send(f"Unmuted: {member.mention}.")
        else:
            await ctx.send("You cannot unmute someone with role above you.")

    @unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You must mention the member you want to unmute.")


def setup(client):
    client.add_cog(Moderation(client))
    
