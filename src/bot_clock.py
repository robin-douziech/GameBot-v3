from bot_instanciation import *

@tasks.loop(seconds=60)
async def clock() :

    (day, month, year, hours, minutes) = bot.get_current_datetime()

    # Souhaiter les anniversaires
    if f"{day}/{month} {hours}:{minutes}" in bot.birthday_datetimes :
        for member in bot.vars["members"] :
            discord_member = bot.get_discord_member(member)
            m = re.match(CREATION_QUESTIONS["birthday"]["date"]["valid"], bot.vars["members"][member]["birthday"])
            age = f"Cette personne agée a {int(f'20{year}') - int(m.group('year')[1:])} ans" if m.group('year') is not None else ""
            if f"{day}/{month} {hours}:{minutes}" == f"{m.group('date')}{m.group('time')}" :
                await bot.send(bot.channels["anniversaires"], MESSAGES["anniversaires"].format(member_mention=discord_member.mention, age=age))

    if f"{hours}:{minutes}" == "00:00" :

        # Nouveau fichier de logs quotidien
        if int(day) == 1 :
            if int(month) == 1 :
                os.makedirs(f"logs/20{year}", exist_ok=True)
            os.makedirs(f"logs/20{year}/{month}", exist_ok=True)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        handler = logging.FileHandler(f"logs/20{year}/{month}/{day}.log")
        handler.setFormatter(formatter)
        logging.getLogger().handlers = [handler]

        # Supprimer les fichiers de logs trop anciens
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
