from bot_events import *

@bot.command(name="event")
@bot.private_command
async def event_gamebot(ctx: commands.Context, *args, **kwargs) :

    author = bot.guild.get_member(ctx.author.id)

    if len(args) > 0 :

        match args[0] :

            case 'create' :
                
                if not(bot.vars["members"][f"{author.name}#{author.discriminator}"]["questionned"]) :
                    
                    # calcul de l'identifiant de la soirée
                    event_id = 1
                    while f"{author.name}#{author.discriminator}:{event_id}" in bot.vars["events"] :
                        event_id += 1
                    event_idstr = f"{author.name}#{author.discriminator}:{event_id}"

                    # ajout de l'event dans bot.vars['events']
                    bot.vars["events"][event_idstr] = BOT_VARS_DEFAULTS["events"].copy()
                    bot.vars["events"][event_idstr]["invited_guests"] = []
                    bot.vars["events"][event_idstr]["waiting_guests"] = []
                    bot.vars["events"][event_idstr]["present_guests"] = []
                    bot.vars["events"][event_idstr]["present_guests"].append(f"{author.name}#{author.discriminator}")

                    # création des salons
                    for string in ["invitations", "soirées", "logs"] :
                        channel = await bot.guild.create_text_channel(event_idstr, category=bot.categories[string])
                        await channel.set_permissions(author, **EVENT_CHANNEL_PERMISSIONS[string])
                        for member in [m for m in bot.guild.members if not(m.bot) and m != author] :
                            await channel.set_permissions(member, read_messages=False)
                        bot.channels[f"{string}_{event_idstr}"] = channel
                        bot.vars["events"][event_idstr][f"{string}_channel_id"] = channel.id
                    bot.write_json("events")

                    bot.vars["members"][f"{author.name}#{author.discriminator}"]['questionned'] = "event"
                    bot.vars["members"][f"{author.name}#{author.discriminator}"]['questions'] = ["", *list(CREATION_QUESTIONS["event"].keys())]
                    bot.vars["members"][f"{author.name}#{author.discriminator}"]['object_id'] = event_id
                    bot.write_json("members")

                    await bot.send_next_question(ctx.channel, author)

                else :
                    await bot.send(ctx.channel, "Tu as déjà une autre commande en cours")

            case 'read' :
                if len(args) > 1 :
                    if f"{author.name}#{author.discriminator}:{args[1]}" in bot.vars["events"] :
                        event_idstr = f"{author.name}#{author.discriminator}:{args[1]}"
                        infos = '\n'.join([f"{var_name}: {bot.vars['events'][event_idstr][var_name]}" for var_name in bot.vars["events"][event_idstr] if var_name != "created" and not(var_name.endswith('channel_id'))])
                        await bot.send(ctx.channel, f"Voici toutes les informations de la soirée ayant l'identifiant \"{args[1]}\" :\n{infos}")
                    else :
                        await bot.send(ctx.channel, f"Aucune de tes soirées ne possède l'identifiant \"{args[1]}\"")
                else :
                    if f"{author.name}#{author.discriminator}" in [id.split(':')[0] for id in bot.vars["events"]] :
                        await bot.send(ctx.channel, "Voici la liste des événements que tu as créé avec leur identifiant respectif :\n- "+"\n- ".join([f"{event_idstr.split(':')[1]} : {bot.vars['events'][event_idstr]['name']}" for event_idstr in [id for id in bot.vars['events'] if id.split(':')[0] == f"{author.name}#{author.discriminator}"]]))
                    else :
                        await bot.send(ctx.channel, "Tu n'as auctuellement aucune soirée de créée. Tu peux en créer une grâce à la commande \"!event create\".")

            case 'delete' :
                if len(args) > 1 :
                    if f"{author.name}#{author.discriminator}:{args[1]}" in bot.vars["events"] :
                        try :
                            await bot.delete_event(f"{author.name}#{author.discriminator}:{args[1]}")
                            await bot.send(ctx.channel, "La soirée a bien été supprimée")
                        except Exception as e :
                            await bot.send(ctx.channel, "Quelque chose s'est mal passé pendant la suppression de la soirée.")
                            raise Exception(e)
                    else :
                        await bot.send(ctx.channel, f"Aucune de tes soirées ne possède l'identifiant \"{args[1]}\"")
                else :
                    await bot.send(ctx.channel, "Mauvaise utilisation de la commande. Utilise \"!help event delete\" pour plus de détails")

            case _ :
                await bot.send(ctx.channel, f"Mauvaise utilisation de la commande. Utilise \"!help event\" pour savoir comment utiliser cette commande")

    else :
        await bot.send(ctx.channel, f"Mauvaise utilisation de la commande. Utilise \"!help event\" pour savoir comment utiliser cette commande")

@bot.command(name="invite")
@bot.private_command
async def invite_gamebot(ctx: commands.Context, *args, **kwargs) :
    
    author = bot.guild.get_member(ctx.author.id)

    if len(args) > 1 :

        event_idstr = f"{author.name}#{author.discriminator}:{args[0]}"
        
        if event_idstr in bot.vars["events"] and bot.vars["events"][event_idstr]["created"] :

            for pseudo in bot.vars["members"] :
                member = bot.get_discord_member(pseudo)
                if (args[1] == member.mention
                    or (re.match(r"^(\d+)$", args[1]) and int(args[1]) == member.id)
                    or (args[1] == member.display_name and len([m.display_name for m in bot.guild.members if m.display_name == args[1]]) == 1)) :
                    if not(pseudo in bot.vars["events"][event_idstr]["invited_guests"]
                                   + bot.vars["events"][event_idstr]["waiting_guests"]
                                   + bot.vars["events"][event_idstr]["present_guests"]) :
                        try :
                            await bot.invite_member(event_idstr, bot.get_discord_member(pseudo))
                            await bot.send(ctx.channel, f"Invitation à la soirée '{bot.vars['events'][event_idstr]['name']}' envoyée à {bot.get_discord_member(pseudo).display_name}")
                        except Exception as e :
                            await bot.send(ctx.channel, f"Quelque chose s'est mal passé pendant l'invitation de {bot.get_discord_member(pseudo).display_name}")
                    return

            for role in bot.guild.roles :
                if args[1] == role.mention :
                    for member in [m for m in role.members if not(m.bot)] :
                        pseudo = f"{member.name}#{member.discriminator}"
                        if not(pseudo in bot.vars["events"][event_idstr]["invited_guests"]
                                       + bot.vars["events"][event_idstr]["waiting_guests"]
                                       + bot.vars["events"][event_idstr]["waiting_guests"]) :
                            try :
                                await bot.invite_member(event_idstr, member)
                                await bot.send(ctx.channel, f"Invitation à la soirée '{bot.vars['events'][event_idstr]['name']}' envoyée à {member.display_name}")
                            except Exception as e :
                                await bot.send(ctx.channel, f"Quelque chose s'est mal passé pendant l'invitation de {member.display_name}")
                    return
                
            await bot.send(ctx.channel, f"Mauvaise utilisation de la commande. Utilise \"!help invite\" pour savoir comment utiliser cette commande")

        else :
            await bot.send(ctx.channel, f"Aucune de tes soirées ne possède l'identifiant \"{args[0]}\"")

    else :
        await bot.send(ctx.channel, f"Mauvaise utilisation de la commande. Utilise \"!help invite\" pour savoir comment utiliser cette commande")