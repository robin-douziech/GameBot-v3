import os
from dotenv import load_dotenv

load_dotenv()

if (os.getenv("ENV") == "PROD") :
    from variables_prod import *
else :
    from variables_test import *

DISCORD_MAX_MESSAGE_LENGTH = 2000

BOT_VARS_DEFAULTS = {
    "members": {
        'id': 0,
        'questionned': '',
        'questions': [],
        'object_being_created': {
            'type': '',
            'id': 0
        },
        'birthday': "0"
    },
    "roles": {},
    "events": {},
    "config": {
        "hours_offset": 0,
        "logs_retention_period": "1 month"
    }
}

MESSAGES = {
    "informations": """## Bienvenue sur 7tadelles ! <:7tadelles_logo:1289883296439730178>

Je m'appelle GameBot et je vais tenter de rendre ton expérience sur ce serveur la plus agréable possible.

7tadelles a été créé afin de rassembler quelques amis amateurs de jeux de société. Ma principale fonction est l'organisation de soirées jeux.\
N'importe qui sur ce serveur peut m'utiliser pour organiser une soirée et y inviter des membres du serveur.

Voici une présentation des différentes catégories du serveur :

- Tu pourras discuter de tout et n'importe quoi avec n'importe qui dans les salons de la catégorie #général
- Quand quelqu'un t'invite à une soirée, tu vera apparaître un salon dans la catégorie #invitations avec un message auquel tu pourras réagir pour accepter l'invitation ou non
- Si tu acceptes une invitation, tu auras accès à un salon dans la catégorie #soirées
""",
    "rules": """Ici c'est les règles, t'as intérêt à les respecter""",
    "maintenance": """https://tenor.com/view/discord-gif-27684109
Le serveur est temporairement indisponible pour cause de maintenance. Je ne sais pas exactement ce que fait {owner_mention}, il ajoute peut-être des salon ou me met à jour, qui sait ?\
J'espère que cela ne durera pas trop longtemps, veuillez nous excuser pour la gêne occasionnée.""",
    "anniversaires": """C'est l'anniversaire de {member_mention} aujourd'hui ! {age}"""
}

# date: JJ/MM
# year: /AAAA
# time: ( hours:minutes)
# hours: ([0-1][0-9]|2[0-3])
# minutes: [0-5][0-9]
birthday_date_regexp = r"^(((?P<date>((0[1-9]|[1-2][0-9]|3[0-1])/(01|03|05|07|08|10|12))|((0[1-9]|[1-2][0-9]|30)/(04|06|09|11))|((0[1-9]|[1-2][0-9])/02))(?P<year>/\d{4}){0,1}(?P<time> (?P<hours>[0-1][0-9]|2[0-3]):(?P<minutes>[0-5][0-9])){0,1})|0)$"

CREATION_QUESTIONS = {
    "birthday": {
        "date": {
            "text": """Si tu veux que je te souhaite ton anniversaire dans le salon #anniversaires, envoie-moi la date de celui-ci au format JJ/MM[/AAAA] [HH:MM].\
Si tu précises ton année de naissance, je donnerai ton âge dans le message. Si tu précise l'heure de ta naissance, j'enverrai le message à cette heure là.
Si tu ne veux pas que j'annonce ton anniversaire, envoie-moi 0.
""",
            "valid": birthday_date_regexp
        }
    }
}