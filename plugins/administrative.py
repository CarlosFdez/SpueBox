import config
import traceback
import aiohttp
import discord.utils
from core import checks
from discord.ext import commands

class AdministrativePlugin:
    def __init__(self, bot):
        self.bot = bot

    async def check_not_direct(self, ctx):
        if self.bot.user.mention not in ctx.prefix:
            await self.bot.say('This command only works if I am directly mentioned')
            return True
        return False

    @commands.check(checks.is_owner)
    @commands.command(name='link')
    async def link_cmd(self):
        link = discord.utils.oauth_url(config.client_id)
        await self.bot.say(link)

    @commands.check(checks.is_owner)
    @commands.command(name='say')
    async def say_cmd(self, *, content: str):
        if await self.check_not_direct(ctx): return

        await self.bot.say(content.strip())

    @commands.check(checks.is_owner)
    @commands.command(name='avatar', pass_context=True)
    async def avatar_cmd(self, ctx):
        await self.bot.say('please reply with the attachment or link')
        reply = await self.bot.wait_for_message(author=ctx.message.author)
        if not reply:
            await self.bot.say('no reply')
            return

        if reply.attachments:
            url = reply.attachments[0]['url']
        else:
            url = reply.content

        res = await aiohttp.get(url)
        if res.status != 200:
            await self.bot.say('failed to load image')
            return

        image_data = await res.read()
        await self.bot.edit_profile(avatar=image_data)
        print('avatar set')
