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
