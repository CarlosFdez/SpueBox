import discord
import config
import traceback
import asyncio
import youtube_dl
from discord.ext import commands

from .guildplayer import GuildPlayer, GuildPlayerMode
from .loader import Loader
from .song import Song

from core import checks, ex_str

import logging
import functools

def voice_only(fn):
    """A decorator that modifies a cog function command to require a sender to be in a voice channel.
    On failure, it'll notify the author with an error message.
    Note: discord.py checks would cause it to not show on the help function. So we do this instead.
    """
    @functools.wraps(fn)
    async def modified_fn(self, ctx, *args, **kwargs):
        author = ctx.author # requester
        if not author.voice:
            await ctx.send('you need to be in a voice channel')
            return

        await fn(self, ctx, *args, **kwargs)
    return modified_fn


class MusicPlayerPlugin(commands.Cog):
    def __init__(self, bot, tagdb):
        self.bot = bot
        self.loader = Loader()
        self.players = {}
        self.tagdb = tagdb

    # Disconnect the bot if there's no one to listen
    async def on_voice_state_update(self, member, before, after):
        "Triggered when a user leaves or joins a voice channel"

        # if there was no channel change, this is not a leave update
        if before.channel is after.channel:
            return

        player = self.player_for(member.guild)

        # If the channel is uninvolved or disconnected, we skip
        if not player.is_connected or before.channel != player.channel:
            return

        # Disconnect if the player's channel is empty of regular users
        all_members = player.channel.members
        regular_members = filter(lambda v: not v.bot, all_members)
        if not next(regular_members, None):
            await player.disconnect()

    def player_for(self, guild):
        'Retrieves or creates a GuildPlayer based on the given context'
        try:
            return self.players[guild.id]
        except KeyError:
            player = GuildPlayer(
                guild,
                volume=config.default_volume,
                inactivity_timeout=config.connection_timeout)
            self.players[guild.id] = player
            return player

    @commands.check(checks.is_owner_or_admin)
    async def volume_cmd(self, ctx, volume : int):
        "Adjusts bot volume for the guild. Can only be used by guild admins"
        player = self.player_for(ctx.guild)
        player.volume = int(volume)
        await ctx.send("Updated guild's volume to " + str(player.volume) + "%")

    @commands.command(name='play', aliases=['p'])
    @voice_only
    async def play_cmd(self, ctx, url : str=None, *args):
        """Plays audio. Use "help play" for more info.
        
        If a url is given, requests audio from a url or tag name to be played.
        Otherwise, it will resume the current playlist if there is any.

        Depending on the play mode, this will either replace the current track,
        or add it to a list.

        Add "loop" to loop the requested audio. Use "next" or "stop" to cancel it.
        """

        args = [a.lower() for a in args]
        loop = 'loop' in args

        try:
            
            player = self.player_for(ctx.guild)

            if url:
                # Try to load a tag, if it fails it passes through
                url = self.tagdb.try_get(ctx.author.id, url, default=url)
                logging.info("Playing {}".format(url))

                song = await self.loader.load_song(url)
                player.request_song(song, ctx.author, ctx.channel, loop=loop)                
            elif not len(player):
                await ctx.send("There is nothing to play.")
                return

            await player.connect(ctx.author.voice.channel)
            player.play()

        except youtube_dl.utils.DownloadError as ex:
            message = 'Failed to download video: ' + ex_str(ex)
            logging.error(message)

            await ctx.send(message)

        except Exception as ex:
            logging.error('Error while trying to connect or play audio')
            logging.exception(ex)

            await ctx.send("Error while trying to connect or play audio")

    @commands.command(name='playlist')
    @voice_only
    async def playlist_cmd(self, ctx, url, *args):
        "Adds a youtube playlist to a queue from a url or a tag name. Loop and shuffle as optional arguments."
        args = [a.lower() for a in args]
        shuffle = 'shuffle' in args

        try:
            # Try to load a tag, if it fails it passes through
            url = self.tagdb.try_get(ctx.author.id, url, default=url)
            logging.info("Playlist at {}".format(url))

            songs = await self.loader.load_playlist(url)
            player = self.player_for(ctx.guild)
            
            await player.connect(ctx.author.voice.channel)
            player.mode = GuildPlayerMode.LINEAR

            for song in songs:
                player.request_song(song, ctx.author, ctx.channel)
            player.play()

        except youtube_dl.utils.DownloadError as ex:            
            message = 'Failed to download video: ' + ex_str(ex)
            logging.error(message)

            await ctx.send(message)

        except Exception as ex:
            logging.error('Error while trying to connect or play audio')
            logging.exception(ex)

            await ctx.send("Error while trying to connect or play audio")

    @commands.command(name='shuffle')
    @voice_only
    async def shuffle_cmd(self, ctx):
        "Shuffles the current queue"
        self.player_for(ctx.guild).shuffle()

    @commands.command(name='next', aliases=['skip'])
    @voice_only
    async def next_cmd(self, ctx):
        "Skips to the next song in the queue"
        self.player_for(ctx.guild).skip()

    @commands.command(name='stop')
    @voice_only
    async def stop_cmd(self, ctx):
        "Stops all songs in the queue and flushes it"
        self.player_for(ctx.guild).stop()

    @commands.command(name='list')
    async def list_cmd(self, ctx):
        "Lists all loaded tracks"
        player = self.player_for(ctx.guild)
        count = len(player)
        if not count:
            await ctx.send('The playlist is empty')
            return

        message = f'{count} items are in the list.\n'
        if count > 20:
            message += 'These are the first 10.\n'

        titles = [req.title for req in player]
        titles = titles[0:10]
        message += '```{}```'.format('\n'.join(titles))

        await ctx.send(message)
