import json, calendar, logging, sys, re, shutil
from dateutil.relativedelta import relativedelta
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
        self.owner: discord.Member = None
        self.roles: dict[str, discord.Role] = {}
        self.channels: dict[str, discord.TextChannel] = {}

        self.messages: dict[str, discord.Message] = {}
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
        for string in ["config", "messages"] :
            if not(os.path.exists(f"json/{string}.json")) :
                with open(f"json/{string}.json", "x") as f :
                    f.write("{}")

    def add_members(self, pseudos: list[str]) :
        for pseudo in pseudos :
            self.vars["members"][pseudo] = BOT_VARS_DEFAULTS["members"]
            self.write_json("members")

    def admin_command(self, function: callable) :
        """ Decorator to apply to a command so that only members with admin role can use it """
        async def wrapper(ctx: commands.Context, *args, **kwargs) :
            author = self.guild.get_member(ctx.author.id)
            if author.get_role(self.roles["admin"].id) != None :
                await function(ctx, *args, **kwargs)
        return wrapper
    
    def answer_is_valid(self, author: discord.Member, answer: str) :
        question = self.vars["members"][f"{author.name}#{author.discriminator}"]["questions"][0]
        valid = CREATION_QUESTIONS[self.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"]][question]["valid"]
        return re.match(valid, answer)
    
    def divide_message(self, message_content: str, wrappers: tuple[str] = ('', '')) :
        """ This function split a message content so that its length doesn't exceed DISCORD_MAX_MESSAGE_LENGTH """
        lines = message_content.split("\n")
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
        """ Decorator to apply to a command so it can only be sent by direct message """
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
    
    async def get_all_messages_in_channel(self, channel: discord.TextChannel|str):
        """ This function returns a list containing all the messages of a channel """
        if isinstance(channel, str) :
            channel = self.channels[channel]
        messages: list[discord.Message] = []
        counter = 0
        while counter == len(messages) :
            counter += 100
            messages = [message async for message in channel.history(limit=counter)]
        return messages
    
    def get_discord_member(self, pseudo: str) :
        for member in self.guild.members :
            if pseudo == f"{member.name}#{member.discriminator}" :
                return member
        return None
    
    async def get_messages_by_ids_in_channel(self, message_ids: list[int], channel: discord.TextChannel|str) :
        """ This function returns a list of discord.Message found in the given channel.
        The message it looks for are the ones having the given ids (present in message_ids).
        If at least one message is not found, the function return None.

        Args:
            message_ids (list[int]): Ids of the messages we are looking for
            channel (discord.TextChannel|str): The channel where to look for messages

        Returns:
            list[discord.Message]|None: The messages found

        """
        channel_messages = await self.get_all_messages_in_channel(channel)
        messages: list[discord.Message] = []
        for id in message_ids :
            message = get_message_by_id(channel_messages, id)
            if message is not None :
                messages.append(message)
            else :
                return None
        return messages
    
    def get_current_datetime(self) :
        """ This function returns the current datetime (taking into account the hour_offset
        between Europe/Paris and the datetime of the server where the bot is executed) """
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
        """ This function logs message into the bot logs file """
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
            
    async def process_msg(self, message: discord.Message) :
        author = self.guild.get_member(message.author.id)

        if not(author.bot) :

            if self.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"] :

                match (self.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"]) :
                    case "birthday" :
                        if self.answer_is_valid(author, message.content) :

                            birthday = ""
                            m = re.match(CREATION_QUESTIONS["birthday"]["date"]["valid"], message.content)
                            if message.content == "0" :
                                birthday = message.content
                                response = "Très bien, je n'annoncerai pas ton anniversaire dans le salon #anniversaires"
                            elif m.group('year') is None and m.group('time') is None :
                                birthday = f"{message.content} 00:00"
                                response = f"J'annoncerai ton anniversaire dans le salon #anniversaires le {m.group('date')} à minuit"
                            elif m.group('year') is None :
                                birthday = message.content
                                response = f"J'annoncerai ton anniversaire dans le salon #anniversaires le {m.group('date')} à{m.group('time')}"
                            elif m.group('time') is None :
                                birthday = f"{message.content} 00:00"
                                response = f"J'annoncerai ton anniversaire dans le salon #anniversaires le {m.group('date')} à minuit en précisant ton âge"
                            else :
                                birthday = message.content
                                response = f"J'annoncerai ton anniversaire dans le salon #anniversaires le {m.group('date')} à{m.group('time')} en précisant ton âge"
                            self.vars["members"][f"{author.name}#{author.discriminator}"]["birthday"] = birthday
                            self.write_json("members")

                            await self.send(author.dm_channel, response)
                            await self.send_next_question(author)

                            if len(self.vars["members"][f"{author.name}#{author.discriminator}"]["questions"]) == 0 :
                                self.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"] = ""
                                self.write_json("members")

                        else :
                            await self.send(author.dm_channel, "Ta réponse ne respecte pas le format attendu")

                    case _ :
                        pass


    def remove_members(self, pseudos: list[str]) :
        try :
            for pseudo in pseudos :
                self.vars["members"].pop(pseudo)
                self.write_json("members")
        except Exception as e :
            self.log(f"{e} (while trying to delete a member)", "error")

    def save_message(self, title: str, ids: list[int]) :
        """ This function saves an official bot message into json/messages.json (so that we can retreive this message) """
        self.messages[title] = ids
        with open("json/messages.json", "wt") as f :
            f.write(json.dumps(self.messages, indent=2))
            
    async def send(self, channel: discord.TextChannel, message_content: str, wrappers: tuple[str] = ('', ''), emojis: list[discord.Reaction] = []) :
        """ This function send a message into a channel """
        message_contents = self.divide_message(message_content, wrappers=wrappers)
        messages: list[discord.Message] = []
        for msg in message_contents :
            messages.append(await channel.send(msg))
        for emoji in emojis :
            await messages[-1].add_reaction(emoji)
        return messages
    
    async def send_next_question(self, author: discord.Member) :
        if len(self.vars["members"][f"{author.name}#{author.discriminator}"]["questions"]) > 0 :
            self.vars["members"][f"{author.name}#{author.discriminator}"]["questions"].pop(0)
            if len(self.vars["members"][f"{author.name}#{author.discriminator}"]["questions"]) > 0 :
                question_type = self.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"]
                question = self.vars["members"][f"{author.name}#{author.discriminator}"]["questions"][0]
                await self.send(author.dm_channel, CREATION_QUESTIONS[question_type][question]["text"])
        self.write_json("members")


    def write_json(self, var_name: str) :
        """ This function saves the content of a bot.vars variable in the corresponding json file """
        json_object = json.dumps(self.vars[var_name], indent=2)
        with open(self.files[var_name], "wt") as f:
            f.write(json_object)

    

    