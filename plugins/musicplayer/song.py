import discord

class Song:
    '''Represents a song data object
    
    Encapsulates the title, url, and raw source of a "song",
    which can be a video or a normal audio file
    '''

    def __init__(self, title : str, url, source):
        self.title = title
        self.url = url
        self.source = source