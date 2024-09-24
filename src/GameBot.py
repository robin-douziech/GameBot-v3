import discord, json, os
from discord.ext import commands, tasks

from variables import *

class GameBot(commands.Bot) :

    def __init__(self) -> None :
        super().__init__(command_prefix = '!', intents = discord.Intents.all())

        self.guild: discord.Guild = None
        self.admin_role: discord.Role = None

        self.members = {}
        self.members_filename = "json/members.json"

        self.channels = {}
        self.channels_filename = "json/channels.json"

        self.roles = {}
        self.roles_filename = "json/roles.json"

        self.events = {}
        self.events_filename = "json/events.json"

        self.dict_vars = {
            "members": [self.members, "json/members.json"],
            "channels": [self.channels, "json/channels.json"],
            "roles": [self.roles, "json/roles.json"],
            "events": [self.events, "json/events.json"],
        }

        for filename in [self.dict_vars[x][1] for x in self.dict_vars] :
            if not(os.path.exists(filename)) :
                with open(filename, 'x') as f :
                    pass # on crée juste le fichier

        for var_name in self.dict_vars :
            self.write_json(var_name)


    def write_json(self, var_name: str) :
        json_object = json.dumps(self.dict_vars[var_name][0], indent=2)
        with open(self.dict_vars[var_name][1], "wt") as f:
            f.write(json_object)


    