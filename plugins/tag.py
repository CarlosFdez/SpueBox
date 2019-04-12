import shelve
import traceback
from discord.ext import commands
from core import InvalidTagException

class TagPlugin(commands.Cog):
    def __init__(self, bot, tagdb):
        self.bot = bot
        self.tagdb = tagdb

    @commands.command(name='addtag',
        help="Adds a tag as a user tag, which can only be used by you")
    async def addtag_cmd(self, ctx, name, *, content):
        try:
            self.tagdb.set(ctx.message.author.id, name, content.strip())
            await ctx.send('tag added')
        except InvalidTagException:
            await ctx.send('Invalid tag name')
        except Exception:
            traceback.print_exc()
            await ctx.send('Unknown error')

    @commands.command(name='tag',
        help="Display a user tag")
    async def tag_cmd(self, ctx, name):
        try:
            value = self.tagdb.get(ctx.message.author.id, name)
            await ctx.send(value)
        except KeyError:
            await ctx.send('Tag {} does not exist'.format(name))
        except InvalidTagException:
            await ctx.send('Invalid tag name')
        except Exception:
            traceback.print_exc()
            await ctx.send('Unknown error')

    @commands.command(name='taglist',
        help="Displays all your user tags")
    async def taglist_cmd(self, ctx):
        try:
            keys = self.tagdb.keys_for(ctx.message.author.id)
            if keys:
                await ctx.send('Your tag names are: {}'.format(', '.join(keys)))
            else:
                await ctx.send("You don't have any tags")
        except:
            traceback.print_exc()
            await ctx.send('Unknown error')
