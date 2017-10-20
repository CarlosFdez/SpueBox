import discord

class Song:
    def __init__(self, title : str, source, request_user, request_channel : discord.TextChannel):
        '''Represents a song data object'''
        self.title = title
        self.source = source
        self.request_user = request_user
        self.request_channel = request_channel