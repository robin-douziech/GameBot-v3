from commands_event import *

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
            bot.config["maintenance_roles_backup"] = {}

            for member in [m for m in bot.guild.members if not(m.bot)] :

                # on retire les permissions sur son salon privé avec le bot
                await bot.channels[f"bot_{member.name}#{member.discriminator}"].set_permissions(member, read_messages=False, send_messages=False, create_instant_invite=False)

                # on garde une trace des roles du membre et on les retire
                bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"] = await backup_roles(member, remove=True)

                await member.remove_roles(bot.roles["7tadellien(ne)"])
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
                await bot.channels[f"bot_{member.name}#{member.discriminator}"].set_permissions(member, read_messages=True, send_messages=True, create_instant_invite=False)

                await member.remove_roles(bot.roles["maintenance"])
                await member.add_roles(bot.roles["base"])

            # on rend les permissions sur les salon des soirées
            await bot.update_permissions_on_event_channels()

            # si la fonctionnalité "règles" est utilisée, on ajoute le rôle "7tadellien(ne)" uniquement aux membres ayant accepté les règles
            if bot.channels["rules"] is not None :

                async for member in bot.rules_reaction.users() :

                    if not(member.bot) :

                        await member.add_roles(bot.roles["7tadellien(ne)"])

                        # on restitue les rôles du membre
                        for role_id in bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"] :
                            await member.add_roles(bot.guild.get_role(role_id))
                        bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"] = []
                    bot.write_config()

            # sinon on ajoute le rôle à tout le monde
            else :
                for member in [m for m in bot.guild.members if not(m.bot) and m.get_role(ROLES_IDS["7tadellien(ne)"]) is None] :

                    await member.add_roles(bot.roles["7tadellien(ne)"])

                    # on restitue les rôles du membre
                    for role_id in bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"] :
                        await member.add_roles(bot.guild.get_role(role_id))
                    bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"] = []
                bot.write_config()

            bot.write_config()
            await bot.send(ctx.channel, ":information: Le serveur est sorti de maintenance")

