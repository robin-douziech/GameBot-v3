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

@tasks.loop(seconds=60)
async def clock() :
    now = dt.datetime.now().strftime('%d/%m/%y %H:%M')
    (date, time) = now.split()
