import discord
import config
import traceback
import asyncio
import youtube_dl
from discord.ext import commands
import audio

from core import checks

class MusicPlayerPlugin:
    def __init__(self, bot, tagdb):
        self.bot = bot
        self.loader = audio.Loader()
        self.players = {}
        self.tagdb = tagdb

    # This isn't a check as checks pretend the command doesn't exist.
    async def cannot_use_voice(self, ctx):
        "Checks if the context allows the use of voice"
        author = ctx.author # requester
        if not author.voice:
            await ctx.send('you need to be in a voice channel')
            return True

        return False # we're clear

    def player_for(self, ctx):
        'Retrieves or creates a GuildMusicPlayer based on the given context'
        guild = ctx.guild
        try:
            return self.players[guild.id]
        except KeyError:
            player = audio.GuildPlayer(
                guild,
                volume=config.default_volume,
                disconnect_timeout=config.connection_timeout)
            self.players[guild.id] = player
            return player

    @commands.check(checks.is_owner_or_admin)
    async def volume_cmd(self, ctx, volume : int):
        "Adjusts bot volume for the guild. Can only be used by guild admins"
        player = self.player_for(ctx)
        player.volume = int(volume)
        await ctx.send("Updated guild's volume to " + str(player.volume) + "%")

    @commands.command(name='play')
    async def play_cmd(self, ctx, url, *args):
        "Plays audio from a url or tag name. Can have loop as an optional argument."
        if await self.cannot_use_voice(ctx): return

        args = [a.lower() for a in args]
        loop = 'loop' in args

        try:
            # Try to load a tag, if it fails url doesn't change
            url = self.tagdb.try_get(ctx.author.id, url, default=url)
            print("Playing {}".format(url))

            song = await self.loader.load_song(url, ctx.author, ctx.channel)
            player = self.player_for(ctx)
            await player.connect(ctx.author.voice.channel)
            await player.play(song, loop=loop)
        except youtube_dl.utils.DownloadError as ex:
            # TODO: LOG
            await ctx.send('Failed to download video: ' + str(ex))

    @commands.command(name='playlist')
    async def playlist_cmd(self, ctx, url, *args):
        "Adds a youtube playlist to a queue from a url or a tag name. Loop and shuffle as optional arguments."
        if await self.cannot_use_voice(ctx): return

        args = [a.lower() for a in args]
        loop = 'loop' in args
        shuffle = 'shuffle' in args

        try:
            # Try to load a tag, if it fails url doesn't change
            url = self.tagdb.try_get(ctx.author.id, url, default=url)
            print("Playlist at {}".format(url))
            # TODO: LOG

            songs = await self.loader.load_playlist(url, ctx.author, ctx.channel)
            player = self.player_for(ctx)
            await player.connect(ctx.author.voice.channel)
            await player.play(*songs, loop=loop, shuffle=shuffle)
        except youtube_dl.utils.DownloadError as ex:
            # TODO: LOG
            ctx.send('Failed to download video playlist: ' + str(ex))

    @commands.command(name='shuffle')
    async def shuffle_cmd(self, ctx):
        "Shuffles the current queue"
        if await self.cannot_use_voice(ctx): return
        self.player_for(ctx).shuffle()

    @commands.command(name='skip')
    async def skip_cmd(self, ctx):
        "Skips to the next song in the queue"
        if await self.cannot_use_voice(ctx): return
        self.player_for(ctx).skip()

    @commands.command(name='stop')
    async def stop_cmd(self, ctx):
        "Stops all songs in the queue and flushes it"
        if await self.cannot_use_voice(ctx): return
        self.player_for(ctx).stop()
