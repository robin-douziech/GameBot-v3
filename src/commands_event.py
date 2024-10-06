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

                    await bot.send_next_question(author)

                else :
                    await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], "Tu as déjà une autre commande en cours")

            case 'read' :
                if len(args) > 1 :
                    if f"{author.name}#{author.discriminator}:{args[1]}" in bot.vars["events"] :
                        event_idstr = f"{author.name}#{author.discriminator}:{args[1]}"
                        infos = '\n'.join([f"{var_name}: {bot.vars['events'][event_idstr][var_name]}" for var_name in bot.vars["events"][event_idstr] if var_name != "created" and not(var_name.endswith('channel_id'))])
                        await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], f"Voici toutes les informations de la soirée ayant l'identifiant \"{args[1]}\" :\n{infos}")
                    else :
                        await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], f"Aucune de tes soirées ne possède l'identifiant \"{args[1]}\"")
                else :
                    if f"{author.name}#{author.discriminator}" in [id.split(':')[0] for id in bot.vars["events"]] :
                        await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], "Voici la liste des événements que tu as créé avec leur identifiant respectif :\n- "+"\n- ".join([f"{event_idstr.split(':')[1]} : {bot.vars['events'][event_idstr]['name']}" for event_idstr in [id for id in bot.vars['events'] if id.split(':')[0] == f"{author.name}#{author.discriminator}"]]))
                    else :
                        await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], "Tu n'as auctuellement aucune soirée de créée. Tu peux en créer une grâce à la commande \"!event create\".")

            case 'delete' :
                if len(args) > 1 :
                    if f"{author.name}#{author.discriminator}:{args[1]}" in bot.vars["events"] :
                        try :
                            await bot.delete_event(f"{author.name}#{author.discriminator}:{args[1]}")
                            await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], "La soirée a bien été supprimée")
                        except Exception as e :
                            await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], "Quelque chose s'est mal passé pendant la suppression de la soirée.")
                            raise Exception(e)
                    else :
                        await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], f"Aucune de tes soirées ne possède l'identifiant \"{args[1]}\"")
                else :
                    await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], "Mauvaise utilisation de la commande. Utilise \"!help event delete\" pour plus de détails")

            case _ :
                await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], f"Mauvaise utilisation de la commande. Utilise \"!help event\" pour savoir comment utiliser cette commande")

    else :
        await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], f"Mauvaise utilisation de la commande. Utilise \"!help event\" pour savoir comment utiliser cette commande")

@bot.command(name="invite")
@bot.private_command
async def invite_gamebot(ctx: commands.Context, *args, **kwargs) :
    
    author = bot.guild.get_member(ctx.author.id)

    if len(args) > 1 :
        
        if f"{author.name}#{author.discriminator}:{args[0]}" in bot.vars["events"] and bot.vars["events"][f"{author.name}#{author.discriminator}:{args[0]}"]["created"] :

            event_idstr = f"{author.name}#{author.discriminator}:{args[0]}"

            if args[1].startswith('@') :
                pass

            elif args[1] in bot.vars["members"] :
                if not(args[1] in bot.vars["events"][event_idstr]["invited_guests"]
                                + bot.vars["events"][event_idstr]["waiting_guests"]
                                + bot.vars["events"][event_idstr]["present_guests"]) :
                    try :
                        await bot.invite_member(event_idstr, bot.get_discord_member(args[1]))
                        await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], f"Invitation à la soirée '{bot.vars['events'][event_idstr]['name']}' envoyée à {bot.get_discord_member(args[1]).display_name}")
                    except Exception as e :
                        await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], f"Quelque chose s'est mal passé pendant l'invitation de {bot.get_discord_member(args[1]).display_name}")
            else :
                await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], f"Mauvaise utilisation de la commande. Utilise \"!help invite\" pour savoir comment utiliser cette commande")

        else :
            await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], f"Aucune de tes soirées ne possède l'identifiant \"{args[0]}\"")

    else :
        await bot.send(bot.channels[f"bot_{author.name}#{author.discriminator}"], f"Mauvaise utilisation de la commande. Utilise \"!help invite\" pour savoir comment utiliser cette commande")