
from discord.ext import commands

async def is_owner_or_admin(ctx : commands.Context):
    'Validates if the author is defined as the bot owner or is a server admin'
    if await ctx.bot.is_owner():
        return True

    permissions = ctx.channel.permissions_for(ctx.author)
    if permissions.administrator:
        return True

    raise commands.MissingPermissions(['administrator'])