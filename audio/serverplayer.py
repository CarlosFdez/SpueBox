import asyncio
import discord
import array
import traceback
from .songlist import SongList

class AdjustableStream:
    def __init__(self, base, client):
        self.base = base
        self.client = client

    async def wait_for_data(self, buffersize):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.base.peek, buffersize)

    def read(self, n=None):
        stream = self.base.read(n)
        if self.client.volume >= 100:
            return stream

        return self._transform_volume(stream)

    def _transform_volume(self, stream):
        stream = array.array('h', stream)
        volume_scaling = self.client.volume / 100

        setitem = stream.__setitem__
        for i, value in enumerate(stream):
            stream.__setitem__(i, int(value * volume_scaling))

        return stream.tobytes()

class ServerPlayer:
    '''An enhancement over discord's VoiceClient that provides additional functionality

    This class will eventually be changed to allow mixing audio data
    '''

    def __init__(self, bot, server, *, volume = 100, timeout=600):
        self.bot = bot
        self.server = server
        self.volume = volume
        self.timeout = timeout
        self.songs = SongList()

        self.player = None # todo: rename
        self.channel = None
        self.play_lock = asyncio.Lock()

        self.connect_lock = asyncio.Lock()
        self.player_timeout = None

    @property
    def is_playing(self):
        return self.play_lock.locked()

    @property
    def is_connected(self):
        return self.bot.is_voice_connected(self.server)

    @property
    def is_channel_empty(self):
        'Returns if the channel is empty not including the player'
        if not self.channel:
            return False

        non_bot_members = filter(lambda v: not v.bot, self.channel.voice_members)
        return non_bot_members.next() is not None

    async def connect(self, voice_channel):
        '''This is a coroutine. Connect to the voice channel,
        disconnecting the current connection if there is one if not already connected to it.
        '''
        if self.is_connected and self.voice.channel is voice_channel:
            return

        if self.is_connected:
            await self.disconnect()

        # do the connection lock here as doing it above could lead to deadlock
        with await self.connect_lock:
            try:
                self.voice = await self.bot.join_voice_channel(voice_channel)
                self.channel = voice_channel
                print("debug: connected")
            except:
                print('failed to connect to voice (should probably do something else here)')

    async def disconnect(self):
        with await self.connect_lock:
            self.stop()
            await self.voice.disconnect()
            self.channel = None

    async def play(self, *songs, loop=False, shuffle=False):
        '''This is a coroutine. Tells the audio client to play items that arrive in the playlist'''
        self.stop()

        with await self.play_lock:
            self.songs.reset(songs, loop=loop, shuffle=shuffle)
            while self.is_connected:
                song = self.songs.next()
                if not song: break

                try:
                    print('playing {}'.format(song.title.encode('utf8')))
                    await self._play_song(song)
                except:
                    # todo: move to caller
                    traceback.print_exc()
                    msg_text = "I couldn't play {}".format(song.title)
                    await self.bot.send_message(song.request_channel, msg_text)

    async def _play_song(self, song, after=None):
        '''This is a coroutine. Plays the contents of the song over audio.
        Will reset the timeout, and start a timeout after the song completes
        '''

        # If there is a player_timeout, cancel. If its already cancelled it has no effect
        if self.player_timeout:
            self.player_timeout.cancel()

        # Make sure the client doesn't disconnect in the middle of this by locking
        with await self.connect_lock:
            stop_event = asyncio.Event()
            loop = asyncio.get_event_loop()
            def after():
                def clear():
                    stop_event.set()
                    self.player = None
                loop.call_soon_threadsafe(clear)

            self.player = self.voice.create_ffmpeg_player(
                song.source,
                before_options="-nostdin",
                options="-vn -b:a 128k",
                after=after)
            self.player.buff = AdjustableStream(self.player.buff, self)

            # wait for there to be data to play
            await self.player.buff.wait_for_data(self.player.frame_size)

            self.player.start()

            # wait until the player is done (triggered by 'after')
            await stop_event.wait()

        # Start the disconnect from voice channel timeout
        self.player_timeout = asyncio.ensure_future(self._wait_timeout())

    async def _wait_timeout(self):
        '''This is a coroutine. Starts the timeout for the player to disconnect.'''
        await asyncio.sleep(self.timeout)
        await self.disconnect()
        print('disconnected due to timeout')

    def skip(self):
        if self.player:
            self.player.stop()

    def stop(self):
        self.songs.clear()
        self.skip()
