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

def setup_logging():
    "Set up logging (and ensure directory)"

    # Set up log directory first
    os.makedirs('logs', exist_ok=True)
    
    normal_formatter = logging.Formatter('%(name)s %(message)s')
    full_formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s %(message)s')

    file_handler = logging.handlers.TimedRotatingFileHandler("logs/log.txt", when='midnight')
    file_handler.setLevel(config.loglevel)
    file_handler.setFormatter(full_formatter)

    # Also print info level logs to stdout
    standard_handler = logging.StreamHandler(sys.stdout)
    standard_handler.setFormatter(normal_formatter)
    standard_handler.setLevel(logging.INFO)

    # Also print error level logs to stder
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setFormatter(normal_formatter)
    error_handler.setLevel(logging.WARNING)

    logging.basicConfig(
        level=config.loglevel,
        handlers=[
            file_handler,
            standard_handler,
            error_handler
    ])

# Global handler for bot command errors
async def command_error(ctx, exc):
    exc_type = type(exc)
    if exc_type in [commands.BadArgument, commands.MissingRequiredArgument]:
        await ctx.send("No wonder you're horrible at debates with arguments like that")
        return

    if ctx.message.guild is None or ctx.prefix.startswith(ctx.bot.user.mention):
        if exc_type is commands.CommandNotFound:
            await ctx.send(str(exc))
            return

    # from the original command error function
    print('Ignoring exception in command {}'.format(ctx.command), file=sys.stderr)
    traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)

if __name__ == '__main__':
    setup_logging()

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
