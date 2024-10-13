import json, calendar, logging, sys, re, shutil, copy
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
        self.categories: dict[str, discord.CategoryChannel] = {}
        self.channels: dict[str, discord.TextChannel] = {}

        self.messages: dict[str, discord.Message] = {}

        self.birthday_datetimes = []
        self.rules_message: discord.Message = None
        self.rules_reaction: discord.Reaction = None
        self.members_having_accepted_rules: list[discord.Member] = []
        
        self.config_filename = "json/config.json"
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
        for string in ["config", "messages", "ids_test", "ids_prod"] :
            if not(os.path.exists(f"json/{string}.json")) :
                with open(f"json/{string}.json", "x") as f :
                    f.write("{}")

    async def add_members(self, pseudos: list[str]) :
        for pseudo in pseudos :

            discord_member = self.get_discord_member(pseudo)

            # on lui ajoute le rôle "base"
            await discord_member.add_roles(self.roles["base"])

            # si la fonctionnalité "règles" n'est pas utilisée on lui ajoute le rôle "7tadellien"
            if self.channels["rules"] is None :
                await discord_member.add_roles(self.roles["7tadellien"])

            # on lui crée son salon de discussion avec le bot
            await self.create_command_channel_for_member(self.get_discord_member(pseudo))

            # on l'enregistre dans bot.vars["members"]
            self.vars["members"][pseudo] = BOT_VARS_DEFAULTS["members"]
            self.write_json("members")

    async def add_member_to_present_guests(self, event_idstr: str, member: discord.Member) :

        if (event_idstr in self.vars["events"] and self.vars["events"][event_idstr]["created"]
            and f"{member.name}#{member.discriminator}" in self.vars["events"][event_idstr]["waiting_guests"]
            and (int(self.vars["events"][event_idstr]["nb_max_guests"]) == 0
                 or (int(self.vars["events"][event_idstr]["nb_max_guests"]) > 0 
                     and len(self.vars["events"][event_idstr]["present_guests"]) < int(self.vars["events"][event_idstr]["nb_max_guests"])))) :
            
            self.vars["events"][event_idstr]["waiting_guests"].remove(f"{member.name}#{member.discriminator}")
            self.vars["events"][event_idstr]["present_guests"].append(f"{member.name}#{member.discriminator}")
            self.write_json("events")

            # on lui donne accès au salon de la soirée
            await self.channels[f"soirées_{event_idstr}"].set_permissions(member, **EVENT_CHANNEL_PERMISSIONS["soirées"])

            await self.send(member.dm_channel, f"Tu es sorti(e) de la liste d'attente pour la soirée '{self.vars['events'][event_idstr]['name']}'. Tu fais donc maintenant partie des personnes qui seront présentes à cette soirée et tu as accès au salon {self.channels[f'soirées_{event_idstr}'].mention}. Tu peux toujours annuler ta venue à cette soirée en retirant ta réaction au message d'invitation ici {self.channels[f'invitations_{event_idstr}'].mention}")
            await self.send(self.channels[f"logs_{event_idstr}"], f"Changement d'état pour '{member.display_name}' : liste d'attente --> présent(e)")

            #await self.update_waiting_list(event_idstr)

        else :

            await self.send(self.channels["logsgamebot"], f"Je ne peux pas ajouter {member.display_name} à la liste des membres présents à la soirée '{self.vars['events'][event_idstr]['name']}' (event_idstr = {event_idstr})")
            raise Exception(f"Cannot add member '{member.name}#{member.discriminator}' to the present guests list for event with id '{event_idstr}'")

    async def add_member_to_waiting_guests(self, event_idstr: str, member: discord.Member) :

        if (event_idstr in self.vars["events"] and self.vars["events"][event_idstr]["created"]
            and f"{member.name}#{member.discriminator}" in self.vars["events"][event_idstr]["invited_guests"]) :

            self.vars["events"][event_idstr]["invited_guests"].remove(f"{member.name}#{member.discriminator}")
            self.vars["events"][event_idstr]["waiting_guests"].append(f"{member.name}#{member.discriminator}")
            self.write_json("events")

            await self.send(member.dm_channel, f"Tu as été ajouté(e) à la liste d'attente pour la soirée '{self.vars['events'][event_idstr]['name']}'. S'il n'y a actuellement plus de place à cette soirée, tu vas rester dans cette liste d'attente jusqu'à ce qu'il y ait à nouveau de la place. S'il reste de la place, tu devrais quitter la liste d'attente très prochainement. Je te préviendrai quand tu sortiras de cette liste d'attente.")
            await self.send(self.channels[f"logs_{event_idstr}"], f"Changement d'état pour '{member.display_name}' : invité --> liste d'attente")

            await self.update_waiting_list(event_idstr)

        else :
            await self.send(self.channels["logsgamebot"], f"Je ne peux pas ajouter {member.display_name} à la liste d'attente de la soirée '{self.vars['events'][event_idstr]['name']}' (event_idstr = {event_idstr})")
            raise Exception(f"Cannot add member '{member.name}#{member.discriminator}' to the waiting list for event with id '{event_idstr}'")

    def admin_command(self, function: callable) :
        """ Decorator to apply to a command so that only members with admin role can use it """
        async def wrapper(ctx: commands.Context, *args, **kwargs) :
            author = self.guild.get_member(ctx.author.id)
            if author.get_role(ROLES_IDS["admin"]) is not None :
                await function(ctx, *args, **kwargs)
        return wrapper
    
    def answer_is_valid(self, author: discord.Member, answer: str) :
        question = self.vars["members"][f"{author.name}#{author.discriminator}"]["questions"][0]
        valid = CREATION_QUESTIONS[self.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"]][question]["valid"]
        return re.match(valid, answer)
    
    async def cancel_participation(self, event_idstr: str, member: discord.Member) :

        if (event_idstr in self.vars["events"] and self.vars["events"][event_idstr]["created"]
            and f"{member.name}#{member.discriminator}" in self.vars["events"][event_idstr]["waiting_guests"]
                                                         + self.vars["events"][event_idstr]["present_guests"]) :
            
            if f"{member.name}#{member.discriminator}" in self.vars["events"][event_idstr]["waiting_guests"] :
                self.vars["events"][event_idstr]["waiting_guests"].remove(f"{member.name}#{member.discriminator}")
                self.vars["events"][event_idstr]["invited_guests"].append(f"{member.name}#{member.discriminator}")
                await self.send(member.dm_channel, f"Tu as été retiré(e) de la liste d'attente pour la soirée '{self.vars['events'][event_idstr]['name']}'. Tu es cependant toujours invité(e) à cette soirée donc si tu changes d'avis et souhaites finalement y participer, tu peux remettre ta réaction dans le salon {self.channels[f'invitations_{event_idstr}'].mention}.")
                await self.send(self.channels[f"logs_{event_idstr}"], f"Changement d'état pour '{member.display_name}' : liste d'attente --> invité(e)")
            else :
                self.vars["events"][event_idstr]["present_guests"].remove(f"{member.name}#{member.discriminator}")
                self.vars["events"][event_idstr]["invited_guests"].append(f"{member.name}#{member.discriminator}")
                await self.remove_permissions_on_channel(self.channels[f"soirées_{event_idstr}"], member)
                await self.send(member.dm_channel, f"Tu as été retiré(e) des membres présents à la soirée '{self.vars['events'][event_idstr]['name']}'. Tu es cependant toujours invité(e) à cette soirée donc si tu changes d'avis et souhaites finalement y participer, tu peux remettre ta réaction dans le salon {self.channels[f'invitations_{event_idstr}'].mention}.")
                await self.send(self.channels[f"logs_{event_idstr}"], f"Changement d'état pour '{member.display_name}' : présent(e) --> invité(e)")
            self.write_json("events")

            await self.update_waiting_list(event_idstr)

        else :

            await self.send(self.channels["logsgamebot"], f"Je ne peux pas annuler la participation de {member.display_name} à la soirée '{self.vars['events'][event_idstr]['name']}' (event_idstr = {event_idstr})")
            raise Exception(f"Cannot cancel participation of member '{member.name}#{member.discriminator}' to the event with id '{event_idstr}'")

    async def create_command_channel_for_member(self, member: discord.Member) :
        """Create the member's command channel with appropriate permissions (depending on maintenance status and rules acceptation)"""
        permissions = self.config["maintenance"] == "down" and (self.channels["rules"] is None or member in self.members_having_accepted_rules) and not(self.vars["members"][f"{member.name}#{member.discriminator}"]["banned"])
        member_permissions = {
            "read_messages": permissions,
            "send_messages": permissions,
            "create_instant_invite": False
        }
        self.channels[f"bot_{member.name}#{member.discriminator}"] = await self.guild.create_text_channel(
            name="utilise-gamebot-ici",
            category=self.categories["bot"],
            topic=f"{member.name}#{member.discriminator}",
            overwrites={
                member: discord.PermissionOverwrite(**member_permissions),
                self.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False, create_instant_invite=False)
            }
        )
    
    async def delete_event(self, event_idstr: str) :

        try :

            if event_idstr in self.vars["events"] and self.vars["events"][event_idstr]["created"] :

                (day, month, year, hour, minute) = self.get_current_datetime()
                current_datetime = f"{day}/{month}/20{year} {hour}:{minute}"

                # on informe tous les invités si la soirée n'est pas passée
                if datetime_cmp(current_datetime, self.vars["events"][event_idstr]["datetime"]) < 0 :
                    for pseudo in self.vars["events"][event_idstr]["invited_guests"] \
                                + self.vars["events"][event_idstr]["waiting_guests"] \
                                + self.vars["events"][event_idstr]["present_guests"] :
                        await self.send(self.get_discord_member(pseudo).dm_channel, f"**__ATTENTION__:** La soirée '{self.vars['events'][event_idstr]['name']}' a été supprimée")
                    
                # on supprime les salons
                for string in ["invitations", "soirées", "logs"] :
                    await self.channels[f"{string}_{event_idstr}"].delete()
                    self.channels.pop(f"{string}_{event_idstr}")

                # on supprime l'event dans self.vars["events"]
                self.vars["events"].pop(event_idstr)
                self.write_json("events")

        except Exception as e :

            await self.send(self.channels["logsgamebot"], f"Quelque chose s'est mal passé pendant la suppression d'une soirée.\nevent_idstr: {event_idstr}\nerror: {e}")
            raise Exception(e)
    
    def divide_message(self, message_content: str, wrappers: tuple[str] = ('', '')) :
        """ This function splits a message content so that its length doesn't exceed DISCORD_MAX_MESSAGE_LENGTH """
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
    
    async def invite_member(self, event_idstr: str, member: discord.Member) :

        if (event_idstr in self.vars["events"] and self.vars["events"][event_idstr]["created"]
            and not(member.id in self.vars["events"][event_idstr]["invited_members"])
            and not(member.bot)) :
            
            # on ajoute le membre à la liste des invités
            msg = ""
            if not(self.member_is_invited_to_event(event_idstr, member)) :
                self.vars["events"][event_idstr]["invited_guests"].append(f"{member.name}#{member.discriminator}")
                msg = f"Changement d'état pour '{member.display_name}' : pas invité(e) --> invité(e)"
            self.vars["events"][event_idstr]["invited_members"].append(member.id)
            self.write_json("events")

            # on lui donne accès au salon d'invitation
            await self.channels[f"invitations_{event_idstr}"].set_permissions(member, **EVENT_CHANNEL_PERMISSIONS["invitations"])

            if len(msg) > 0 :
                await self.send(self.channels[f"logs_{event_idstr}"], msg)

        else :
            await self.send(self.channels["logsgamebot"], f"Quelque chose s'est mal passé pendant l'invitation d'un membre à une soirée.\nsoirée: {event_idstr} - {self.vars['events'][event_idstr]['name']}\nmembre : {member.display_name}")
            raise Exception(f"Cannot invite member '{member.display_name}' to the event")

    async def invite_role(self, event_idstr: str, role: discord.Role) :

        if (event_idstr in self.vars["events"] and self.vars["events"][event_idstr]["created"]
            and not(role.id in self.vars["events"][event_idstr]["invited_roles"])) :

            # on ajoute les membres dans les listes de la soirée
            msg = ""
            for member in [m for m in role.members if not(m.bot) and not(self.member_is_invited_to_event(event_idstr, m))] :
                self.vars["events"][event_idstr]["invited_guests"].append(f"{member.name}#{member.discriminator}")
                msg += f"Changement d'état pour '{member.display_name}' : pas invité(e) --> invité(e)\n"
            self.vars["events"][event_idstr]["invited_roles"].append(role.id)
            self.write_json("events")

            # on donne accès au salon d'invitation au rôle
            await self.channels[f"invitations_{event_idstr}"].set_permissions(role, **EVENT_CHANNEL_PERMISSIONS["invitations"])
            
            if len(msg) > 0 :
                await self.send(self.channels[f"logs_{event_idstr}"], msg)

        else :
            await self.send(self.channels["logsgamebot"], f"Quelque chose s'est mal passé pendant l'invitation d'un rôle à une soirée.\nsoirée: {event_idstr} - {self.vars['events'][event_idstr]['name']}\nrole : {role.name}")
            raise Exception(f"Cannot invite role '{role.name}' to the event")
    
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
            
    def member_is_invited_to_event(self, event_idstr: str, member: discord.Member) :
        return (any([role_id in self.vars["events"][event_idstr]["invited_roles"]
                     for role_id in [role.id for role in member.roles]
                                    + self.config["ban_roles_backup"][f"{member.name}#{member.discriminator}"]
                                    + self.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"]
                                    + self.config["rules_roles_backup"][f"{member.name}#{member.discriminator}"]])
                or member.id in self.vars["events"][event_idstr]["invited_members"])
            
    def private_command(self, function: callable) :
        """ Decorator to apply to a command so it can only be sent in the dedicated private channel """
        async def wrapper(ctx: commands.Context, *args, **kwargs):
            author = self.guild.get_member(ctx.author.id)
            if not(f"bot_{author.name}#{author.discriminator}" in self.channels) :
                await self.create_command_channel_for_member(author)
            if ctx.channel == self.channels[f"bot_{author.name}#{author.discriminator}"] or ctx.channel == author.dm_channel :
                await function(ctx, *args, **kwargs)
            else :
                message = await ctx.channel.fetch_message(ctx.message.id)
                await ctx.channel.delete_messages([message])
                await self.send(self.channels[f"bot_{author.name}#{author.discriminator}"], f"Pour utiliser mes commandes, ça se passe ici ou par messages privés")
                await self.send(author.dm_channel, f"Pour utiliser mes commandes, ça se passe ici ... ou là bas {self.channels[f'bot_{author.name}#{author.discriminator}'].mention}")
        return wrapper
            
    async def process_msg(self, message: discord.Message) :
        author = self.guild.get_member(message.author.id)

        if not(author.bot) :

            if self.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"] :

                match (self.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"]) :
                    case "birthday" :
                        if self.answer_is_valid(author, message.content) :

                            # Si c'était le seul à avoir cette date d'anniversaire, on la retire de self.birthday_datetimes
                            self.birthday_datetimes = [birthday_datetime[:5]+birthday_datetime[-6:] for birthday_datetime in [self.vars["members"][pseudo]["birthday"] for pseudo in self.vars["members"] if self.vars["members"][pseudo]["birthday"] != "0" and pseudo != f"{author.name}#{author.discriminator}"]]

                            # Selon le format du message reçu, on adapte la valeur stockée (on ajoute 00:00 si l'heure n'est pas précisée) et le message de confirmation
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
                            if birthday != "0" :
                                self.birthday_datetimes = list(set(self.birthday_datetimes + [f"{birthday[:5]} {birthday[-5:]}"]))
                            self.write_json("members")

                            await self.send(message.channel, response)
                            await self.send_next_question(message.channel, author)

                        else :
                            await self.send(message.channel, "Ta réponse ne respecte pas le format attendu")

                    case 'event' :
                        if self.answer_is_valid(author, message.content) :
                            event_id = self.vars["members"][f"{author.name}#{author.discriminator}"]["object_id"]
                            event_idstr = f"{author.name}#{author.discriminator}:{event_id}"
                            question = self.vars["members"][f"{author.name}#{author.discriminator}"]["questions"][0]
                            self.vars["events"][event_idstr][question] = message.content
                            self.write_json("events")
                            await self.send_next_question(message.channel, author)

                            if not(self.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"]) :

                                # changer le format de host
                                if self.vars["events"][event_idstr]["host"] == '.' :
                                    self.vars["events"][event_idstr]["host"] = f"{author.mention}"
                                else :
                                    self.vars["events"][event_idstr]["host"] = f"{self.vars['events'][event_idstr]['host']} ({author.mention})"

                                # renommer les salons
                                for string in ["invitations", "soirées", "logs"] :
                                    await self.channels[f"{string}_{event_idstr}"].edit(name=self.vars["events"][event_idstr]["name"])

                                # envoyer le message d'invitation
                                await self.send(self.channels[f"invitations_{event_idstr}"], MESSAGES["invitation"].format(
                                    host = self.vars['events'][event_idstr]['host'],
                                    lieu = self.vars['events'][event_idstr]['place'],
                                    date = self.vars['events'][event_idstr]['datetime'].split()[0],
                                    heure = self.vars['events'][event_idstr]['datetime'].split()[1],
                                    description = self.vars['events'][event_idstr]['description'],
                                    NB = f"\nIl y a un total de {self.vars['events'][event_idstr]['nb_max_guests']} places disponibles (hôte compris). Si plus de personnes souhaitent participer, je m'occuperai de gérer la liste d'attente" if int(self.vars['events'][event_idstr]['nb_max_guests']) > 0 else ''
                                ), emojis=[chr(0x1F44D)])

                                self.vars["events"][event_idstr]["created"] = True

                                self.write_json("events")

                    case _ :
                        pass

    async def remove_members(self, tup: list[tuple[str, int]]) :
        try :
            for t in tup :
                
                pseudo, member_id = t

                # on supprime toutes ses soirées
                for event_idstr in [id for id in self.vars["events"] if id.split(':')[0] == pseudo] :
                    await self.delete_event(event_idstr)

                # on le désinvite des soirées auxquelles il est invité
                for event_idstr in [id for id in self.vars["events"] if pseudo in self.vars["events"][id]["invited_guests"]
                                                                                + self.vars["events"][id]["waiting_guests"]
                                                                                + self.vars["events"][id]["present_guests"]] :
                    if member_id in self.vars["events"][event_idstr]["invited_members"] :
                        self.vars["events"][event_idstr]["invited_members"].remove(member_id)
                    if pseudo in self.vars["events"][id]["invited_guests"] :
                        self.vars["events"][id]["invited_guests"].remove(pseudo)
                    elif pseudo in self.vars["events"][id]["waiting_guests"] :
                        self.vars["events"][id]["waiting_guests"].remove(pseudo)
                    elif pseudo in self.vars["events"][id]["present_guests"] :
                        self.vars["events"][id]["present_guests"].remove(pseudo)
                    self.write_json("events")

                    await self.update_waiting_list(event_idstr)

                if f"bot_{pseudo}" in self.channels :
                    await self.channels[f"bot_{pseudo}"].delete()
                    self.channels.pop(f"bot_{pseudo}")

                self.vars["members"].pop(pseudo)
                self.write_json("members")
        except Exception as e :
            self.log(f"{e} (while trying to delete a member)", "error")

    async def remove_member_from_invited_guests(self, event_idstr: str, member: discord.Member) :

        if (event_idstr in self.vars["events"] and self.vars["events"][event_idstr]["created"]
            and f"{member.name}#{member.discriminator}" in self.vars["events"][event_idstr]["invited_guests"]) :

            self.vars["events"][event_idstr]["invited_guests"].remove(f"{member.name}#{member.discriminator}")
            self.write_json("events")

            await (await self.get_all_messages_in_channel(self.channels[f"invitations_{event_idstr}"]))[-1].remove_reaction(chr(0x1F44D), member)

            await self.remove_permissions_on_channel(self.channels[f"invitations_{event_idstr}"], member)

            await self.send(self.channels[f"logs_{event_idstr}"], f"Changement d'état pour '{member.display_name}' : invité --> pas invité")

        else :

            await self.send(self.channels["logsgamebot"], f"Je ne peux pas ajouter {member.display_name} à la liste d'attente de la soirée '{self.vars['events'][event_idstr]['name']}' (event_idstr = {event_idstr})")
            raise Exception(f"Cannot remove member '{member.name}#{member.discriminator}' from the invited_guests list for event with id '{event_idstr}'")

    async def remove_member_from_present_guests(self, event_idstr: str, member: discord.Member) :
        
        if (event_idstr in self.vars["events"] and self.vars["events"][event_idstr]["created"]
            and f"{member.name}#{member.discriminator}" in self.vars["events"][event_idstr]["present_guests"]) :

            self.vars["events"][event_idstr]["present_guests"].remove(f"{member.name}#{member.discriminator}")
            self.write_json("events")

            await (await self.get_all_messages_in_channel(self.channels[f"invitations_{event_idstr}"]))[-1].remove_reaction(chr(0x1F44D), member)

            await self.remove_permissions_on_channel(self.channels[f"invitations_{event_idstr}"], member)
            await self.remove_permissions_on_channel(self.channels[f"soirées_{event_idstr}"], member)

            await self.send(member.dm_channel, f"Tu as été retiré(e) des personnes invitées à la soirée '{self.vars['events'][event_idstr]['name']}'.")
            await self.send(self.channels[f"logs_{event_idstr}"], f"Changement d'état pour '{member.display_name}' : présent --> pas invité")

            await self.update_waiting_list(event_idstr)

        else :

            await self.send(self.channels["logsgamebot"], f"Je ne peux pas ajouter {member.display_name} à la liste d'attente de la soirée '{self.vars['events'][event_idstr]['name']}' (event_idstr = {event_idstr})")
            raise Exception(f"Cannot remove member '{member.name}#{member.discriminator}' from the present_guests list for event with id '{event_idstr}'")

    async def remove_member_from_waiting_guests(self, event_idstr: str, member: discord.Member) :
        
        if (event_idstr in self.vars["events"] and self.vars["events"][event_idstr]["created"]
            and f"{member.name}#{member.discriminator}" in self.vars["events"][event_idstr]["waiting_guests"]) :

            self.vars["events"][event_idstr]["waiting_guests"].remove(f"{member.name}#{member.discriminator}")
            self.write_json("events")

            await (await self.get_all_messages_in_channel(self.channels[f"invitations_{event_idstr}"]))[-1].remove_reaction(chr(0x1F44D), member)

            await self.remove_permissions_on_channel(self.channels[f"invitations_{event_idstr}"], member)

            await self.send(member.dm_channel, f"Tu as été retiré(e) des personnes invitées à la soirée '{self.vars['events'][event_idstr]['name']}'.")
            await self.send(self.channels[f"logs_{event_idstr}"], f"Changement d'état pour '{member.display_name}' : liste d'attente --> pas invité")

            await self.update_waiting_list(event_idstr)

        else :

            await self.send(self.channels["logsgamebot"], f"Je ne peux pas ajouter {member.display_name} à la liste d'attente de la soirée '{self.vars['events'][event_idstr]['name']}' (event_idstr = {event_idstr})")
            raise Exception(f"Cannot remove member '{member.name}#{member.discriminator}' from the waiting_guests list for event with id '{event_idstr}'")
        
    async def remove_permissions_on_channel(self, channel: discord.TextChannel, target: discord.Member|discord.Role) :
        await channel.set_permissions(target, overwrite=None)
        
    def role_is_invited_to_event(self, event_idstr: str, role: discord.Role) :
        return (role.id in self.vars["events"][event_idstr]["invited_roles"])

    def save_message(self, title: str, ids: list[int]) :
        """ This function saves an official bot message into json/messages.json (so that we can retreive this message) """
        self.messages[title] = ids
        with open("json/messages.json", "wt") as f :
            f.write(json.dumps(self.messages, indent=2))
            
    async def send(self, channel: discord.TextChannel, message_content: str, wrappers: tuple[str] = ('', ''), emojis: list[discord.Reaction] = []) :
        """ This function sends a message into a channel """
        message_contents = self.divide_message(message_content, wrappers=wrappers)
        messages: list[discord.Message] = []
        for msg in message_contents :
            messages.append(await channel.send(msg))
        for emoji in emojis :
            await messages[-1].add_reaction(emoji)
        return messages
    
    async def send_next_question(self, channel: discord.TextChannel, author: discord.Member) :
        if len(self.vars["members"][f"{author.name}#{author.discriminator}"]["questions"]) > 0 :
            self.vars["members"][f"{author.name}#{author.discriminator}"]["questions"].pop(0)
            if len(self.vars["members"][f"{author.name}#{author.discriminator}"]["questions"]) > 0 :
                question_type = self.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"]
                question = self.vars["members"][f"{author.name}#{author.discriminator}"]["questions"][0]
                await self.send(channel, CREATION_QUESTIONS[question_type][question]["text"])
            else :
                self.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"] = ""
                self.vars["members"][f"{author.name}#{author.discriminator}"]["object_id"] = 0
        self.write_json("members")

    async def uninvite_member(self, event_idstr: str, member: discord.Member) :

        if (event_idstr in self.vars["events"] and self.vars["events"][event_idstr]["created"]
            and member.id in self.vars["events"][event_idstr]["invited_members"]) and member != self.get_discord_member(event_idstr.split(':')[0]) :
            
            if f"{member.name}#{member.discriminator}" in self.vars["events"][event_idstr]["invited_guests"] :
                await self.remove_member_from_invited_guests(event_idstr, member)

            elif f"{member.name}#{member.discriminator}" in self.vars["events"][event_idstr]["waiting_guests"] :
                await self.remove_member_from_waiting_guests(event_idstr, member)

            elif f"{member.name}#{member.discriminator}" in self.vars["events"][event_idstr]["present_guests"] :
                await self.remove_member_from_present_guests(event_idstr, member)

            self.vars["events"][event_idstr]["invited_members"].remove(member.id)
            self.write_json("events")

        else:
            await self.send(self.channels["logsgamebot"], f"Je n'ai pas réussi à désinviter {member.display_name} d'une soirée")
            raise Exception(f"Cannot uninvite '{member.display_name}' from the event")
        
    async def uninvite_role(self, event_idstr: str, role: discord.Role) :
        
        if (event_idstr in self.vars["events"] and self.vars["events"][event_idstr]["created"]
            and role.id in self.vars["events"][event_idstr]["invited_roles"]) :

            # membres invités autrement que via ce rôle 
            invited_members = [self.guild.get_member(member_id) for member_id in self.vars["events"][event_idstr]["invited_members"]] \
                            + [m for r in [self.guild.get_role(role_id) for role_id in self.vars["events"][event_idstr]["invited_roles"] if role_id != role.id] for m in r.members]
            
            # on supprime les membres qui ne sont plus invités
            msg = ""
            for member in [m for m in role.members if not(m in invited_members)] :
                pseudo = f"{member.name}#{member.discriminator}"
                if pseudo in self.vars["events"][event_idstr]["invited_guests"] :
                    self.vars["events"][event_idstr]["invited_guests"].remove(pseudo)
                    msg += f"Changement d'état pour '{member.display_name}' : invité --> pas invité (le rôle '{role.name}' n'est plus invité)\n"
                if pseudo in self.vars["events"][event_idstr]["waiting_guests"] :
                    self.vars["events"][event_idstr]["waiting_guests"].remove(pseudo)
                    msg += f"Changement d'état pour '{member.display_name}' : liste d'attente --> pas invité (le rôle '{role.name}' n'est plus invité)\n"
                    await (await self.get_all_messages_in_channel(self.channels[f"invitations_{event_idstr}"]))[-1].remove_reaction(chr(0x1F44D), member)
                    await self.send(member.dm_channel, f"Tu as été retiré(e) des personnes invitées à la soirée '{self.vars['events'][event_idstr]['name']}' car le rôle '{role.name}' n'est plus invité.")
                if pseudo in self.vars["events"][event_idstr]["present_guests"] :
                    self.vars["events"][event_idstr]["present_guests"].remove(pseudo)
                    msg += f"Changement d'état pour '{member.display_name}' : présent --> pas invité (le rôle '{role.name}' n'est plus invité)\n"
                    await (await self.get_all_messages_in_channel(self.channels[f"invitations_{event_idstr}"]))[-1].remove_reaction(chr(0x1F44D), member)
                    await self.send(member.dm_channel, f"Tu as été retiré(e) des personnes invitées à la soirée '{self.vars['events'][event_idstr]['name']}' car le rôle '{role.name}' n'est plus invité.")
                    await self.remove_permissions_on_channel(self.channels[f"soirées_{event_idstr}"], member)
            self.vars["events"][event_idstr]["invited_roles"].remove(role.id)
            self.write_json("events")

            # on retire les droits sur le salon d'invitation au rôle
            await self.remove_permissions_on_channel(self.channels[f"invitations_{event_idstr}"], role)

            if len(msg) > 0 :
                await self.send(self.channels[f"logs_{event_idstr}"], msg)

            await self.update_waiting_list(event_idstr)

        else :
            await self.send(self.channels["logsgamebot"], f"Quelque chose s'est mal passé pendant l'annulation de l'invitation d'un rôle à une soirée.\nsoirée: {event_idstr} - {self.vars['events'][event_idstr]['name']}\nrole : {role.name}")
            raise Exception(f"Cannot uninvite role '{role.name}' from the event")            
        
    async def update_permissions_on_event_channels(self, member: discord.Member|None = None) :
        """Ajuste les permissions sur les salons des soirées pour le membre renseigné ou pour tout le monde si aucun membre n'est renseigné
        en fonction de l'état de maintenance du serveur et de la réaction au message des règles si cette fonctionnalité est utilisée
        Cela ne désinvite pas le membre des soirées, ça l'empêche temporairement de voir les salon (jusqu'à la fin de la maintenance
        ou tant qu'il n'a pas réagis au message des règles)."""

        members_can_see_channels = self.config["maintenance"] == "down"

        if member is None : # on anctualise les permissions des salons pour tous les membres du serveur

            for event_idstr in self.vars["events"] :

                # on ajuste les permissions du salon de logs
                host = self.get_discord_member(event_idstr.split(':')[0])
                host_can_see_channels = members_can_see_channels and (self.channels["rules"] is None or host in self.members_having_accepted_rules) and not(self.vars["members"][f"{host.name}#{host.discriminator}"]["banned"])
                if host_can_see_channels :
                    await self.channels[f"logs_{event_idstr}"].set_permissions(host, **EVENT_CHANNEL_PERMISSIONS["logs"])
                else :
                    await self.remove_permissions_on_channel(self.channels[f"logs_{event_idstr}"], host)

                # pour chaque invité ...
                for member_id in self.vars["events"][event_idstr]["invited_members"] :
                    
                    member = self.guild.get_member(member_id)
                    pseudo = f"{member.name}#{member.discriminator}"
                    can_see_channels = members_can_see_channels and (self.channels["rules"] is None or member in self.members_having_accepted_rules) and not(self.vars["members"][pseudo]["banned"])

                    # on ajuste les permissions du salon d'invitation
                    if can_see_channels :
                        await self.channels[f"invitations_{event_idstr}"].set_permissions(member, **EVENT_CHANNEL_PERMISSIONS["invitations"])
                    else :
                        await self.remove_permissions_on_channel(self.channels[f"invitations_{event_idstr}"], member)
                    
                    # on ajuste les permissions du salon de la soirée
                    if pseudo in self.vars["events"][event_idstr]["present_guests"] :
                        if can_see_channels :
                            await self.channels[f"soirées_{event_idstr}"].set_permissions(member, **EVENT_CHANNEL_PERMISSIONS["soirées"])
                        else :
                            await self.remove_permissions_on_channel(self.channels[f"soirées_{event_idstr}"], member)

        else : # on anctualise les permissions des salons pour le membre renseigné

            pseudo = f"{member.name}#{member.discriminator}"
            can_see_channels = members_can_see_channels and (self.channels["rules"] is None or member in self.members_having_accepted_rules) and not(self.vars["members"][pseudo]["banned"])

            for event_idstr in self.vars["events"] :

                # si le membre est l'hôte de la soirée
                if pseudo == event_idstr.split(':')[0] :
                    if can_see_channels :
                        await self.channels[f"logs_{event_idstr}"].set_permissions(member, **EVENT_CHANNEL_PERMISSIONS["logs"])
                    else :
                        await self.remove_permissions_on_channel(self.channels[f"logs_{event_idstr}"], member)

                # si le membre est invité
                if member.id in self.vars["events"][event_idstr]["invited_members"] :

                    if can_see_channels :
                        await self.channels[f"invitations_{event_idstr}"].set_permissions(member, **EVENT_CHANNEL_PERMISSIONS["invitations"])
                    else :
                        await self.remove_permissions_on_channel(self.channels[f"invitations_{event_idstr}"], member)

                    # si le membre est présent à la soirée
                    if pseudo in self.vars["events"][event_idstr]["present_guests"] :
                        if can_see_channels :
                            await self.channels[f"soirées_{event_idstr}"].set_permissions(member, **EVENT_CHANNEL_PERMISSIONS["soirées"])
                        else :
                            await self.remove_permissions_on_channel(self.channels[f"soirées_{event_idstr}"], member)

    async def update_waiting_list(self, event_idstr: str) :

        if event_idstr in self.vars["events"] and self.vars["events"][event_idstr]["created"] :

            if int(self.vars["events"][event_idstr]["nb_max_guests"]) == 0 :

                for pseudo in self.vars["events"][event_idstr]["waiting_guests"] :
                    await self.add_member_to_present_guests(event_idstr, self.get_discord_member(pseudo))

            elif len(self.vars["events"][event_idstr]["present_guests"]) < int(self.vars["events"][event_idstr]["nb_max_guests"]) :

                for pseudo in self.vars["events"][event_idstr]["waiting_guests"][:(int(self.vars["events"][event_idstr]["nb_max_guests"]) - len(self.vars["events"][event_idstr]["present_guests"]))] :
                    await self.add_member_to_present_guests(event_idstr, self.get_discord_member(pseudo))

        else :
            await self.send(self.channels["logsgamebot"], f"Je ne peux pas mettre à jour la liste d'attente pour la soirée '{self.vars['events'][event_idstr]['name']}' (event_idstr = {event_idstr})")
            raise Exception(f"Cannot update waiting list for event with id '{event_idstr}'")

    def write_json(self, var_name: str) :
        """ This function saves the content of a bot.vars variable in the corresponding json file """
        with open(self.files[var_name], "wt") as f:
            f.write(json.dumps(self.vars[var_name], indent=2))

    def write_config(self) :
        with open(self.config_filename, "wt") as f :
            f.write(json.dumps(self.config, indent=2))

    

    