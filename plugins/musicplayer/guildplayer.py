import asyncio
import discord
import traceback
from .songrequestlist import SongRequestList
from .song import Song

import logging
from enum import Enum, auto

class SongRequest:
    """Represents a song request from a user from a channel
    
    This is used internally by the GuildPlayer to track the songs being played.
    """

    def __init__(self, song, request_user, request_channel, *, loop=False):
        self.song = song
        self.request_user = request_user
        self.request_channel = request_channel
        self.loop = loop

    @property
    def title(self):
        return self.song.title

    @property
    def url(self):
        return self.song.url

    @property
    def source(self):
        return self.song.source

class GuildPlayerMode(Enum):
    SINGLE = "Single"
    LINEAR = "Linear"

    def __str__(self):
        return self.value

class GuildPlayer:
    '''A class used to play audio for a guild and manage state.

    This class manages and wraps over discord's VoiceClient .
    '''

    def __init__(self, guild, *, volume = 100, inactivity_timeout=600):
        """Creates a new guild player
        """

        self.guild = guild # todo: use to validate connections?
        self.requests = SongRequestList()
        self.inactivity_timeout_length = inactivity_timeout

        self.voice_client = None

        self.connect_lock = asyncio.Lock()
        self.stop_signal = asyncio.Event()
        self.skip_signal = asyncio.Event()
        self.inactivity_timeout = None

        self.is_playing = False

        self.volume = volume

        self._mode = None
        self.mode = GuildPlayerMode.SINGLE

    @property
    def volume(self):
        '''Returns the guild's set volume level'''
        return self._volume

    @volume.setter
    def volume(self, value):
        '''Sets the guild's default volume level, and any currently playing music'''
        new_value = max(0, min(150, value))
        self._volume = value
        if self.voice_client:
            self.voice_client.source.volume = value / 100

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, newmode):
        self._mode = newmode
        # todo: handle the process of switching modes

    @property
    def is_connected(self):
        return self.voice_client and self.voice_client.is_connected()

    @property
    def channel(self):
        if self.voice_client:
            return self.voice_client.channel
        return None

    async def connect(self, voice_channel : discord.VoiceChannel):
        '''This is a coroutine. Connect to the voice channel,
        or move to it if already connected to another one.
        '''
        # If we are already connected to the voice channel, do nothing
        if self.is_connected and self.voice_client.channel is voice_channel:
            return

        # If we're moving or connecting, we have to stop
        self.stop()

        # If we are already connected to a channel here, move to the other channel
        if self.is_connected:
            await self.voice_client.move_to(voice_channel)
            return

        with await self.connect_lock:
            self.voice_client = await voice_channel.connect()         

    async def disconnect(self):
        self.stop()
        with await self.connect_lock:
            if self.voice_client:
                await self.voice_client.disconnect()
            self.voice_client = None

    def request_song(self, song : Song, request_user, request_channel, loop=False):
        """Requests a song. The mode decides what happens.
        
        SINGLE: Stops the song, clears the list
        LINEAR: Adds the song to the list

        No matter the mode, the guild player will begin playing if its currently
        not playing. The procedure is added to the asyncio event loop.
        """
        request = SongRequest(song, request_user, request_channel, loop=loop)
        
        if self._mode is GuildPlayerMode.SINGLE:
            self.requests.clear()
            self.requests.add(request)
            self.skip()
        else:
            self.requests.add(request)
        
        asyncio.ensure_future(self.start_playing())

    async def start_playing(self):
        if self.is_playing:
            return

        self.is_playing = True
        self.stop_signal.clear()
        self.skip_signal.clear()

        while self.is_connected and not self.stop_signal.is_set():
            song = self.requests.next()
            if not song: break

            try:
                print('playing {}'.format(song.title.encode('utf8')))

                # notify the request channel that the song is playing
                playing = discord.Embed()
                playing.title = f'Now playing {song.title}'
                playing.description = f"Requested by {song.request_user.name}"
                playing.url = song.url
                playing.set_footer(text=f"Mode: {str(self.mode)} | Volume: {self.volume}")
                await song.request_channel.send(embed=playing)

                if song.loop:
                    # If loop: keep playing until a stop OR skip signal is set
                    while not self.stop_signal.is_set() and not self.skip_signal.is_set():
                        await self._play_song(song)
                    self.skip_signal.clear()
                else:
                    await self._play_song(song)

            except:
                # We have to handle it here as we still need to keep playing songs
                # TODO: Implement an on_play_error handler
                traceback.print_exc()
                msg_text = "I couldn't play {}".format(song.title)
                await song.request_channel.send(msg_text)

        self.is_playing = False

        # Start the disconnect from voice channel timeout
        timeout_coro = self._wait_timeout(self.inactivity_timeout_length)
        self.inactivity_timeout = asyncio.ensure_future(timeout_coro)

    async def _play_song(self, song, after=None):
        '''This is a coroutine. Plays the contents of the song over audio.
        Will reset the timeout, and start a timeout after the song completes
        '''

        # If there is a player_timeout, cancel. If its already cancelled it has no effect
        if self.inactivity_timeout:
            self.inactivity_timeout.cancel()

        # Make sure the client doesn't disconnect in the middle of this by locking
        with await self.connect_lock:
            stop_event = asyncio.Event()
            loop = asyncio.get_event_loop()
            def after(error):
                if error:
                    logging.error(error)
                # todo: log
                def clear():
                    stop_event.set()
                loop.call_soon_threadsafe(clear)

            # NOTE: These are experimental flags, but they dont work on my linux server.
            # Going to keep them here to do more research on them later
            ##    before_options="-reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 2")

            source = discord.FFmpegPCMAudio(song.source)
            source = discord.PCMVolumeTransformer(source)
            source.volume = self.volume / 100

            self.voice_client.play(source, after=after)

            # wait until the player is done (triggered by 'after')
            await stop_event.wait()

    async def _wait_timeout(self, length):
        '''This is a coroutine. Starts the timeout for the player to disconnect.'''
        await asyncio.sleep(length)
        await self.disconnect()
        print('disconnected due to timeout')

    def skip(self):
        "Tells the player to stop playing the current song and play the next"
        self.skip_signal.set() # prevents looping
        if self.voice_client:
            self.voice_client.stop()

    def stop(self):
        "Tells the player to stop playing entirely. This does not clear the list"
        self.stop_signal.set()
        if self.voice_client:
            self.voice_client.stop()
