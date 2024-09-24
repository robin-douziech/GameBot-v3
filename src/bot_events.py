from bot_instanciation import *

@bot.event
async def on_ready():

    bot.guild = bot.get_guild(BOT_GUILD_ID)
    bot.admin_role = bot.guild.get_role(ADMIN_ROLE_ID)

    