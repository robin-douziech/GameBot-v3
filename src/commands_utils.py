from commands_event import *

@bot.command(name="ban")
@bot.admin_command
@bot.private_command
async def ban_gamebot(ctx: commands.Context, *args, **kwargs) :

    if len(args) > 0 :

        target = " ".join(args)

        for pseudo in bot.vars["members"] :

            member = bot.get_discord_member(pseudo)

            if ((re.match(r"^(\d+)$", args[0]) and int(args[0]) == member.id)
                or (target == member.display_name and len([m.display_name for m in bot.guild.members if m.display_name == target]) == 1)) :

                if member.get_role(ROLES_IDS["admin"]) is None and not(bot.vars["members"][pseudo]["banned"]) :

                    # on pass "banned" à True
                    bot.vars["members"][pseudo]["banned"] = True

                    # on lui retire le rôle "7tadellien"
                    if member.get_role(ROLES_IDS["7tadellien"]) is not None :
                        await member.remove_roles(bot.roles["7tadellien"])

                    # on lui retire ses rôles et on les met en backup
                    await backup_roles(bot.config["ban_roles_backup"][pseudo], member, remove=True)

                    # on lui retire l'accès aux salon des soirées auxquelles il est invitées
                    await bot.update_permissions_on_event_channels(member=member)

                    # on lui retire l'accès à son salon privé avec le bot
                    await bot.remove_permissions_on_channel(bot.channels[f"bot_{pseudo}"], member)

                    bot.write_json("members")
                    bot.write_config()

                    await bot.send(ctx.channel, f"{member.display_name} est maintenant banni")

                return
            
@bot.command(name="banned")
@bot.admin_command
@bot.private_command
async def banned_gamebot(ctx: commands.Context):
    await bot.send(ctx.channel, "Voici les membres actuellement bannis du serveur :\n- " + "\n- ".join([str(member.display_name) for member in [m for m in bot.guild.members if not(m.bot) and bot.vars["members"][f"{m.name}#{m.discriminator}"]["banned"]]]))

@bot.command(name="birthday")
@bot.private_command
async def birthday_gamebot(ctx: commands.Context, *args, **kwargs) :
    author = bot.guild.get_member(ctx.author.id)
    if len(bot.vars["members"][f"{author.name}#{author.discriminator}"]["questions"]) == 0 :
        question_type = "birthday"
        bot.vars["members"][f"{author.name}#{author.discriminator}"]["questions"] = ["", *list(CREATION_QUESTIONS[question_type].keys())]
        bot.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"] = question_type
        bot.write_json("members")
        await bot.send_next_question(ctx.channel, author)
    else:
        await bot.send(ctx.channel, "Tu as déjà une autre commande en cours")

@bot.command(name="help")
@bot.private_command
async def help_gamebot(ctx: commands.Context, *args, **kwargs) :
    author = bot.guild.get_member(ctx.author.id)
    if len(args) > 0 :
        await bot.send(ctx.channel, HELP_MESSAGES[" ".join(args)])
    else :
        help_message = "Voici la liste des commandes que tu peux utiliser :\n\n"
        help_message += "- !birthday : sert à informer le bot de ta date d'anniversaire pour qu'il te le souhaites\n"
        help_message += "- !event : sert à organiser des soirées\n"
        help_message += "- !invite : sert à inviter des membres du serveur à l'une de test soirées\n"
        help_message += "- !uninvite : sert à annuler une invitation à une soirée\n"
        if author.get_role(ROLES_IDS["admin"]) is not None :
            help_message += "- !logs : afficher les logs du bot\n"
            help_message += "- !maintenance : entrer ou sortir du mode maintenance du serveur\n"
            help_message += "- !kill : éteindre le bot\n"
        help_message += "\nSi tu veux plus de détails sur l'utilisation d'une commande, utilise \"!help __commande__\""
        await bot.send(ctx.channel, help_message)

@bot.command(name="kill")
@bot.admin_command
@bot.private_command
async def kill_gamebot(ctx: commands.Context, *args, **kwargs) :
    bot.log("Bot killed by the !kill command", 'warning')
    sys.exit(0)

@bot.command(name="logs")
@bot.admin_command
@bot.private_command
async def logs_gamebot(ctx: commands.Context, nb_lines: int = 10, *args, **kwargs) :
    author = bot.guild.get_member(ctx.author.id)
    (day, month, year) = bot.get_current_datetime()[:3]
    try :
        with open(f"logs/20{year}/{month}/{day}.log", "rt") as f :
            msg = f.read().split("\n")
            if len(msg) > nb_lines :
                msg = msg[-int(nb_lines):]
            txt = "\n".join(msg) + "\n"
            await bot.send(ctx.channel, txt, wrappers=('```', '```'))
    except Exception as e :
        bot.log(f"An exception occured while reading logs: {e}", 'error')

@bot.command(name="maintenance")
@bot.admin_command
@bot.private_command
async def maintenance_gamebot(ctx: commands.Context, *args, **kwargs) :
    if len(args) > 0 :

        if args[0] == "up" and bot.config["maintenance"] == "down" :

            bot.config["maintenance"] = "up"

            # variable pour garder une trace des roles de chaque membre (pour les restituer à la fin de la maintenance)
            bot.config["maintenance_roles_backup"] = {f"{member.name}#{member.discriminator}": [] for member in [m for m in bot.guild.members if not(m.bot)]}

            for member in [m for m in bot.guild.members if not(m.bot)] :

                # on retire les permissions sur son salon privé avec le bot
                await bot.remove_permissions_on_channel(bot.channels[f"bot_{member.name}#{member.discriminator}"], member)

                # on garde une trace des roles du membre et on les retire
                await backup_roles(bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"], member, remove=True)

                await member.remove_roles(bot.roles["7tadellien"])
                await member.remove_roles(bot.roles["base"])
                await member.add_roles(bot.roles["maintenance"])

            # on supprime les permissions sur les salon des soirées
            await bot.update_permissions_on_event_channels()

            bot.write_config()

            await bot.send(ctx.channel, ":information: Le serveur est entré en maintenance")

        elif args[0] == "down" and bot.config["maintenance"] == "up" :

            bot.config["maintenance"] = "down"

            for member in [m for m in bot.guild.members if not(m.bot)] :

                # on rend les permissions sur son salon privé avec le bot
                overwrite = copy.deepcopy(bot.overwrites_none)
                overwrite.update(
                    read_messages=True,
                    send_messages=True,
                    mention_everyone=True,
                    read_message_history=True
                )
                await bot.channels[f"bot_{member.name}#{member.discriminator}"].set_permissions(member, overwrite=overwrite)

                await member.remove_roles(bot.roles["maintenance"])
                await member.add_roles(bot.roles["base"])

            # on rend les permissions sur les salon des soirées
            await bot.update_permissions_on_event_channels()

            # si la fonctionnalité "règles" est utilisée, on ajoute le rôle "7tadellien" uniquement aux membres ayant accepté les règles
            if bot.channels["règles"] is not None :

                for member in bot.members_having_accepted_rules :

                    await member.add_roles(bot.roles["7tadellien"])

                    # on restitue les rôles du membre
                    for role_id in bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"] :
                        await member.add_roles(bot.guild.get_role(role_id))
                    bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"] = []

            # sinon on ajoute le rôle à tout le monde
            else :

                for member in [m for m in bot.guild.members if not(m.bot)] :

                    if member.get_role(ROLES_IDS["7tadellien"]) is None :
                        await member.add_roles(bot.roles["7tadellien"])

                    # on restitue les rôles du membre
                    for role_id in bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"] :
                        await member.add_roles(bot.guild.get_role(role_id))
                    bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"] = []

            bot.write_config()
            
            await bot.send(ctx.channel, ":information: Le serveur est sorti de maintenance")

@bot.command(name="unban")
@bot.admin_command
@bot.private_command
async def unban_gamebot(ctx: commands.Context, *args, **kwargs) :
        
        if len(args) > 0 :

            target = " ".join(args)

            for pseudo in bot.vars["members"] :

                member = bot.get_discord_member(pseudo)

                if ((re.match(r"^(\d+)$", args[0]) and int(args[0]) == member.id)
                    or (target == member.display_name and len([m.display_name for m in bot.guild.members if m.display_name == target]) == 1)) :

                    if bot.vars["members"][pseudo]["banned"] :

                        # on passe "banned" à False
                        bot.vars["members"][pseudo]["banned"] = False

                        if bot.config["maintenance"] == "down" :

                            # on donne le rôle "base" s'il ne l'a pas
                            if member.get_role(ROLES_IDS["base"]) is None :
                                await member.add_roles(bot.roles["base"])

                            # on restitue le rôle "7tadellien"
                            if member.get_role(ROLES_IDS["7tadellien"]) is None and (bot.channels["règles"] is None or member in bot.members_having_accepted_rules) :
                                await member.add_roles(bot.roles["7tadellien"])

                            # on retire le rôle "maintenance" s'il l'a
                            if member.get_role(ROLES_IDS["maintenance"]) is not None :
                                await member.remove_roles(bot.roles["maintenance"])

                            # on donne l'accès au salon privé avec le bot (s'il a accepté les règles)
                            if (bot.channels["règles"] is None or member in bot.members_having_accepted_rules) :
                                overwrite = copy.deepcopy(bot.overwrites_none)
                                overwrite.update(
                                    read_messages=True,
                                    send_messages=True,
                                    mention_everyone=True,
                                    read_message_history=True
                                )
                                await bot.channels[f"bot_{pseudo}"].set_permissions(member, overwrite=overwrite)

                        else :

                            # on retire le rôle "base" s'il l'a
                            if member.get_role(ROLES_IDS["base"]) is not None :
                                await member.remove_roles(bot.roles["base"])

                            # on retire le rôle "7tadellien" s'il l'a
                            if member.get_role(ROLES_IDS["7tadellien"]) is not None :
                                await member.remove(bot.roles["7tadellien"])

                            # on donne le rôle "maintenance" s'il ne l'a pas
                            if member.get_role(ROLES_IDS["maintenance"]) is None :
                                await member.add_roles(bot.roles["maintenance"])

                            # on retire l'accès au salon privé avec le bot
                            await bot.remove_permissions_on_channel(bot.channels[f"bot_{pseudo}"], member)

                        # on restitue les rôles en backup
                        for role_id in bot.config["ban_roles_backup"][pseudo] :
                            await member.add_roles(bot.guild.get_role(role_id))
                        bot.config["ban_roles_backup"][pseudo] = []

                        # on lui redonne accès aux salon des soirées auxquelles il est invité
                        await bot.update_permissions_on_event_channels(member=member)

                        bot.write_json("members")
                        bot.write_config()

                        await bot.send(ctx.channel, f"{member.display_name} n'est plus banni")

                    return
                
@bot.command(name="clean")
@bot.private_command
@bot.admin_command
async def clean_gamebot(ctx: commands.Context) :

    if os.getenv("ENV") == "TEST" :

        bot.vars["members"] = {}
        bot.vars["events"] = {}
        bot.config["ban_roles_backup"] = {}
        bot.config["maintenance_roles_backup"] = {}
        bot.config["rules_roles_backup"] = {}

        bot.write_json("members")
        bot.write_json("events")
        bot.write_config()

        for channel in bot.guild.channels :
            await channel.delete()

        for category in bot.guild.categories :

            for channel in category.channels :
                await channel.delete()

            await category.delete()

        for role in [r for r in bot.guild.roles if r.id != 1288223534627160220 and r != bot.guild.default_role] :
            await role.delete()