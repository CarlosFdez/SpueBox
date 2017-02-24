import discord
import random
import asyncio
from discord.ext import commands

class RandomGamePlugin:
    'A simple plugin that will cycle based on a preset list of games'

    def __init__(self, bot, all_games):
        self.bot = bot
        self.games = all_games

    async def on_ready(self):
        while self.bot.is_logged_in:
            name = random.choice(self.games)
            await self.bot.change_presence(game=discord.Game(name=name, type=1))
            await asyncio.sleep(60)
