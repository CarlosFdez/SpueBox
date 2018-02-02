import asyncio
import youtube_dl
from youtube_dl.utils import DownloadError
import config

from .song import Song

class Loader:
    '''Retrieves song data via youtube dl'''

    async def load_song(self, lookup : str):
        results = await self._load_from_url(lookup, noplaylist=True)
        title, source = results[0]
        return Song(title, lookup, source)

    async def load_playlist(self, lookup : str):
        results = await self._load_from_url(lookup)
        return [Song(title, lookup, source) for (title, source) in results]

    async def _load_from_url(self, url: str, *, noplaylist=False):
        '''Retrieves one or more songs for a url. If its a playlist, returns multiple

        The results are (title, source) pairs
        '''

        ydl = youtube_dl.YoutubeDL({
            'format': 'bestaudio/best',
            'noplaylist': noplaylist,
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'logtostderr': False,
            'quiet': True
        })

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_songs, ydl, url)

    def _extract_songs(self, ydl: youtube_dl.YoutubeDL, url: str):
        info = ydl.extract_info(url, download=False)
        if not info:
            raise DownloadError('Data could not be retrieved')

        print(info)
            
        if '_type' in info and info['_type'] == 'playlist':
            entries = info['entries']
        else:
            entries = [info]

        results = [(e['title'], e['url']) for e in entries]
        return results
