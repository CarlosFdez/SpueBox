import sys
import traceback
import os
import asyncio

import config
import discord
import plugins

import core

from discord.ext import commands

import logging
from logging.handlers import TimedRotatingFileHandler

# Global handler for bot command errors
async def command_error(exc, ctx):
    exc_type = type(exc)
    if exc_type in [commands.BadArgument, commands.MissingRequiredArgument]:
        await ctx.bot.send_message(ctx.message.channel, "No wonder you're horrible at debates with arguments like that")
        return

    if ctx.message.server is None or ctx.prefix.startswith(ctx.bot.user.mention):
        if exc_type is commands.CommandNotFound:
            await ctx.bot.send_message(ctx.message.channel, str(exc))
            return

    # from the original command error function
    print('Ignoring exception in command {}'.format(ctx.command), file=sys.stderr)
    traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)

if __name__ == '__main__':
    # Set up logging (and ensure directory)
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        format='%(asctime)s %(levelname)s:%(name)s %(message)s',
        level=config.loglevel,
        handlers=[TimedRotatingFileHandler("logs/log.txt", when='midnight')])

    # Ensure database folder exists
    os.makedirs('database', exist_ok=True)

    prefixes = commands.when_mentioned_or('!')
    description = "Supe's glorious and handsome bot"

    tagdb = core.TagDatabase()

    bot = commands.Bot(command_prefix=prefixes, description=description)
    bot.on_command_error = command_error
    bot.add_cog(plugins.AdministrativePlugin(bot))
    bot.add_cog(plugins.MusicPlayerPlugin(bot, tagdb))
    bot.add_cog(plugins.TagPlugin(bot, tagdb))
    bot.add_cog(plugins.RandomGamePlugin(bot, config.games))

    logging.info("Bot plugins initialized")

    bot.run(config.credentials)

    logging.info("Bot shut down")
