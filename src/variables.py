import os
from dotenv import load_dotenv

load_dotenv()

if (os.getenv("ENV") == "PROD") :
    from variables_prod import *
else :
    from variables_test import *

DISCORD_MAX_MESSAGE_LENGTH = 2000

ROLES_TO_IGNORE = ["base", "7tadellien(ne)", "maintenance", "@everyone", "admin"]

BOT_VARS_DEFAULTS = {
    "members": {
        'id': 0,
        'questionned': '',
        'questions': [],
        'object_id': 0,
        'birthday': "0"
    },
    "roles": {},
    "events": {
        "name": "",
        "host": "",
        "place": "",
        "datetime": "",
        "description": "",
        "nb_max_guests": "",

        "invited_guests": [],
        "waiting_guests": [],
        "present_guests": [],

        "invitations_channel_id": 0,
        "soirées_channel_id": 0,
        "logs_channel_id": 0,
        
        "created": False
    },
    "config": {
        "hours_offset": 0,
        "logs_retention_period": "1 month",
        "maintenance": "down",
        "maintenance_roles_backup": {},
        "rules_roles_backup": {}
    }
}

EVENT_CHANNEL_PERMISSIONS = {
    "invitations": {
        "read_messages": True,
        "send_messages": False,
        "create_instant_invite": False
    },
    "soirées": {
        "read_messages": True,
        "send_messages": True,
        "create_instant_invite": False
    },
    "logs": {
        "read_messages": True,
        "send_messages": False,
        "create_instant_invite": False
    },
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
    "maintenance": """Le serveur est temporairement indisponible pour cause de maintenance. Je ne sais pas exactement ce que fait {owner_mention}, il ajoute peut-être des salon ou me met à jour, qui sait ?\
J'espère que cela ne durera pas trop longtemps, veuillez nous excuser pour la gêne occasionnée.""",
    "anniversaires": """C'est l'anniversaire de {member_mention} aujourd'hui ! {age}""",
    "invitation": """Hello @here !

Vous avez été invité à une soirée par {host}

Voici quelques informations sur cette soirée :
Lieu : {lieu}
Date : {date}
Heure : {heure}
Description : {description}

Réagis avec :+1: si tu souhaites participer à cette soirée
{NB}
"""
}

# date: JJ/MM
# year: /AAAA
# time: ( hours:minutes)
# hours: ([0-1][0-9]|2[0-3])
# minutes: [0-5][0-9]
birthday_date_regexp = r"^(((?P<date>((0[1-9]|[1-2][0-9]|3[0-1])/(01|03|05|07|08|10|12))|((0[1-9]|[1-2][0-9]|30)/(04|06|09|11))|((0[1-9]|[1-2][0-9])/02))(?P<year>/\d{4}){0,1}(?P<time> (?P<hours>[0-1][0-9]|2[0-3]):(?P<minutes>[0-5][0-9])){0,1})|0)$"

# datetime: "date time" (JJ/MM/AAAA HH:MM)
# date:     "day/month/year"
# time:     "hour:minute"
# day:      01 - 31
# month     01 - 12
# year      \d{4}
# hour      00 - 23
# minute    00 - 59
event_datetime_regexp = r"^(?P<datetime>(?P<date>(?P<day>0[1-9]|[1-2][0-9]|3[0-1])/(?P<month>0[1-9]|1[0-2])/(?P<year>\d{4})) (?P<time>(?P<hour>[0-1][0-9]|2[0-3]):(?P<minute>[0-5][0-9])))$"

CREATION_QUESTIONS = {
    "birthday": {
        "date": {
            "text": """Si tu veux que je te souhaite ton anniversaire dans le salon #anniversaires, envoie-moi la date de celui-ci au format JJ/MM[/AAAA] [HH:MM].\
Si tu précises ton année de naissance, je donnerai ton âge dans le message. Si tu précise l'heure de ta naissance, j'enverrai le message à cette heure là (sinon je le ferai à minuit).
Si tu ne veux pas que j'annonce ton anniversaire, envoie-moi 0.
""",
            "valid": birthday_date_regexp
        }
    },
    "event": {
        "name": {
            "text": "Quel nom veux-tu donner à cette soirée ? (ça sera le nom donné aux salons de discussion)",
            "valid": r"^(.+)$"
        },
        "description": {
            "text": "Donne-moi une description pour cette soirée. Celle-ci sera partagée avec les invités de la soirée",
            "valid": r"^(.+)$"
        },
        "host": {
            "text": "Sous quel nom veux-tu que je t'appelle dans le message d'annonce de la soirée ? Cela peut servir si certains invités ne connaissent pas ton pseudo. Si tu veux que je donne uniquement ton pseudo, envoie-moi \".\"",
            "valid": r"^(.+)$"
        },
        "place": {
            "text": "Où se déroulera cette soirée ?",
            "valid": r"^(.+)$"
        },
        "datetime": {
            "text": "Quand se déroulera cette soirée ? format : JJ/MM/AAAA HH:MM",
            "valid": event_datetime_regexp
        },
        "nb_max_guests": {
            "text": "Combien veux-tu qu'il y ait de personne au maximum à cette soirée (toi compris) ? Tu pourras inviter plus de personnes que cette valeur mais toutes ne pourront pas accepter l'invitation, je m'occuperai de gérer la liste d'attente si trop de personnes acceptent l'invitation",
            "valid": r"^([1-9]\d*|0)$"
        }
    }
}

HELP_MESSAGES = {

    "birthday": """Cette commande sert à m'informer de ta date d'anniversaire afin que je puisse te le souhaiter le jour venu dans un salon dédié\
(et par la même occasion informer les autres membres du serveur de cet événement). Elle s'utilise de la façon suivante :

!birthday

Quand tu utilises cette commande, je te pose une question en t'expliquant dans quel format me répondre.
""",

####################################################################################################################################################################

    "event": """Cette commande sert à organiser des soirées, elle s'utilise de la façon suivante :

!event __option__

Options :
create - crée une soirée 
read [__event_id__] - affiche des informations sur toutes les soirées que tu as créé ou une soirée en particulier
delete __event_id__ - supprimer une soirée

Pour plus de détails sur une option, tu peux utiliser la commande "!help event __option__"
""",

####################################################################################################################################################################

    "event create": """Cette commande sert à créer une soirée. Tu pourras ensuite inviter des membres du serveur à cette soirée grâce à la commande "!invite".
Si tu utilises la commande "!event create" pour créer une soirée, je vais te guider dans la création de celle-ci en te posant des questions (attention: je mets\
parfois un peu de temps à poser la première question car je fais d'autres choses avant de commencer à poser les questions).\
Tes réponses me servirons à remplir les différents attributs de la soirée que voici :
- le nom que tu veux donner à la soirée (il servira à nommer les salons dédiés à celle-ci)
- une description pour la soirée. Elle sera affichée dans le message d'invitation celle-ci
- ton nom (pour l'afficher dans le message d'invitation, cela peut être utile si certains invités ne savent pas qui se cache derrière ton pseudo).\
Si tu ne veux pas que je donne ton nom (et donc que je mette uniquement ton pseudo dans le message d'invitation), répond-moi à cette question avec "."
- le lieu où se déroulera la soirée
- la date et l'heure de la soirée (au format "JJ/MM/AAAA HH:MM")
- le nombre maximum de participants à la soirée (toi compris). Tu pourras inviter plus de participants que ce nombre mais tous ne pourront pas accepter\
l'invitation si tu le fais (premier arrivé premier servi). Je m'occupe de gérer la liste d'attente si trop de personnes acceptent l'invitation. Si tu ne\
souhaites pas renseigner de nombre maximum de participants, répond à cette question avec "0"
""",

####################################################################################################################################################################

    "event read": """Cette commande sert à obtenir des informations sur toutes les soirées que tu as créé ou une de ces soirées en particulier. Elle s'utilise de la façon suivante :

!event read [__event_id__]

Si tu ne renseignes pas l'identifiant, je te répondrai avec une liste des soirées que tu as créé en faisant correspondre l'identifiant de la soirée avec son nom.\
Si tu renseignes l'identifiant de la soirée, je te donnerai toutes les informations utiles sur la soirée en question.
""",

####################################################################################################################################################################

    "event delete": """Cette commande sert à supprimer une soirée que tu as créée. Elle s'utilise de la façon suivante :

!event delete __event_id__

Si la soirée n'est pas encore passée, je préviendrai tous les membres du serveur invités que celle-ci est annulée.
""",

####################################################################################################################################################################

    "invite": """Cette commande sert à inviter un membre ou un rôle du serveur à une soirée que tu as créée. Elle s'utilise de la façon suivante :

!invite __event_id__ __guest__

avec :
- event_id: l'identifiant de la soirée à laquelle tu souhaites inviter quelqu'un (tu peux utiliser la commande "!event read" pour connaitre les identifiants de tes soirées)
- guest: ce paramètre représente la personne ou le rôle que tu souhaites inviter. Il peut être :
  - le pseudo d'un membre (celui que tu vois dans la liste des membres)
  - l'identifiant d'un membre
  - la mention d'un rôle (mentionner le rôle). Malheureusement, la mention ne fonctionne pas pour inviter un membre car on ne peut pas mentionner quelqu'un dans un salon auquel il n'a pas accès.
""",

####################################################################################################################################################################

    "uninvite": """Cette commande sert à annuler l'invitation d'un membre ou un rôle à une soirée. Elle s'utilise exactement de la même manière que la commande "!invite" mais aura l'effet inverse."""
}