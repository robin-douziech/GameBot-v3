from bot_instanciation import *

@bot.event
async def on_ready():

    bot.guild = bot.get_guild(BOT_GUILD_ID)
    bot.admin_role = bot.guild.get_role(ADMIN_ROLE_ID)

    for var_name in bot.vars :
        with open(bot.files[var_name], "rt") as f :
            bot.vars[var_name] = set_default_config(json.load(f), bot.defaults[var_name])
            bot.write_json(var_name)

    

