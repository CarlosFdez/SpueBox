import random
from discord.ext import commands

class ChoicePlugin:
    def __init__(self, bot):
        self.bot = bot

    @commands.command('roll')
    async def roll_cmd(self, message):
        await self._roll_base(message, 6)

    @commands.command('d20')
    async def d20_cmd(self, message):
        await self._roll_base(message, 20)

    async def _roll_base(self, message, max_int):
        result = random.randint(1, max_int)
        msg = '{} rolled {}'.format(message.author.mention, result)
        await self.bot.send_message(message.channel, msg)
