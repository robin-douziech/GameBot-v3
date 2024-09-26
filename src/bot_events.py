from bot_instanciation import *

@bot.event
async def on_ready():

    bot.guild = bot.get_guild(BOT_GUILD_ID)
    bot.admin_role = bot.guild.get_role(ADMIN_ROLE_ID)
    bot.channels = {x: bot.guild.get_channel(x) for x in CHANNEL_IDS.values()}

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

    # setting logs file
    (day, month, year) = bot.get_current_datetime()[:3]
    if not(os.path.exists(f"logs/20{year}/{month}/")) :
        os.makedirs(f"logs/20{year}/{month}")
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
    handler = logging.FileHandler(f"logs/20{year}/{month}/{day}.log")
    handler.setFormatter(formatter)
    logging.getLogger().handlers = [handler]

    bot.log(f"{bot.user.display_name} est prêt.", 'info')    

    clock.start()

@bot.event
async def on_message(message: discord.Message) :
	author = bot.guild.get_member(message.author.id)
	if not(author.bot) and message.channel == author.dm_channel :
		bot.log(f"DM message from {author.name}#{author.discriminator} : {message.content}")
	if message.content.startswith(bot.command_prefix) :
		await bot.process_commands(message)
	else :
		await bot.process_msg(message)

@tasks.loop(seconds=60)
async def clock() :

    (day, month, year, hours, minutes) = bot.get_current_datetime()

    if f"{hours}:{minutes}" == "00:00" :

        # setting logs file (new day)
        if int(day) == 1 :
            if int(month) == 1 :
                os.makedirs(f"logs/20{year}", exist_ok=True)
            os.makedirs(f"logs/20{year}/{month}", exist_ok=True)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        handler = logging.FileHandler(f"logs/20{year}/{month}/{day}.log")
        handler.setFormatter(formatter)
        logging.getLogger().handlers = [handler]

        # deleting too old logs files
        try :
            date = get_time_ago(bot.config['logs_retention_period'])
            years_dirs = os.listdir('logs')
            months_dirs = os.listdir(f"logs/{date.year}")
            days_files = os.listdir(f"logs/{date.year}/{date.month}")
            for _day in days_files :
                if int(_day.split('.')[0]) < date.day :
                    os.remove(f"logs/{date.year}/{date.month}/{'0' if int(_day) < 10 else ''}{_day}.log")
            for _month in months_dirs :
                if int(_month) < date.month :
                    shutil.rmtree(f"logs/{date.year}/{'0' if int(_month) < 10 else ''}{_month}")     
            for _year in years_dirs :
                if int(_year) < date.year :
                    shutil.rmtree(f"logs/{_year}")
        except Exception as e :
            bot.log(f"An exception occured while deleting logs files: {e}", 'error')
