import discord
import config
import traceback
import asyncio
import youtube_dl
from discord.ext import commands
import audio

from core import checks

def get_voice_channels(server):
    'Returns the voice channels for the server sorted by position'
    channels = filter(lambda c: c.type == discord.ChannelType.voice, server.channels)
    channels = sorted(channels, key=lambda c: c.position)
    return channels

class MusicPlayerPlugin:
    def __init__(self, bot, tagdb):
        self.bot = bot
        self.loader = audio.Loader()
        self.players = {}
        self.tagdb = tagdb

    async def cannot_use_voice(self, ctx):
        author = ctx.message.author # requester
        if not author.voice_channel:
            await self.bot.say('you need to be in a voice channel')
            return True

        return False # we're clear

    def player_for(self, ctx):
        'Retrieves or creates a ServerMusicPlayer based on the given context'
        server = ctx.message.server
        try:
            return self.players[server.id]
        except KeyError:
            player = audio.ServerPlayer(
                self.bot,
                server,
                volume=config.default_volume,
                timeout=config.connection_timeout)
            self.players[server.id] = player
            return player

    @commands.check(checks.is_owner_or_admin)
    @commands.command(name='volume', pass_context=True,
        help="Adjusts bot volume for the server. Can only be used by server admins")
    async def volume_cmd(self, ctx, volume : int):
        player = self.player_for(ctx)
        player.volume = int(volume)
        await self.bot.say("Updated server's volume to " + str(player.volume) + "%")

    @commands.command(name='play', pass_context=True,
        help="Plays a song, can be a url or a tag name.\n" +
             "Can have loop as an optional argument.")
    async def play_cmd(self, ctx, url, *args):
        if await self.cannot_use_voice(ctx): return

        args = [a.lower() for a in args]
        loop = 'loop' in args

        try:
            url = self.tagdb.try_get(ctx.message.author.id, url, default=url)
            print("Playing {}".format(url))

            song = await self.loader.load_song(url, ctx.message.author, ctx.message.channel)
            player = self.player_for(ctx)
            await player.connect(ctx.message.author.voice_channel)
            await player.play(song, loop=loop)
        except youtube_dl.utils.DownloadError as ex:
            msg_text = 'Failed to download video: ' + str(ex)
            await self.bot.send_message(ctx.message.channel, msg_text) # there is an unknown bug with say() in catch

    @commands.command(name='playlist', pass_context=True,
        help="Adds a youtube playlist on a queue. Can be a url or a tag name.\n" +
             "Can have loop and shuffle as optional arguments.")
    async def playlist_cmd(self, ctx, url, *args):
        if await self.cannot_use_voice(ctx): return

        args = [a.lower() for a in args]
        loop = 'loop' in args
        shuffle = 'shuffle' in args

        try:
            url = self.tagdb.try_get(ctx.message.author.id, url, default=url)
            print("Playlist at {}".format(url))

            songs = await self.loader.load_playlist(url, ctx.message.author, ctx.message.channel)
            player = self.player_for(ctx)
            await player.connect(ctx.message.author.voice_channel)
            await player.play(*songs, loop=loop, shuffle=shuffle)
        except youtube_dl.utils.DownloadError as ex:
            msg_text = 'Failed to download video playlist: ' + str(ex)
            await self.bot.send_message(ctx.message.channel, msg_text) # there is an unknown bug with say() in catch

    @commands.command(name='shuffle', pass_context=True,
        help="Shuffles the current queue")
    async def shuffle_cmd(self, ctx):
        if await self.cannot_use_voice(ctx): return
        self.player_for(ctx).shuffle()

    @commands.command(name='skip', pass_context=True,
        help="Skips to the next song in the queue")
    async def skip_cmd(self, ctx):
        if await self.cannot_use_voice(ctx): return
        self.player_for(ctx).skip()

    @commands.command(name='stop', pass_context=True,
        help="Stops all songs in the queue and flushes it")
    async def stop_cmd(self, ctx):
        if await self.cannot_use_voice(ctx): return
        self.player_for(ctx).stop()
