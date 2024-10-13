from bot_clock import *

@bot.event
async def on_ready():

    global BOT_GUILD_ID, BOT_OWNER_ID, CATEGORY_IDS, CHANNEL_IDS, ROLES_IDS

    # on récupère la config (et on vérifie qu'elle a le bon format)
    with open("json/config.json", "rt") as f :
        bot.config = default_config(json.load(f), bot.defaults["config"])
    bot.write_config()

    # on récupère les variables (et on vérifie qu'elles ont le bon format)
    for var_name in bot.vars :
        with open(bot.files[var_name], "rt") as f :
            bot.vars[var_name] = db_default_config(json.load(f), bot.defaults[var_name])
        bot.write_json(var_name)

    # on  récupère les identifiants des objets discord (rôles, salons, catégories, serveur, propriétaire du bot)
    ids_filename = "json/ids_prod.json" if os.getenv("ENV") == "PROD" else "json/ids_test.json"
    with open(ids_filename, "rt") as f :
        ids = json.load(f)
        if 'BOT_GUILD_ID' in ids and ids['BOT_GUILD_ID'] != 0 :
            BOT_GUILD_ID = ids['BOT_GUILD_ID']
        if 'BOT_OWNER_ID' in ids and ids['BOT_OWNER_ID'] != 0 :
            BOT_OWNER_ID = ids['BOT_OWNER_ID']
        if 'CATEGORY_IDS' in ids :
            for category_name in [name for name in ids['CATEGORY_IDS'] if ids['CATEGORY_IDS'][name] != 0] :
                CATEGORY_IDS[category_name] = ids['CATEGORY_IDS'][category_name]
        if 'CHANNEL_IDS' in ids :
            for channel_name in [name for name in ids['CHANNEL_IDS'] if ids['CHANNEL_IDS'][name] != 0] :
                CHANNEL_IDS[channel_name] = ids['CHANNEL_IDS'][channel_name]
        if 'ROLES_IDS' in ids :
            for role_name in [name for name in ids['ROLES_IDS'] if ids['ROLES_IDS'][name] != 0] :
                ROLES_IDS[role_name] = ids['ROLES_IDS'][role_name]

    # propriétaire du bot
    bot.guild = bot.get_guild(BOT_GUILD_ID)

    # serveur du bot
    bot.owner = bot.guild.get_member(BOT_OWNER_ID)

    # création ou récupération des rôles
    for role_name in ROLES_IDS :
        if bot.guild.get_role(ROLES_IDS[role_name]) is None :
            if not(role_name in [role.name for role in bot.guild.roles]) :
                ROLES_IDS[role_name] = (await bot.guild.create_role(name=role_name)).id
            else :
                ROLES_IDS[role_name] = get_role_by_name(role_name).id
    bot.roles = {role: bot.guild.get_role(ROLES_IDS[role]) for role in ROLES_IDS}
    perm = discord.Permissions.none()
    perm.administrator = True
    await bot.roles["admin"].edit(permissions=perm)
    await bot.guild.get_member(BOT_OWNER_ID).add_roles(bot.roles["admin"])

    # création ou récupération des catégories
    for category_name in CATEGORY_IDS :
        if discord.utils.get(bot.guild.categories, id=CATEGORY_IDS[category_name]) is None :
            CATEGORY_IDS[category_name] = (await bot.guild.create_category(name=category_name.upper(), overwrites={
                bot.guild.default_role: discord.PermissionOverwrite(read_messages=False)
            })).id
    bot.categories = {category: discord.utils.get(bot.guild.categories, id=CATEGORY_IDS[category]) for category in CATEGORY_IDS}

    # création ou récupération des salons
    bot.channels = {}
    overwrite_none = discord.PermissionOverwrite()
    for perm in discord.Permissions() :
        setattr(overwrite_none, perm[0], False)
    overwrite = copy.deepcopy(overwrite_none)
    overwrite.read_messages = True
    overwrite.add_reactions = True
    overwrite.read_message_history = True
    for role_name in ROLES_IDS :
        for channel_name in CHANNELS_BY_ROLE[role_name] :
            if ((bot.config["rules"] or channel_name != "rules") and bot.guild.get_channel(CHANNEL_IDS[channel_name]) is None) :
                CHANNEL_IDS[channel_name] = (await bot.guild.create_text_channel(channel_name, overwrites={
                    bot.guild.default_role: overwrite_none,
                    bot.roles[role_name]: overwrite
                })).id
            elif (bot.config["rules"] or channel_name != "rules")  :
                await bot.guild.get_channel(CHANNEL_IDS[channel_name]).set_permissions(bot.guild.default_role, overwrite=overwrite_none)
                await bot.guild.get_channel(CHANNEL_IDS[channel_name]).set_permissions(bot.roles[role_name], overwrite=overwrite)
    bot.channels = {channel: bot.guild.get_channel(CHANNEL_IDS[channel]) for channel in CHANNEL_IDS}

    # on enregistre les identifiants
    with open(ids_filename, "wt") as f :
        f.write(json.dumps({
            "BOT_GUILD_ID": bot.guild.id,
            "BOT_OWNER_ID": bot.owner.id,
            "CATEGORY_IDS": CATEGORY_IDS,
            "CHANNEL_IDS": CHANNEL_IDS,
            "ROLES_IDS": ROLES_IDS
        }, indent=2))
    
    # on récupère les salons des soirées
    for event_idstr in bot.vars["events"] :
        for string in ["invitations", "soirées", "logs"] :
            bot.channels[f"{string}_{event_idstr}"] = bot.guild.get_channel(bot.vars["events"][event_idstr][f"{string}_channel_id"])

    # on supprime les salon des soirées inexistantes
    for string in ["invitations", "soirées", "logs"] :
        category = bot.categories[string]
        for channel in category.channels :
            if not(channel.id in [c.id for c in bot.channels.values()]) :
                await channel.delete()

    # on récupère les messages permanents du bot
    with open("json/messages.json", "rt") as f :
         bot.messages = json.load(f)    

    # on définit le fichier de logs
    (day, month, year) = bot.get_current_datetime()[:3]
    if not(os.path.exists(f"logs/20{year}/{month}/")) :
        os.makedirs(f"logs/20{year}/{month}")
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
    handler = logging.FileHandler(f"logs/20{year}/{month}/{day}.log")
    handler.setFormatter(formatter)
    logging.getLogger().handlers = [handler]

    # on gère les membres du serveur
    guild_members: list[str] = []
    members_to_add: list[str] = []
    members_to_remove: list[str] = []
    for member in [m for m in bot.guild.members if not(m.bot)] :
        guild_members.append(f"{member.name}#{member.discriminator}")
        if member.dm_channel is None :
            await member.create_dm()
    for pseudo in guild_members :
        if not(pseudo in bot.vars["members"]) :
            members_to_add.append(pseudo)
    for pseudo in bot.vars["members"] :
         if not(pseudo in guild_members) :
            members_to_remove.append((pseudo, bot.get_discord_member(pseudo).id))
    await bot.add_members(members_to_add)
    await bot.remove_members(members_to_remove)

    bot.config["ban_roles_backup"] = {x: bot.config["ban_roles_backup"][x] if x in bot.config["ban_roles_backup"] else [] for x in bot.vars["members"]}
    bot.config["maintenance_roles_backup"] = {x: bot.config["maintenance_roles_backup"][x] if x in bot.config["maintenance_roles_backup"] else [] for x in bot.vars["members"]}
    bot.config["rules_roles_backup"] = {x: bot.config["rules_roles_backup"][x] if x in bot.config["rules_roles_backup"] else [] for x in bot.vars["members"]}
    bot.write_config()

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
        bot.members_having_accepted_rules = [user async for user in bot.rules_reaction.users() if not(user.bot)]
    #
    # Message de maintenance dans le salon #maintenance
    if (not("maintenance" in bot.messages) or await bot.get_messages_by_ids_in_channel(bot.messages["maintenance"], "maintenance") == None) :
        await bot.channels["maintenance"].purge()
        await bot.send(bot.channels["maintenance"], 'https://tenor.com/view/discord-gif-27684109')
        messages = await bot.send(bot.channels["maintenance"], MESSAGES["maintenance"].format(owner_mention=bot.owner.mention))
        bot.save_message("maintenance", [message.id for message in messages])

    # salon pour utiliser le bot
    for channel in bot.categories["bot"].channels :
        await channel.delete()
    
    # Gestion des rôles
    if bot.config["maintenance"] == "down" :

        # on donne le rôle "base" à tous ceux qui ne l'ont pas
        for member in [m for m in bot.guild.members if not(m.bot) and m.get_role(ROLES_IDS["base"]) is None] :
            await member.add_roles(bot.roles["base"])

        # si la fonctionnalité "règles" est utilisée, on ajoute le rôle "7tadellien" uniquement aux membres ayant accepté les règles
        if bot.channels["rules"] is not None :

            for member in [m for m in bot.guild.members if not(m.bot) and not(bot.vars["members"][f"{m.name}#{m.discriminator}"]["banned"])] :

                # si le membre a accepté les règles
                if member in bot.members_having_accepted_rules :

                    # on lui rend ses rôles en backup
                    for role_id in bot.config["rules_roles_backup"][f"{member.name}#{member.discriminator}"] :
                        if member.get_role(role_id) is None :
                            await member.add_roles(role_id)
                    bot.config["rules_roles_backup"][f"{member.name}#{member.discriminator}"] = []
                    bot.write_config()

                    # on lui rend le rôle "7tadellien"
                    if member.get_role(ROLES_IDS["7tadellien"]) is None :
                        await member.add_roles(bot.roles["7tadellien"])

                # si le membre n'a pas accepté les règles
                else :

                    # on lui retire ses rôles et on les met en backup
                    await backup_roles(bot.config["rules_roles_backup"][f"{member.name}#{member.discriminator}"], member, remove=True)
                    bot.write_config()

                    # on lui retire le rôle "7tadellien"
                    if member.get_role(ROLES_IDS["7tadellien"]) is not None :
                        await member.remove_roles(bot.roles["7tadellien"])

        # sinon on ajoute le rôle à tout le monde
        else :

            for member in [m for m in bot.guild.members if not(m.bot) and not(bot.vars["members"][f"{m.name}#{m.discriminator}"]["banned"])] :

                if member.get_role(ROLES_IDS["7tadellien"]) is None :
                    await member.add_roles(bot.roles["7tadellien"])

    else :

        for member in [m for m in bot.guild.members if not(m.bot) and not(bot.vars["members"][f"{m.name}#{m.discriminator}"]["banned"])] :
            
            await backup_roles(bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"], member, remove=True)
            bot.write_config()

            if member.get_role(ROLES_IDS["7tadellien"]) is not None :
                await member.remove_roles(bot.roles["7tadellien"])
            if member.get_role(ROLES_IDS["base"]) is not None :
                await member.remove_roles(bot.roles["base"])
            if member.get_role(ROLES_IDS["maintenance"]) is None :
                await member.add_roles(bot.roles["maintenance"])

    for member in [m for m in bot.guild.members if not(m.bot)] :
        await bot.create_command_channel_for_member(member)

    # gestion des permissions sur les salons des soirées
    await bot.update_permissions_on_event_channels()
    
    # on vérifie que les membres invités aux soirée le sont vraiment
    # (ils pourraient ne plus l'être si un rôle leur a été supprimé
    # ou le devenir si un rôle leur a été ajouté)
    for event_idstr in bot.vars["events"] :

        # pour chaque membre dans les listes, on vérifie que le membre est toujours invité
        msg = ""
        for pseudo in bot.vars["events"][event_idstr]["invited_guests"] \
                    + bot.vars["events"][event_idstr]["waiting_guests"] \
                    + bot.vars["events"][event_idstr]["present_guests"] :
            
            member = bot.get_discord_member(pseudo)
            
            # si le membre n'est pas invité
            if not(bot.member_is_invited_to_event(event_idstr, member)) :
                if pseudo in bot.vars["events"][event_idstr]["invited_guests"] :
                    bot.vars["events"][event_idstr]["invited_guests"].remove(pseudo)
                    msg += f"Changement d'état pour '{member.display_name}' : invité --> pas invité\n"
                elif pseudo in bot.vars["events"][event_idstr]["waiting_guests"] :
                    bot.vars["events"][event_idstr]["waiting_guests"].remove(pseudo)
                    msg += f"Changement d'état pour '{member.display_name}' : liste d'attente --> pas invité\n"
                    await (await bot.get_all_messages_in_channel(bot.channels[f"invitations_{event_idstr}"]))[-1].remove_reaction(chr(0x1F44D), member)
                    await bot.send(member.dm_channel, f"Tu as été retiré(e) des personnes invitées à la soirée '{bot.vars['events'][event_idstr]['name']}'.")
                elif pseudo in bot.vars["events"][event_idstr]["present_guests"] :
                    bot.vars["events"][event_idstr]["present_guests"].remove(pseudo)
                    msg += f"Changement d'état pour '{member.display_name}' : présent --> pas invité\n"
                    await (await bot.get_all_messages_in_channel(bot.channels[f"invitations_{event_idstr}"]))[-1].remove_reaction(chr(0x1F44D), member)
                    await bot.send(member.dm_channel, f"Tu as été retiré(e) des personnes invitées à la soirée '{bot.vars['events'][event_idstr]['name']}'.")
                    await bot.remove_permissions_on_channel(bot.channels[f"soirées_{event_idstr}"], member)
        
        if len(msg) > 0 :
            bot.write_json("events")
            await bot.update_waiting_list(event_idstr)
            await bot.send(bot.channels[f"logs_{event_idstr}"], msg)

        # pour chaque rôle invité, on vérifie si tous les membres ayant ce rôle sont dans les listes
        for role_id in bot.vars["events"][event_idstr]["invited_roles"] :

            role = bot.guild.get_role(role_id)

            for member in [m for m in role.members if not(m.bot)] :

                pseudo = f"{member.name}#{member.discriminator}"

                if not(pseudo in bot.vars["events"][event_idstr]["invited_guests"]
                               + bot.vars["events"][event_idstr]["waiting_guests"]
                               + bot.vars["events"][event_idstr]["present_guests"]) :
                    
                    bot.vars["events"][event_idstr]["invited_guests"].append(pseudo)
                    bot.write_json("events")
                    await bot.send(bot.channels[f"logs_{event_idstr}"], f"Changement d'état pour '{member.display_name}' : pas invité --> invité (ajout du rôle '{role.name}')")
    
    # liste de toutes les dates d'anniversaire des membres du serveur (pour petite optimisation dans clock())
    for member in bot.vars["members"] :
        m = re.match(CREATION_QUESTIONS["birthday"]["date"]["valid"], bot.vars["members"][member]["birthday"])
        if bot.vars["members"][member]["birthday"] != "0" and not(bot.vars["members"][member]["birthday"] in bot.birthday_datetimes) :
            bot.birthday_datetimes.append(f"{m.group('date')}{m.group('time')}")

    await bot.send(bot.channels["logsgamebot"], f"{bot.user.display_name} est prêt")

    clock.start()

@bot.event
async def on_message(message: discord.Message) :
    author = bot.guild.get_member(message.author.id)
    if (not(author.bot)
        and (bot.config["maintenance"] == "down" or author.get_role(ROLES_IDS["admin"]) is not None)
        and not(bot.vars["members"][f"{author.name}#{author.discriminator}"]["banned"])) :
        if bot.config['maintenance'] == "down" or message.content == "!maintenance down" :
            if message.content.startswith(bot.command_prefix) :
                if message.content[1:].split(' ')[0] in [c.name for c in bot.commands] :
                    await bot.process_commands(message)
                else :
                    await bot.send(message.channel, "Je ne connais pas cette commande")
            elif message.channel == author.dm_channel or message.channel == bot.channels[f"bot_{author.name}#{author.discriminator}"] :
                await bot.process_msg(message)
        else :
            await bot.send(message.channel, "Pas pendant une maintenance...")

@bot.event
async def on_member_join(member: discord.Member) :
    pseudo = f"{member.name}#{member.discriminator}"
    if member in bot.guild.members and not(pseudo in bot.vars["members"]) :
        await bot.add_members([pseudo])

@bot.event
async def on_member_remove(member: discord.Member) :
    pseudo = f"{member.name}#{member.discriminator}"
    if pseudo in bot.vars["members"] and not(member in bot.guild.members) :
        await bot.remove_members([(pseudo, member.id)])

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent) :
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    author = bot.guild.get_member(payload.user_id)

    if author is not None and not(author.bot) :

        # réaction au message des règles du serveur
        if "rules" in bot.messages and len(bot.messages["rules"]) > 0 and message.id == bot.messages["rules"][-1] :
            if payload.emoji.name == chr(0x1F4DD) :
                bot.members_having_accepted_rules.append(author)
                if not(bot.vars["members"][f"{author.name}#{author.discriminator}"]["banned"]) :
                    await bot.update_permissions_on_event_channels(member=author)
                    await bot.channels[f"bot_{author.name}#{author.discriminator}"].set_permissions(author, read_messages=True, send_messages=True, create_instant_invite=False)
                    await author.add_roles(bot.roles["7tadellien"])
                    for role_id in bot.config["rules_roles_backup"][f"{author.name}#{author.discriminator}"] :
                        await author.add_roles(bot.guild.get_role(role_id))
                    bot.config["rules_roles_backup"][f"{author.name}#{author.discriminator}"] = []
                    bot.write_config()
            elif payload.emoji.name != chr(0x270B) :
                await message.remove_reaction(payload.emoji, author)
            return

        # acceptation de l'invitation à une soirée
        for event_idstr in bot.vars["events"] :
            if channel == bot.channels[f"invitations_{event_idstr}"] :
                if f"{author.name}#{author.discriminator}" in bot.vars["events"][event_idstr]["invited_guests"] and payload.emoji.name == chr(0x1F44D) :
                    await bot.add_member_to_waiting_guests(event_idstr, author)
                return

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
        if "rules" in bot.messages and len(bot.messages["rules"]) > 0 and message.id == bot.messages["rules"][-1] :
            if payload.emoji.name == chr(0x1F4DD) :
                bot.members_having_accepted_rules.remove(author)
                if not(bot.vars["members"][f"{author.name}#{author.discriminator}"]["banned"]) :
                    await bot.update_permissions_on_event_channels(member=author)
                    await bot.remove_permissions_on_channel(bot.channels[f"bot_{author.name}#{author.discriminator}"], author)
                    await author.remove_roles(bot.roles["7tadellien"])
                    await backup_roles(bot.config["rules_roles_backup"][f"{author.name}#{author.discriminator}"], author, remove=True)
                    bot.write_config()
            return
        
        # annulation de la participation à une soirée
        for event_idstr in bot.vars["events"] :
            if channel == bot.channels[f"invitations_{event_idstr}"] :
                if (f"{author.name}#{author.discriminator}" != event_idstr.split(':')[0]
                    and payload.emoji.name == chr(0x1F44D)
                    and f"{author.name}#{author.discriminator}" in bot.vars["events"][event_idstr]["waiting_guests"]
                                                                 + bot.vars["events"][event_idstr]["present_guests"]) :
                    await bot.cancel_participation(event_idstr, author)
                return        
            
@bot.event
async def on_member_update(before: discord.Member, after: discord.Member) :

    roles_to_ignore = [bot.roles[role] for role in ROLES_TO_IGNORE] + [bot.guild.default_role]

    if after.roles != before.roles and not(after.bot) :
        
        # suppression de rôle
        for role in [r for r in before.roles if not(r in after.roles)] :

            if ((role.id == ROLES_IDS["base"] and bot.config["maintenance"] == "down")
                or (role.id == ROLES_IDS["maintenance"] and bot.config["maintenance"] == "up")) :
                await after.add_roles(role)

            # si le rôle était invité à une soirée, on désinvite le membre (uniquement s'il n'était invité que via ce rôle)
            if not(role.id in [
                ROLES_IDS["7tadellien"],
                ROLES_IDS["base"],
                ROLES_IDS["maintenance"]
            ]) :
                for event_idstr in bot.vars["events"] :

                    # s'il était invité mais ne l'est plus à cause de la perte de ce rôle
                    if bot.member_is_invited_to_event(event_idstr, before) and not(bot.member_is_invited_to_event(event_idstr, after)) :
                        pseudo = f"{after.name}#{after.discriminator}"
                        if pseudo in bot.vars["events"][event_idstr]["invited_guests"] :
                            bot.vars["events"][event_idstr]["invited_guests"].remove(pseudo)
                            msg = f"Changement d'état pour '{after.display_name}' : invité --> pas invité (suppression du rôle '{role.name}')"
                        elif pseudo in bot.vars["events"][event_idstr]["waiting_guests"] :
                            bot.vars["events"][event_idstr]["waiting_guests"].remove(pseudo)
                            msg = f"Changement d'état pour '{after.display_name}' : liste d'attente --> pas invité (suppression du rôle '{role.name}')"
                            await (await bot.get_all_messages_in_channel(bot.channels[f"invitations_{event_idstr}"]))[-1].remove_reaction(chr(0x1F44D), after)
                            await bot.send(after.dm_channel, f"Tu as été retiré(e) des personnes invitées à la soirée '{bot.vars['events'][event_idstr]['name']}' car tu n'as plus le rôle '{role.name}'.")
                        elif pseudo in bot.vars["events"][event_idstr]["present_guests"] :
                            bot.vars["events"][event_idstr]["present_guests"].remove(pseudo)
                            msg = f"Changement d'état pour '{after.display_name}' : présent --> pas invité (suppression du rôle '{role.name}')"
                            await (await bot.get_all_messages_in_channel(bot.channels[f"invitations_{event_idstr}"]))[-1].remove_reaction(chr(0x1F44D), after)
                            await bot.send(after.dm_channel, f"Tu as été retiré(e) des personnes invitées à la soirée '{bot.vars['events'][event_idstr]['name']}' car tu n'as plus le rôle '{role.name}'.")
                            await bot.remove_permissions_on_channel(bot.channels[f"soirées_{event_idstr}"], after)
                        bot.write_json("events")

                        if len(msg) > 0 :
                            await bot.send(bot.channels[f"logs_{event_idstr}"], msg)
                            await bot.update_waiting_list(event_idstr)

        # ajout de rôle
        for role in [r for r in after.roles if not(r in before.roles)] :

            # si le membre est "banned", on ajoute l'id du rôle à la backup et on supprime le rôle
            if bot.vars["members"][f"{after.name}#{after.discriminator}"]["banned"] :
                if not(role.id in bot.config["ban_roles_backup"][f"{after.name}#{after.discriminator}"]) :
                    bot.config["ban_roles_backup"][f"{after.name}#{after.discriminator}"].append(role.id)
                    bot.write_config()
                await after.remove_roles(role)

            # si le serveur est en maintenance, on ajoute l'id du rôle à la backup et on supprime le rôle
            elif bot.config["maintenance"] == "up" and not(role in roles_to_ignore) :
                if not(role.id in bot.config["maintenance_roles_backup"][f"{after.name}#{after.discriminator}"]) :
                    bot.config["maintenance_roles_backup"][f"{after.name}#{after.discriminator}"].append(role.id)
                    bot.write_config()
                await after.remove_roles(role)

            # si le membre n'a pas accepté les règles, on ajoute l'id du rôle à la backup et on supprime le rôle
            elif bot.channels["rules"] is not None and not(after in bot.members_having_accepted_rules) and not(role in roles_to_ignore) :
                if not(role.id in bot.config["rules_roles_backup"][f"{after.name}#{after.discriminator}"]) :
                    bot.config["rules_roles_backup"][f"{after.name}#{after.discriminator}"].append(role.id)
                    bot.write_config()
                await after.remove_roles(role)

            # si le rôle est invité à une soirée, on invite le membre
            for event_idstr in bot.vars["events"] :
                if not(bot.member_is_invited_to_event(event_idstr, before)) and bot.member_is_invited_to_event(event_idstr, after) :
                    pseudo = f"{after.name}#{after.discriminator}"
                    bot.vars["events"][event_idstr]["invited_guests"].append(pseudo)
                    bot.write_json("events")
                    await bot.send(bot.channels[f"logs_{event_idstr}"], f"Changement d'état pour '{after.display_name}' : pas invité --> invité (ajout du rôle '{role.name}')")

        bot.write_json("members")

