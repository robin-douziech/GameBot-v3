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
                    bot.vars["events"][event_idstr]["invited_members"] = []
                    bot.vars["events"][event_idstr]["invited_roles"] = []
                    bot.vars["events"][event_idstr]["present_guests"].append(f"{author.name}#{author.discriminator}")
                    bot.vars["events"][event_idstr]["invited_members"].append(author.id)

                    # création des salons
                    for string in ["invitations", "soirées", "logs"] :
                        overwrites = copy.deepcopy(bot.overwrites_none)
                        overwrites.update(**EVENT_CHANNEL_PERMISSIONS[string])
                        channel = await bot.guild.create_text_channel(event_idstr, category=bot.categories[string], overwrites={
                            author: overwrites,
                            bot.guild.default_role: bot.overwrites_none
                        })
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
                        
                        
                        infos = '\n'.join([f"{var_name}: {bot.vars['events'][event_idstr][var_name]}" for var_name in bot.vars["events"][event_idstr]
                                           if var_name != "created" and not(var_name.endswith('channel_id')) and not(isinstance(bot.vars['events'][event_idstr][var_name], list))])
                        
                        infos += f"\n\n__Membres invités n'ayant pas encore accepté l'invitation__ :\n- " + '\n- '.join(bot.vars['events'][event_idstr]['invited_guests']) + "\n\n"
                        infos += f"__Membres invités dans la liste d'attente (car plus de place)__ :\n- " + '\n- '.join(bot.vars['events'][event_idstr]['waiting_guests']) + "\n\n"
                        infos += f"__Membres présents à la soirée____ :\n- " + '\n- '.join(bot.vars['events'][event_idstr]['present_guests'])
                        
                        await bot.send(ctx.channel, f"Voici toutes les informations de la soirée ayant l'identifiant \"{args[1]}\" :\n{infos}")
                    else :
                        await bot.send(ctx.channel, f"Aucune de tes soirées ne possède l'identifiant \"{args[1]}\"")
                else :
                    if f"{author.name}#{author.discriminator}" in [id.split(':')[0] for id in bot.vars["events"]] :
                        await bot.send(ctx.channel, "Voici la liste des événements que tu as créé avec leur identifiant respectif :\n- "+"\n- ".join([f"{event_idstr.split(':')[1]} : {bot.vars['events'][event_idstr]['name']}" for event_idstr in [id for id in bot.vars['events'] if id.split(':')[0] == f"{author.name}#{author.discriminator}"]]))
                    else :
                        await bot.send(ctx.channel, "Tu n'as auctuellement aucune soirée de créée. Tu peux en créer une grâce à la commande \"!event create\".")

            case 'update' :
                if len(args) > 3 and f"{author.name}#{author.discriminator}:{args[1]}" in bot.vars["events"]  :
                    event_idstr = f"{author.name}#{author.discriminator}:{args[1]}"
                    match args[2] :
                        case 'nb_max_guests':
                            pattern_match = re.match(r"^(\d+)$", args[3])
                            if pattern_match :
                                if int(args[3]) >= len(bot.vars["events"][event_idstr]["present_guests"]) :
                                    bot.vars["events"][event_idstr]['nb_max_guests'] = args[3]
                                    bot.write_json("events")
                                    await bot.update_waiting_list(event_idstr)
                                else :
                                    await bot.send(ctx.channel, "Tu ne peux pas réduire autant le nombre maximum d'invités à cette soirée car il y a déjà plus de membres présents que ça")
                            else :
                                await bot.send(ctx.channel, "Mauvaise utilisation de la commande. Utilise \"!help event update\" pour plus de détails")
                        case _ :
                            await bot.send(ctx.channel, "Mauvaise utilisation de la commande. Utilise \"!help event update\" pour plus de détails")
                else :
                    await bot.send(ctx.channel, "Mauvaise utilisation de la commande. Utilise \"!help event update\" pour plus de détails")
            
            case 'delete' :
                if len(args) > 1 :
                    if f"{author.name}#{author.discriminator}:{args[1]}" in bot.vars["events"] :
                        try :
                            await bot.delete_event(f"{author.name}#{author.discriminator}:{args[1]}")
                            await bot.send(ctx.channel, "La soirée a bien été supprimée")
                        except Exception as e :
                            await bot.send(ctx.channel, "Quelque chose s'est mal passé pendant la suppression de la soirée.")
                            raise Exception(e)
                    elif author.get_role(ROLES_IDS["admin"]) and args[1] in bot.vars["events"] :
                        try :
                            await bot.delete_event(args[1])
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
        target = " ".join(args[1:])
        
        if event_idstr in bot.vars["events"] and bot.vars["events"][event_idstr]["created"] :

            # inviter un membre
            for pseudo in bot.vars["members"] :
                member = bot.get_discord_member(pseudo)
                if ((re.match(r"^(\d+)$", args[1]) and int(args[1]) == member.id)
                    or (target == member.display_name and len([m.display_name for m in bot.guild.members if m.display_name == target]) == 1)) :
                    if not(member.id in bot.vars["events"][event_idstr]["invited_members"]) :
                        try :
                            await bot.invite_member(event_idstr, member)
                            await bot.send(ctx.channel, f"Invitation à la soirée {bot.vars['events'][event_idstr]['name']} envoyée à {member.display_name}")
                        except Exception as e :
                            await bot.send(ctx.channel, f"Quelque chose s'est mal passé pendant l'invitation de {member.display_name}")
                            raise Exception(e)
                    return

            # inviter un rôle
            for role in bot.guild.roles :
                if ((re.match(r"^(\d+)$", args[1]) and int(args[1]) == role.id)
                    or (target == role.name and len([r.name for r in bot.guild.roles if r.name == target]) == 1)) :
                    if not(role.id in bot.vars["events"][event_idstr]["invited_roles"]) :
                        try :
                            await bot.invite_role(event_idstr, role)
                            await bot.send(ctx.channel, f"Tous les membres ayant le rôle {role.name} sont maintenant invités à la soirée {bot.vars['events'][event_idstr]['name']}")
                        except Exception as e :
                            await bot.send(ctx.channel, f"Quelque chose s'est mal passé pendant l'invitation du rôle {role.name}")
                            raise Exception(e)
                    return
                
            await bot.send(ctx.channel, f"Mauvaise utilisation de la commande. Utilise \"!help invite\" pour savoir comment utiliser cette commande")

        else :
            await bot.send(ctx.channel, f"Aucune de tes soirées ne possède l'identifiant \"{args[0]}\"")

    else :
        await bot.send(ctx.channel, f"Mauvaise utilisation de la commande. Utilise \"!help invite\" pour savoir comment utiliser cette commande")

@bot.command(name="uninvite")
@bot.private_command
async def uninvite_gamebot(ctx: commands.Context, *args, **kwargs) :

    author = bot.guild.get_member(ctx.author.id)

    if len(args) > 1 :
        
        event_idstr = f"{author.name}#{author.discriminator}:{args[0]}"
        host = bot.get_discord_member(event_idstr.split(':')[0])
        target = " ".join(args[1:])

        if event_idstr in bot.vars["events"] and bot.vars["events"][event_idstr]["created"] :

            # désinviter un membre
            for pseudo in bot.vars["members"] :
                member = bot.get_discord_member(pseudo)
                if ((re.match(r"^(\d+)$", args[1]) and int(args[1]) == member.id)
                    or (target == member.display_name and len([m.display_name for m in bot.guild.members if m.display_name == target]) == 1)) :
                    if (member.id in bot.vars["events"][event_idstr]["invited_members"]) and member != host :
                        try :
                            await bot.uninvite_member(event_idstr, member)
                            msg = f"Invitation à la soirée {bot.vars['events'][event_idstr]['name']} annulée pour {member.display_name}."
                            if bot.member_is_invited_to_event(event_idstr, member) :
                                msg += f" {member.display_name} est cependant toujours invité(e) via l'un de ses rôles."
                            await bot.send(ctx.channel, msg)
                        except Exception as e :
                            await bot.send(ctx.channel, f"Quelque chose s'est mal passé pendant l'annulation de l'invitation de {member.display_name}")
                            raise Exception(e)
                    return

            # désinviter un rôle
            for role in bot.guild.roles :
                if ((re.match(r"^(\d+)$", args[1]) and int(args[1]) == role.id)
                    or (target == role.name and len([r.name for r in bot.guild.roles if r.name == target]) == 1)) :
                    if (role.id in bot.vars["events"][event_idstr]["invited_roles"]) :
                        try :
                            await bot.uninvite_role(event_idstr, role)
                            await bot.send(ctx.channel, f"Les membres ayant le rôle {role.name} et n'ayant pas été invité autrement que via ce rôle ont été désinvité")
                        except Exception as e :
                            await bot.send(ctx.channel, f"Quelque chose s'est mal passé pendant l'annulation de l'invitation du rôle {role.name}")
                            raise Exception(e)
                    return
                
            await bot.send(ctx.channel, f"Mauvaise utilisation de la commande. Utilise \"!help uninvite\" pour savoir comment utiliser cette commande")

        else :
            await bot.send(ctx.channel, f"Aucune de tes soirées ne possède l'identifiant \"{args[0]}\"")

    else :
        await bot.send(ctx.channel, f"Mauvaise utilisation de la commande. Utilise \"!help uninvite\" pour savoir comment utiliser cette commande")

