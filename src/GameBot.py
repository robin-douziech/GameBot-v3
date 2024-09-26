import discord, json, os
from discord.ext import commands, tasks

from utils import *

class GameBot(commands.Bot) :

    def __init__(self) -> None :
        super().__init__(command_prefix = '!', intents = discord.Intents.all())

        self.guild: discord.Guild = None
        self.admin_role: discord.Role = None

        self.vars = {
            'members': {},
            'channels': {},
            'roles': {},
            'events': {}
        }

        self.defaults = BOT_VARS_DEFAULTS

        self.files = {x: f"json/{x}.json" for x in self.vars}

        for var_name in self.vars :
            if not(os.path.exists(self.files[var_name])) :
                self.write_json(var_name)

    def admin_command(self, function: callable) :
        async def wrapper(ctx: commands.Context, *args, **kwargs) :
            author = self.guild.get_member(ctx.author.id)
            if author.get_role(self.admin_role.id) != None :
                await function(ctx, *args, **kwargs)
        return wrapper        

    def dm_command(self, function: callable) :
        async def wrapper(ctx: commands.Context, *args, **kwargs):
            author = self.guild.get_member(ctx.author.id)
            dm_channel = author.dm_channel if author.dm_channel is not None else await author.create_dm()
            if ctx.channel == dm_channel :
                await function(ctx, *args, **kwargs)
            else :
                message = await ctx.channel.fetch_message(ctx.message.id)
                await ctx.channel.delete_messages([message])
                await dm_channel.send("Pour éviter de polluer les salons du serveur, je ne réponds qu'aux commandes envoyées par message privé")
        return wrapper

    def write_json(self, var_name: str) :
        json_object = json.dumps(self.vars[var_name], indent=2)
        with open(self.files[var_name], "wt") as f:
            f.write(json_object)

    

    