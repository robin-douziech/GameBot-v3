from bot_clock import *

@bot.event
async def on_ready():

    bot.guild = bot.get_guild(BOT_GUILD_ID)
    bot.admin_role = bot.guild.get_role(ROLES_IDS["admin"])
    bot.channels = {x: bot.guild.get_channel(x) for x in CHANNEL_IDS.values()}
    bot.owner = bot.guild.get_member(BOT_OWNER_ID)

    # load variables and set defaults
    for var_name in bot.vars :
        with open(bot.files[var_name], "rt") as f :
            bot.vars[var_name] = db_default_config(json.load(f), bot.defaults[var_name])
            bot.write_json(var_name)
    
    # load config and set default
    with open("json/config.json", "rt") as fread :
        config = json.load(fread)
        bot.config = default_config(config, bot.defaults["config"])
        with open("json/config.json", "wt") as fwrite :
            fwrite.write(json.dumps(bot.config, indent=2))

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
        if member not in bot.vars["members"] :
            members_to_add.append(member)
    for member in bot.vars["members"] :
         if member not in guild_members :
            members_to_remove.append(member)
    bot.add_members(members_to_add)
    bot.remove_members(members_to_remove)            

    if (not("informations" in bot.messages) or await bot.get_messages_by_ids_in_channel(bot.messages["informations"], "informations") == None) :
        await bot.channels[CHANNEL_IDS["informations"]].purge()
        messages = await bot.send(bot.channels[CHANNEL_IDS["informations"]], MESSAGES["informations"])
        bot.save_message("informations", [message.id for message in messages])

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
