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
            for member in [m for m in bot.guild.members if not(m.bot)] :
                await member.add_roles(bot.roles["maintenance"])
                await member.remove_roles(bot.roles["7tadellien(ne)"])
                await member.remove_roles(bot.roles["base"])
                for role_id in bot.vars["members"][f"{member.name}#{member.discriminator}"]["roles"] :
                    await member.remove_roles(bot.guild.get_role(role_id))
            bot.config["maintenance"] = "up"
            bot.write_config()
        elif args[0] == "down" and bot.config["maintenance"] == "up" :
            for member in [m for m in bot.guild.members if not(m.bot)] :
                for role_id in bot.vars["members"][f"{member.name}#{member.discriminator}"]["roles"] :
                    await member.add_roles(bot.guild.get_role(role_id))
                await member.remove_roles(bot.roles["maintenance"])
                await member.add_roles(bot.roles["base"])
            if bot.channels["rules"] is not None :
                message: discord.Message = (await bot.get_messages_by_ids_in_channel(bot.messages["rules"][-1:], bot.channels["rules"]))[0]
                reaction: discord.Reaction = [r for r in message.reactions if r.emoji == chr(0x1F4DD)][0]
                async for member in reaction.users() :
                    await member.add_roles(bot.roles["7tadellien(ne)"])
            else :
                for member in [m for m in bot.guild.members if not(m.bot) and m.get_role(ROLES_IDS["7tadellien(ne)"]) is None] :
                    await member.add_roles(bot.roles["7tadellien(ne)"])
            bot.config["maintenance"] = "down"
            bot.write_config()

