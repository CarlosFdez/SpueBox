import asyncio
import discord
import traceback
from .songlist import SongList

class GuildPlayer:
    '''A class used to play audio for a guild and manage state.

    This class wraps over discord's VoiceClient, 
    but does not require a connection to exist.
    '''

    def __init__(self, guild, *, volume = 100, inactivity_timeout=600):
        self.guild = guild # todo: use to validate connections?
        self.songs = SongList()
        self.inactivity_timeout_length = inactivity_timeout

        self.voice_client = None

        self.play_lock = asyncio.Lock()
        self.connect_lock = asyncio.Lock()
        self.inactivity_timeout = None

        self.volume = volume

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
    def is_connected(self):
        return self.voice_client and self.voice_client.is_connected()

    @property
    def channel(self):
        if self.voice_client:
            return self.voice_client.channel

    async def connect(self, voice_channel : discord.VoiceChannel):
        '''This is a coroutine. Connect to the voice channel,
        or move to it if already connected to another one.
        '''
        self.stop()

        # If we are already connected to the voice channel, skip
        if self.is_connected and self.voice_client.channel is voice_channel:
            return

        # If we are already connected to a channel here, move to the other channel
        if self.is_connected:
            await self.voice_client.move_to(voice_channel)
            print("debug: moved channels")
            return

        # note: we lock here as doing it above could lead to deadlock (disconnect uses the lock)
        with await self.connect_lock:
            try:
                self.voice_client = await voice_channel.connect()
                print("debug: connected")
            except Exception as ex:
                print('failed to connect to voice: ' + str(ex))

    async def disconnect(self):
        self.stop()
        with await self.connect_lock:
            if self.voice_client:
                await self.voice_client.disconnect()
            self.voice_client = None

    async def play(self, *songs, loop=False, shuffle=False):
        '''This is a coroutine. Tells the audio client to play items that arrive in the playlist'''
        self.stop()

        # Don't start manipulating songs while the previous one is still playing
        with await self.play_lock:
            self.songs.reset(songs, loop=loop, shuffle=shuffle)
            while self.is_connected:
                song = self.songs.next()
                if not song: break

                try:
                    print('playing {}'.format(song.title.encode('utf8')))
                    await self._play_song(song)
                except:
                    # We have to handle it here as we still need to keep playing songs
                    traceback.print_exc()
                    msg_text = "I couldn't play {}".format(song.title)
                    await song.request_channel.send(msg_text)

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
                    print(error)
                # todo: log
                def clear():
                    stop_event.set()
                loop.call_soon_threadsafe(clear)

            source = discord.FFmpegPCMAudio(song.source)
            source = discord.PCMVolumeTransformer(source)
            source.volume = self.volume / 100

            self.voice_client.play(source, after=after)

            # wait until the player is done (triggered by 'after')
            await stop_event.wait()

        # Start the disconnect from voice channel timeout
        timeout_coro = self._wait_timeout(self.inactivity_timeout_length)
        self.inactivity_timeout = asyncio.ensure_future(timeout_coro)

    async def _wait_timeout(self, length):
        '''This is a coroutine. Starts the timeout for the player to disconnect.'''
        await asyncio.sleep(length)
        await self.disconnect()
        print('disconnected due to timeout')

    def skip(self):
        if self.voice_client:
            self.voice_client.stop()

    def stop(self):
        self.songs.clear()
        self.skip()
