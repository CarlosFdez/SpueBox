import asyncio
import array

def transform_stream(stream, volume):
    if volume >= 100:
        return stream

    stream = array.array('h', stream)
    volume_scaling = volume / 100

    setitem = stream.__setitem__
    for i, value in enumerate(stream):
        stream.__setitem__(i, int(value * volume_scaling))

    return stream.tobytes()

class AudioStream:
    'An audio stream that wraps around a raw PCM stream. The volume can be adjusted.'

    def __init__(self, raw_stream, volume=100):
        self.base = raw_stream
        self.volume = volume

    async def wait_for_data(self, buffersize):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.base.peek, buffersize)

    def read(self, n=None):
        stream = self.base.read(n)
        return transform_stream(stream, self.volume)
