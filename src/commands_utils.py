from commands_event import *

@bot.command(name="birthday")
@bot.dm_command
async def birthday_gamebot(ctx: commands.Context, *args, **kwargs) :
    author = bot.guild.get_member(ctx.author.id)
    if len(bot.vars["members"][f"{author.name}#{author.discriminator}"]["questions"]) == 0 :
        question_type = "birthday"
        bot.vars["members"][f"{author.name}#{author.discriminator}"]["questions"] = ["", *list(CREATION_QUESTIONS[question_type].keys())]
        bot.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"] = question_type
        bot.write_json("members")
        await bot.send_next_question(author)
    else:
        await bot.send(author.dm_channel, "Tu as déjà une autre commande en cours")

@bot.command(name="kill")
@bot.admin_command
@bot.dm_command
async def kill_gamebot(ctx: commands.Context, *args, **kwargs) :
    bot.log("Bot killed by the !kill command", 'warning')
    sys.exit(0)

@bot.command(name="logs")
@bot.admin_command
@bot.dm_command
async def logs_gamebot(ctx: commands.Context, nb_lines: int = 10, *args, **kwargs) :
    author = bot.guild.get_member(ctx.author.id)
    (day, month, year) = bot.get_current_datetime()[:3]
    try :
        with open(f"logs/20{year}/{month}/{day}.log", "rt") as f :
            msg = f.read().split("\n")
            if len(msg) > nb_lines :
                msg = msg[-int(nb_lines):]
            txt = "\n".join(msg) + "\n"
            await bot.send(author.dm_channel, txt, wrappers=('```', '```'))
    except Exception as e :
        bot.log(f"An exception occured while reading logs: {e}", 'error')

@bot.command(name="maintenance")
@bot.admin_command
@bot.dm_command
async def maintenance_gamebot(ctx: commands.Context, *args, **kwargs) :
    if len(args) > 0 :

        if args[0] == "up" and bot.config["maintenance"] == "down" :

            # variable pour garder une trace des roles de chaque membre (pour les restituer à la fin de la maintenance)
            bot.config["maintenance_roles_backup"] = {}

            for member in [m for m in bot.guild.members if not(m.bot)] :

                # on garde une trace des roles du membre et on les retire
                bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"] = await backup_roles(member, remove=True)

                await member.remove_roles(bot.roles["7tadellien(ne)"])
                await member.remove_roles(bot.roles["base"])
                await member.add_roles(bot.roles["maintenance"])

            # si tout s'est bien passé, on passe "maintenance" à "up" et on sauvegarde
            bot.config["maintenance"] = "up"
            bot.write_config()

        elif args[0] == "down" and bot.config["maintenance"] == "up" :

            for member in [m for m in bot.guild.members if not(m.bot)] :

                # on restitue les rôles du membre
                for role_id in bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"] :
                    await member.add_roles(bot.guild.get_role(role_id))
                bot.config["maintenance_roles_backup"][f"{member.name}#{member.discriminator}"] = []
                bot.write_config()

                await member.remove_roles(bot.roles["maintenance"])
                await member.add_roles(bot.roles["base"])

            # si la fonctionnalité "règles" est utilisée, on ajoute le rôle "7tadellien(ne)" uniquement aux membres ayant accepté les règles
            if bot.channels["rules"] is not None :
                message = (await bot.get_messages_by_ids_in_channel(bot.messages["rules"][-1:], bot.channels["rules"]))[-1]
                reaction = [r for r in message.reactions if r.emoji == chr(0x1F4DD)][0]
                async for member in reaction.users() :
                    await member.add_roles(bot.roles["7tadellien(ne)"])
            # sinon on ajoute le rôle à tout le monde
            else :
                for member in [m for m in bot.guild.members if not(m.bot) and m.get_role(ROLES_IDS["7tadellien(ne)"]) is None] :
                    await member.add_roles(bot.roles["7tadellien(ne)"])

            # si tout s'est bien passé, on passe "maintenance" à "down" et on sauvegarde
            bot.config["maintenance"] = "down"
            bot.write_config()

