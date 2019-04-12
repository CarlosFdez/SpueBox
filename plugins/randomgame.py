import discord
import random
import asyncio
from discord.ext import commands

class RandomGamePlugin(commands.Cog):
    'A simple plugin that will cycle based on a preset list of games'

    def __init__(self, bot, all_games):
        self.bot = bot
        self.all_games = all_games
        self._running = False

    @commands.Cog.listener()
    async def on_ready(self):
        # on_ready could be called multiple times, so we try to only go at it once
        if self._running:
            return

        self._running = True
        while not self.bot.is_closed():
            name = random.choice(self.all_games)
            await self.bot.change_presence(activity=discord.Game(name=name, type=1))
            await asyncio.sleep(60)

        # todo: handle what happens if we get here and its temporary.
        # No idea what would cause such a state, and in what order things would be called
