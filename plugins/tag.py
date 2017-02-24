import shelve
import traceback
from discord.ext import commands
from core import InvalidTagException

class TagPlugin:
    def __init__(self, bot, tagdb):
        self.bot = bot
        self.tagdb = tagdb

    @commands.command(name='addtag', pass_context=True,
        help="Adds a tag as a user tag, which can only be used by you")
    async def addtag_cmd(self, ctx, name, *, content):
        try:
            self.tagdb.set(ctx.message.author.id, name, content.strip())
            await self.bot.say('tag added')
        except InvalidTagException:
            await self.bot.say('Invalid tag name')
        except Exception:
            traceback.print_exc()
            await self.bot.say('Unknown error')

    @commands.command(name='tag', pass_context=True,
        help="Display a user tag")
    async def tag_cmd(self, ctx, name):
        try:
            value = self.tagdb.get(ctx.message.author.id, name)
            await self.bot.say(value)
        except KeyError:
            await self.bot.say('Tag {} does not exist'.format(name))
        except InvalidTagException:
            await self.bot.say('Invalid tag name')
        except Exception:
            traceback.print_exc()
            await self.bot.say('Unknown error')

    @commands.command(name='taglist', pass_context=True,
        help="Displays all your user tags")
    async def taglist_cmd(self, ctx):
        try:
            keys = self.tagdb.keys_for(ctx.message.author.id)
            if keys:
                await self.bot.reply('Your tag names are: {}'.format(', '.join(keys)))
            else:
                await self.bot.reply("You don't have any tags")
        except:
            traceback.print_exc()
            await self.bot.say('Unknown error')
