import core
import config

def is_owner(ctx):
    'Validates if the author is the bot owner as defined in the config'
    return ctx.message.author.id == config.owner_id

def is_admin(ctx):
    'Validates if the author is a server admin'
    permissions = ctx.message.author.server_permissions
    return permissions.administrator

def is_owner_or_admin(ctx):
    'Validates if the author is defined as the bot owner or is a server admin'
    return is_owner(ctx) or is_admin(ctx)
