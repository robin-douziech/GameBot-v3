import discord, json, os, calendar, logging, sys
from discord.ext import commands, tasks
import datetime as dt

from utils import *

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class GameBot(commands.Bot) :

    def __init__(self) -> None :
        super().__init__(command_prefix = '!', intents = discord.Intents.all())

        self.guild: discord.Guild = None
        self.admin_role: discord.Role = None
        self.channels: dict[int: discord.abc.GuildChannel] = None
        self.config = {}

        self.vars = {
            'members': {},
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
    
    def divide_message(self, message: str, wrappers: tuple[str] = ('', '')) :
        lines = message.split("\n")
        for i in range(len(lines)-2) :
            if lines[i] == "" :
                lines[i] = "\u200B"
        msg_list = []
        while len(lines) > 0 :
            current_msg = ""
            while len(lines) > 0 and len(current_msg+lines[0]+wrappers[0]+wrappers[1]) < DISCORD_MAX_MESSAGE_LENGTH :
                current_msg += f"{lines.pop(0)}\n"
            msg_list.append(f"{wrappers[0]}{current_msg}{wrappers[1]}")
        return msg_list

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
    
    def get_current_datetime(self) :
        now = dt.datetime.now().strftime('%d/%m/%y %H:%M')
        (date, time) = now.split()
        (day, month, year) = date.split('/')
        (hours, minutes) = time.split(':')
        if (int(hours) + int(self.config['hours_offset'])) > 23 :
            hours = f"{'0' if (int(hours) + int(self.config['hours_offset'])) % 24 < 10 else ''}{(int(hours) + int(self.config['hours_offset'])) % 24}"
            day = f"{'0' if int(day)+1 < 10 else ''}{int(day)+1}"
            if int(day) > int(calendar.monthrange(int(year), int(month))[1]) :
                day = "01"
                month = f"{'0' if int(month)+1 < 10 else ''}{int(month)+1}"
                if int(month) > 12 :
                    month = "01"
                    year = f"{int(year)+1}"
        return (day, month, year, hours, minutes)
    
    def log(self, message: str, level: str = "info") :
        match level :
            case "debug" :
                logging.debug(message)
            case "info" :
                logging.info(message)
            case "warning" :
                logging.warning(message)
            case "error" :
                logging.error(message)
            case "critical" :
                logging.critical(message)
            case _ :
                raise Exception("Unknown logging level")
            
    async def send(self, channel: discord.TextChannel, message: str, wrappers: tuple[str] = ('', '')) :
        messages = self.divide_message(message, wrappers=wrappers)
        for msg in messages :
            await channel.send(msg)

    def write_json(self, var_name: str) :
        json_object = json.dumps(self.vars[var_name], indent=2)
        with open(self.files[var_name], "wt") as f:
            f.write(json_object)

    

    