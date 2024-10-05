import discord

from variables import *

def datetime_cmp(datetime1: str, datetime2: str) :

    datetime1 = {
        "year":   datetime1.split()[0].split('/')[2],
        "month":  datetime1.split()[0].split('/')[1],
        "day":    datetime1.split()[0].split('/')[0],
        "hour":   datetime1.split()[1].split(':')[0],
        "minute": datetime1.split()[1].split(':')[1]
    }

    datetime2 = {
        "year":   datetime2.split()[0].split('/')[2],
        "month":  datetime2.split()[0].split('/')[1],
        "day":    datetime2.split()[0].split('/')[0],
        "hour":   datetime2.split()[1].split(':')[0],
        "minute": datetime2.split()[1].split(':')[1]
    }

    units = ["year", "month", "day", "hour", "minute"]
    for unit in units :
        if int(datetime1[unit]) < int(datetime2[unit]) :
            return -1
        elif int(datetime1[unit]) > int(datetime2[unit]) :
            return 1
    return 0

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