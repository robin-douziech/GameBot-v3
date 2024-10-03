from bot_clock import *

@bot.event
async def on_ready():

    bot.guild = bot.get_guild(BOT_GUILD_ID)
    bot.owner = bot.guild.get_member(BOT_OWNER_ID)
    bot.channels = {channel: bot.guild.get_channel(CHANNEL_IDS[channel]) for channel in CHANNEL_IDS}
    bot.roles = {role: bot.guild.get_role(ROLES_IDS[role]) for role in ROLES_IDS}

    # load variables and set defaults
    for var_name in bot.vars :
        with open(bot.files[var_name], "rt") as f :
            bot.vars[var_name] = db_default_config(json.load(f), bot.defaults[var_name])
            bot.write_json(var_name)
    
    # load config and set default
    with open("json/config.json", "rt") as fread :
        bot.config = default_config(json.load(fread), bot.defaults["config"])
        bot.write_config()

    bot.config["maintenance_roles_backup"] = {x: bot.config["maintenance_roles_backup"][x] if x in bot.config["maintenance_roles_backup"] else [] for x in bot.vars["members"]}
    bot.config["rules_roles_backup"] = {x: bot.config["rules_roles_backup"][x] if x in bot.config["rules_roles_backup"] else [] for x in bot.vars["members"]}
    bot.write_config()

    # load bot messages
    with open("json/messages.json", "rt") as f :
         bot.messages = json.load(f)    

    # setting logs file
    (day, month, year) = bot.get_current_datetime()[:3]
    if not(os.path.exists(f"logs/20{year}/{month}/")) :
        os.makedirs(f"logs/20{year}/{month}")
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
    handler = logging.FileHandler(f"logs/20{year}/{month}/{day}.log")
    handler.setFormatter(formatter)
    logging.getLogger().handlers = [handler]

    # guild members
    guild_members: list[str] = []
    members_to_add: list[str] = []
    members_to_remove: list[str] = []
    for member in [m for m in bot.guild.members if not(m.bot)] :
        guild_members.append(f"{member.name}#{member.discriminator}")
        if member.dm_channel is None :
            await member.create_dm()
    for member in guild_members :
        if not(member in bot.vars["members"]) :
            members_to_add.append(member)
    for member in bot.vars["members"] :
         if not(member in guild_members) :
            members_to_remove.append(member)
    await bot.add_members(members_to_add)
    bot.remove_members(members_to_remove)

    roles_to_ignore = [bot.roles[role] for role in ROLES_TO_IGNORE]
    for member in bot.vars["members"] :
        bot.vars["members"][member]["roles"] = [role.id for role in bot.get_discord_member(member).roles if not(role in roles_to_ignore)]
    bot.write_json("members")

    # MESSAGES PERMANENTS
    #
    # Message de bienvenue dans le salon #informations
    if (not("informations" in bot.messages) or await bot.get_messages_by_ids_in_channel(bot.messages["informations"], "informations") == None) :
        await bot.channels["informations"].purge()
        messages = await bot.send(bot.channels["informations"], MESSAGES["informations"])
        bot.save_message("informations", [message.id for message in messages])
    #
    # Messages de règles dans le salon #règles (si la fonctionnailité est utilisée)
    if bot.channels["rules"] is not None :
        if (not("rules" in bot.messages) or await bot.get_messages_by_ids_in_channel(bot.messages["rules"], "rules") == None) :
            await bot.channels["rules"].purge()
            messages = await bot.send(bot.channels["rules"], MESSAGES["rules"], emojis=[chr(0x1F4DD)])
            bot.save_message("rules", [message.id for message in messages])
        bot.rules_message = (await bot.get_messages_by_ids_in_channel(bot.messages["rules"][-1:], bot.channels["rules"]))[-1]
        bot.rules_reaction = [r for r in bot.rules_message.reactions if r.emoji == chr(0x1F4DD)][0]
        bot.members_having_accepted_rules = [user async for user in bot.rules_reaction.users()]
    #
    # Message de maintenance dans le salon #maintenance
    if (not("maintenance" in bot.messages) or await bot.get_messages_by_ids_in_channel(bot.messages["maintenance"], "maintenance") == None) :
        await bot.channels["maintenance"].purge()
        await bot.send(bot.channels["maintenance"], 'https://tenor.com/view/discord-gif-27684109')
        messages = await bot.send(bot.channels["maintenance"], MESSAGES["maintenance"].format(owner_mention=bot.owner.mention))
        bot.save_message("maintenance", [message.id for message in messages])

    # Gestion des rôles
    if bot.config["maintenance"] == "down" :

        # On actualise les membres du rôle "7tadellien(ne)" en fonction de qui a accepté les règles
        #
        # on donne le rôle "base" à tous ceux qui ne l'ont pas
        for member in [m for m in bot.guild.members if not(m.bot) and m.get_role(ROLES_IDS["base"]) is None] :
            await member.add_roles(bot.roles["base"])
        #
        # si la fonctionnalité "règles" est utilisée, on ajoute le rôle "7tadellien(ne)" uniquement aux membres ayant accepté les règles
        if bot.channels["rules"] is not None :

            for member in [m for m in bot.guild.members if not(m.bot)] :

                if member.get_role(ROLES_IDS["base"]) is None :
                    await member.add_roles(bot.roles["base"])

                # si le membre a accepté les règles
                if member in bot.members_having_accepted_rules :

                    for role_id in bot.config["rules_roles_backup"][f"{member.name}#{member.discriminator}"] :
                        if member.get_role(role_id) is None :
                            await member.add_roles(role_id)
                    bot.config["rules_roles_backup"][f"{member.name}#{member.discriminator}"] = []
                    bot.write_config()

                    if member.get_role(ROLES_IDS["7tadellien(ne)"]) is None :
                        await member.add_roles(bot.roles["7tadellien(ne)"])

                # si le membre n'a pas accepté les règles
                else :

                    bot.config["rules_roles_backup"][f"{member.name}#{member.discriminator}"] = await backup_roles(member, remove=True)
                    bot.write_config()

                    if member.get_role(ROLES_IDS["7tadellien(ne)"]) is not None :
                        await member.remove_roles(bot.roles["7tadellien(ne)"])

        # sinon on ajoute le rôle à tout le monde
        else :

            for member in [m for m in bot.guild.members if not(m.bot)] :

                if member.get_role(ROLES_IDS["base"]) is None :
                    await member.add_roles(bot.roles["base"])

                if member.get_role(ROLES_IDS["7tadellien(ne)"]) is None :
                    await member.add_roles(bot.roles["7tadellien(ne)"])

    else :

        for member in [m for m in bot.guild.members if not(m.bot)] :
            bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"].extend(await backup_roles(member, remove=True))
            bot.write_config()
            if member.get_role(ROLES_IDS["7tadellien(ne)"]) is not None :
                await member.remove_roles(bot.roles["7tadellien(ne)"])
            if member.get_role(ROLES_IDS["base"]) is not None :
                await member.remove_roles(bot.roles["base"])
            if member.get_role(ROLES_IDS["maintenance"]) is None :
                await member.add_roles(bot.roles["maintenance"])

    # liste de toutes les dates d'anniversaire des membres du serveur (pour petite optimisation dans clock())
    for member in bot.vars["members"] :
        m = re.match(CREATION_QUESTIONS["birthday"]["date"]["valid"], bot.vars["members"][member]["birthday"])
        if bot.vars["members"][member]["birthday"] != "0" and not(bot.vars["members"][member]["birthday"] in bot.birthday_datetimes) :
            bot.birthday_datetimes.append(f"{m.group('date')}{m.group('time')}")

    bot.log(f"{bot.user.display_name} est prêt.", 'info')    

    clock.start()

@bot.event
async def on_message(message: discord.Message) :
    author = bot.guild.get_member(message.author.id)
    if not(author.bot) and message.channel == author.dm_channel :
        bot.log(f"DM message from {author.name}#{author.discriminator} : {message.content}")
    if message.content.startswith(bot.command_prefix) :
        if message.content[1:].split(' ')[0] in [c.name for c in bot.commands] :
            await bot.process_commands(message)
        else :
            await bot.send(author.dm_channel, "Je ne connais pas cette commande")
    else :
        await bot.process_msg(message)

@bot.event
async def on_member_join(member: discord.Member) :
    pseudo = f"{member.name}#{member.discriminator}"
    if member in bot.guild.members and not(pseudo in bot.vars["members"]) :
        await bot.add_members([member])

@bot.event
async def on_member_remove(member: discord.Member) :
    pseudo = f"{member.name}#{member.discriminator}"
    if pseudo in bot.vars["members"] and not(member in bot.guild.members) :
        bot.remove_members([member])

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent) :
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    author = bot.guild.get_member(payload.user_id)

    if author is not None and not(author.bot) :

        # réaction au message des règles du serveur
        if "rules" in bot.messages and len(bot.messages["rules"]) > 0 and message.id == bot.messages["rules"][-1] :
            if payload.emoji.name == chr(0x1F4DD) :
                await author.add_roles(bot.roles["7tadellien(ne)"])
                for role_id in bot.config["rules_roles_backup"][f"{author.name}#{author.discriminator}"] :
                    await author.add_roles(bot.guild.get_role(role_id))
                bot.config["rules_roles_backup"][f"{author.name}#{author.discriminator}"] = []
                bot.write_config()
            else :
                await message.remove_reaction(payload.emoji, author)

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent) :
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    try :
        author = bot.guild.get_member(payload.user_id)
    except :
        return
    
    if author is not None and not(author.bot) :

        # réaction au message des règles du serveur
        if "rules" in bot.messages and len(bot.messages["rules"]) > 0 and message.id == bot.messages["rules"][-1] and payload.emoji.name == chr(0x1F4DD) :
            await author.remove_roles(bot.roles["7tadellien(ne)"])
            bot.config["rules_roles_backup"][f"{author.name}#{author.discriminator}"] = await backup_roles(author, remove=True)
            bot.write_config()
            
@bot.event
async def on_member_update(before: discord.Member, after: discord.Member) :

    roles_to_ignore = [bot.roles[role] for role in ROLES_TO_IGNORE]

    if after.roles != before.roles and not(after.bot) :
        
        # suppression de rôle
        for role in [r for r in before.roles if not(r in after.roles)] :

            if role.id == ROLES_IDS["base"] and bot.config["maintenance"] == "down" :
                await after.add_roles(role)

        # ajout de rôle
        for role in [r for r in after.roles if not(r in before.roles)] :

            # si le serveur est en maintenance, on ajoute l'id du rôle à la backup et on supprime le rôle
            if bot.config["maintenance"] == "up" :
                if not(role.id in bot.config["maintenance_roles_backup"][f"{after.name}#{after.discriminator}"]) :
                    bot.config["maintenance_roles_backup"][f"{after.name}#{after.discriminator}"].append(role.id)
                    bot.write_config()
                await after.remove_roles(role)

            # si le membre n'a pas accepté les règles, on ajoute l'id du rôle à la backup et on supprime le rôle
            if bot.channels["rules"] is not None and not(after in bot.members_having_accepted_rules) and not(role in roles_to_ignore) :
                if not(role.id in bot.config["rules_roles_backup"][f"{after.name}#{after.discriminator}"]) :
                    bot.config["rules_roles_backup"][f"{after.name}#{after.discriminator}"].append(role.id)
                    bot.write_config()
                await after.remove_roles(role)

        bot.write_json("members")

