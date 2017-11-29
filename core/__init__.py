from .tagdatabase import TagDatabase, InvalidTagException

def ex_str(ex : Exception):
    "Returns a string that properly represents an exception"
    message : str = getattr(ex, 'message', str(ex))
    if message and message.strip():
        return message
    return repr(ex) # final resort if there's no actual message
