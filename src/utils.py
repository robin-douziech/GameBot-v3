import discord

from variables import *

# set default config for DB-friendly JSON variables (default is the default format for an instance)
def db_default_config(variable: dict[any], default: dict[any]) :
    for key in variable :
        variable[key] = default_config(variable[key], default)
    return variable

# set default config for not DB-friendly JSON variables (default is the default for the whole variable)
def default_config(variable, default) :
    if isinstance(default, dict) :
        if isinstance(variable, dict) :
            for key in default:
                if not(key in variable) :
                    variable[key] = default[key]
                else :
                    variable[key] = default_config(variable[key], default[key])
        else :
            variable = default
    else :
        for type in [list, str, int, bool, float] :
            if isinstance(default, type) and not(isinstance(variable, type)) :
                variable = default
    return variable

def get_message_by_id(messages: list[discord.Message], id: int) :
    for message in messages :
        if message.id == id :
            return message
    return None