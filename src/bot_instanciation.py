from GameBot import *

bot = GameBot()
bot.remove_command("help")

async def backup_roles(result_list: list[int], member: discord.Member, remove: bool = False) :
    for role in [r for r in member.roles if not(r in [bot.roles[role_str] for role_str in ROLES_TO_IGNORE])] :
        result_list.append(role.id)
        if remove :
            await member.remove_roles(role)
    return result_list

def get_role_by_name(role_name: str) :
    for role in bot.guild.roles :
        if role.name == role_name :
            return role
    return None

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
