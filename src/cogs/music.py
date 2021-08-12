import discord
import requests
from discord.ext import commands
import lavalink
from discord import utils
from discord import Embed
import asyncio # Maybe ?
import re
import psycopg2
from bot import DB_NAME, DB_PASS, DB_HOST, DB_USER, private_message
import json


def is_correct_channel(ctx):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor()
    cur.execute(f"SELECT channel_id FROM music WHERE guild_id = '{ctx.guild.id}'")
    channel_id = cur.fetchone()
    if channel_id is None:
        return True

    if int(ctx.channel.id) == int(channel_id[0]):
        return True

    return False


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.music = lavalink.Client(self.bot.user.id)
        self.bot.music.add_node("localhost", 6969, "Pa$sw0rd", "eu", "syntax-music")
        self.bot.add_listener(self.bot.music.voice_update_handler, "on_socket_response")
        self.bot.music.add_event_hook(self.track_hook)
        self.url_rx = re.compile(r'https?://(?:www\.)?.+')


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

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = int(event.player.guild_id)
            await self.connect_to(guild_id, None)
        if isinstance(event, lavalink.events.TrackStartEvent):
            main = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
            cur = main.cursor()
            guild_id = event.player.fetch('guild')
            cur.execute(f"SELECT vol FROM music WHERE guild_id = '{guild_id}'")
            result = cur.fetchone()
            if result is not None: await event.player.set_volume(int(result[0]))
            else: await event.player.set_volume(100)
            channel_id = event.player.fetch('channel')
            channel = self.bot.get_channel(channel_id)
            await channel.send(f"Playing: {event.player.current.title}")
            cur.close()
            main.close()

    async def connect_to(self, guild_id: int, channel_id: str):
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)

    def get_channel(self, ctx):
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        cur.execute(f"SELECT channel_id FROM music WHERE guild_id = '{ctx.guild.id}'")
        channel_id = cur.fetchone()
        return self.bot.get_channel(id=int(channel_id[0]))

    @commands.command(name="join", aliases=['j'], description="Joining your vc.")
    @commands.check(is_correct_channel)
    async def join(self, ctx):
        member = utils.find(lambda m: m.id == ctx.author.id, ctx.guild.members)
        if member is not None and member.voice is not None:
            vc = member.voice.channel
            player = self.bot.music.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
            if not player.is_connected:
                player.store('channel', ctx.channel.id)
                await self.connect_to(ctx.guild.id, str(vc.id))
                await ctx.send('Connected.')
                await ctx.guild.change_voice_state(channel=vc, self_deaf=True)

    @join.error
    async def join_error(self, ctx, error):
        channel = self.get_channel(ctx)
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f"You cannot write music commands in {ctx.channel.mention} channel. You have to use {channel.mention}.")

    @commands.command(name="dc", aliases=['disconnect', 'leave', 'fuckoff'], description="Disconnecting from vc.")
    @commands.check(is_correct_channel)
    async def dc(self, ctx):
        try:
            # self.bot.music.player_manager.remove(ctx.guild.id)
            await self.connect_to(ctx.guild.id, None)
            await ctx.send('Left channel.')
        except Exception as e:
            print(e)
            await ctx.send("You are not connected to a vc!")

    @dc.error
    async def dc_error(self, ctx, error):
        channel = self.get_channel(ctx)
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f"You cannot write music commands in {ctx.channel.mention} channel. You have to use {channel.mention}.")

    @commands.command(name='play', aliases=['p'], description="Playing a requested song.")
    @commands.check(is_correct_channel)
    async def play(self, ctx, *, query):
        # TODO: design songs embed
        try:
            member = utils.find(lambda m: m.id == ctx.author.id, ctx.guild.members)
            if member is not None and member.voice is not None:
                vc = member.voice.channel
                player = self.bot.music.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
                if not player.is_connected:
                    player.store('channel', ctx.channel.id)
                    player.store('guild', ctx.guild.id)
                    await self.connect_to(ctx.guild.id, str(vc.id))
                    await ctx.send('Connected.')
                    await ctx.guild.change_voice_state(channel=vc, self_deaf=True)
                    ## PLAY SECTION ##
                    player = self.bot.music.player_manager.get(ctx.guild.id)
                    query = query.strip("<>")
                    if not self.url_rx.match(query):
                        query = f'ytsearch:{query}'

                    results = await player.node.get_tracks(query)
                    tracks = results['tracks'][0:10]
                    i = 0
                    query_result = ''
                    for track in tracks:
                        i += 1
                        query_result = query_result + f'{i}) {track["info"]["title"]} - {track["info"]["uri"]}\n'
                    embed = Embed()
                    embed.description = query_result

                    await ctx.channel.send(embed=embed)

                    def check(m):
                        return m.author.id == ctx.author.id and m.channel == ctx.channel
                    
                    response = await self.bot.wait_for('message', check=check)
                    track = tracks[int(response.content)-1]

                    player.add(requester=ctx.author.id, track=track)
                    if not player.is_playing:
                        await player.play()
                else:
                    player = self.bot.music.player_manager.get(ctx.guild.id)
                    query = f'ytsearch:{query}'
                    results = await player.node.get_tracks(query)
                    tracks = results['tracks'][0:10]
                    i = 0
                    query_result = ''
                    for track in tracks:
                        i += 1
                        query_result = query_result + f'{i}) {track["info"]["title"]} - {track["info"]["uri"]}\n'
                    embed = Embed()
                    embed.description = query_result

                    await ctx.channel.send(embed=embed)

                    def check(m):
                        return m.author.id == ctx.author.id
                    
                    response = await self.bot.wait_for('message', check=check)
                    track = tracks[int(response.content)-1]

                    player.add(requester=ctx.author.id, track=track)
                    if not player.is_playing:
                        # await ctx.send(f'Playing {tracks}')
                        await player.play()
                
        except Exception as error:
            print(error)

    @play.error
    async def play_error(self, ctx, error):
        channel = self.get_channel(ctx)
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f"You cannot write music commands in {ctx.channel.mention} channel. You have to use {channel.mention}.")

    @commands.command(name="pause", description="Pausing current playing song.")
    @commands.check(is_correct_channel)
    async def pause(self, ctx):
        try:
            player = self.bot.music.player_manager.get(ctx.guild.id)
            await player.set_pause(True)
            await ctx.send('Paused.')
        except Exception as e:
            print(e)
            await ctx.send("You are not connected to a vc!")

    @pause.error
    async def pause_error(self, ctx, error):
        channel = self.get_channel(ctx)
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f"You cannot write music commands in {ctx.channel.mention} channel. You have to use {channel.mention}.")

    @commands.command(name="resume", description="Resuming current paused song.")
    @commands.check(is_correct_channel)
    async def resume(self, ctx):
        try:
            player = self.bot.music.player_manager.get(ctx.guild.id)
            await player.set_pause(False)
            await ctx.send('Resumed.')
        except Exception as e:
            print(e)
            await ctx.send("You are not connected to a vc!")

    @resume.error
    async def resume_error(self, ctx, error):
        channel = self.get_channel(ctx)
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f"You cannot write music commands in {ctx.channel.mention} channel. You have to use {channel.mention}.")

    @commands.command(name='stop', description="Stopping current playing song.")
    @commands.check(is_correct_channel)
    async def stop(self, ctx):
        try:
            player = self.bot.music.player_manager.get(ctx.guild.id)
            await player.stop()
            await ctx.send('Stopped Playing.')
            self.bot.music.player_manager.remove(ctx.guild.id)
        except Exception as e:
            print(e)
            await ctx.send("You are not connected to a vc!")

    @stop.error
    async def stop_error(self, ctx, error):
        channel = self.get_channel(ctx)
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f"You cannot write music commands in {ctx.channel.mention} channel. You have to use {channel.mention}.")

    @commands.command(name='skip', aliases=['s'], description="Skipping to the next song in queue.")
    @commands.check(is_correct_channel)
    async def skip(self, ctx):
        try:
            player = self.bot.music.player_manager.get(ctx.guild.id)
            await player.skip()
            await ctx.send('Skipped.')
        except Exception as e:
            print(e)
            await ctx.send("You are not connected to a vc!")

    @skip.error
    async def skip_error(self, ctx, error):
        channel = self.get_channel(ctx)
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f"You cannot write music commands in {ctx.channel.mention} channel. You have to use {channel.mention}.")

    @commands.command(name='queue', aliases=['q'], description="Getting list of songs in queue.")
    @commands.check(is_correct_channel)
    async def queue(self, ctx):
        try:
            player = self.bot.music.player_manager.get(ctx.guild.id)
            queue = player.queue
            queue_list = ""
            j = 0
            for i in queue:
                j += 1
                queue_list = f"{queue_list} ({j}) {i.title}\n"
            embed = Embed(title=f"Queue for {ctx.guild.name}", color=0x3498db)
            
            if queue_list == "":
                embed.description = f"**Current: {player.current.title}**\n\nIn Queue:\nNone"
            else:
                embed.description = f"**Current: {player.current.title}**\n\nIn Queue:\n" + queue_list

            await ctx.send(embed=embed)
            
        except Exception as e:
            print(e)

    @queue.error
    async def queue_error(self, ctx, error):
        channel = self.get_channel(ctx)
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f"You cannot write music commands in {ctx.channel.mention} channel. You have to use {channel.mention}.")

    @commands.command(name='loop', aliases=['repeat'], description="Looping the current playing song.")
    @commands.check(is_correct_channel)
    async def loop(self, ctx):
        try:
            player = self.bot.music.player_manager.get(ctx.guild.id)
            if player.repeat: 
                player.repeat = False
                await ctx.send('Loop off')
            else: 
                player.repeat = True
                await ctx.send('Loop on')
        except Exception as e:
            print(e)
            await ctx.send("You are not connected to a vc!")

    @loop.error
    async def loop_error(self, ctx, error):
        channel = self.get_channel(ctx)
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f"You cannot write music commands in {ctx.channel.mention} channel. You have to use {channel.mention}.")

    @commands.command(name='setVolume', aliases=['set_volume'], description="Changing server volume.")
    @commands.has_permissions(manage_guild=True)
    @commands.check(is_correct_channel)
    async def setVolume(self, ctx, vol: int):
        try:
            player = self.bot.music.player_manager.get(ctx.guild.id)
            await player.set_volume(vol)
            await ctx.send(f"Set volume to: {vol}")
            main = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
            cur = main.cursor()
            cur.execute(f"SELECT vol FROM music WHERE guild_id = '{ctx.guild.id}'")
            result = cur.fetchone()
            if result is None:
                sql = ("INSERT INTO music(guild_id,vol) VALUES(%s,%s)")
                val = (str(ctx.guild.id), str(vol))
            else:
                sql = ("UPDATE music SET vol = %s WHERE guild_id = %s")
                val = (str(vol), str(ctx.guild.id))
            cur.execute(sql, val)
            main.commit()
            cur.close()
            main.close()

        except Exception as e:
            # TODO: Finish erros
            print(e)
            # await ctx.send("You are not connected to a vc!")

    @setVolume.error
    async def setVolume_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{ctx.author.mention}, wrong syntax use: {self.get_prefix(ctx.guild.id)}setVolume <amount>")
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"{ctx.author.mentin}, you don't have premissions to change the volume.")
        channel = self.get_channel(ctx)
        if isinstance(error, commands.CheckFailure):
            await ctx.send(f"You cannot write music commands in {ctx.channel.mention} channel. You have to use {channel.mention}.")

    @commands.command(name="music_channel", description="Setting a specific channel that the bot can read messages")
    async def music_channel(self, ctx, channel: commands.TextChannelConverter):
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        cur.execute(f"SELECT channel_id FROM music WHERE guild_id = '{ctx.guild.id}'")
        channel_id = cur.fetchone()
        if channel_id is None:
            sql = ("INSERT INTO music(guild_id,channel_id) VALUES(%s,%s)")
            val = (str(ctx.guild.id), str(channel.id))
        else:
            sql = ("UPDATE music SET channel_id = %s WHERE guild_id = %s")
            val = (str(channel.id), str(ctx.guild.id))
        cur.execute(sql, val)
        conn.commit()
        cur.close()
        conn.close()
        await ctx.send(f"Set music channel to {channel.mention}.")
        

def setup(bot):
    bot.add_cog(Music(bot))
    print('Load music')
