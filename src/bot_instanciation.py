from GameBot import *

bot = GameBot()
bot.remove_command("help")

def get_time_ago(delta: str) :
    (day, month, year) = bot.get_current_datetime()[:3]
    current_date = dt.datetime(year, month, day)
    m = re.search("^(\d+) (day|month|year)[s]{0,1}$", delta)
    date: dt.datetime = None
    match m.group(2) :
        case 'day' :
            date = current_date + dt.timedelta(days=-int(m.group(1)))
        case 'month' :
            date = current_date + dt.timedelta(days=-30*int(m.group(1)))
        case 'year' :
            date = current_date + dt.timedelta(days=-365*int(m.group(1)))
    return date
