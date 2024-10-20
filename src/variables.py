import os
from dotenv import load_dotenv

load_dotenv()

if (os.getenv("ENV") == "PROD") :
    from variables_prod import *
else :
    from variables_test import *

DISCORD_MAX_MESSAGE_LENGTH = 2000
RETRY_TIMEOUT = 1

ROLES_TO_IGNORE = ["base", "7tadellien", "maintenance", "admin"]
CHANNELS_BY_ROLE = {
    "base": ["bienvenue", "informations", "règles"],
    "7tadellien": ["annonces", "anniversaires"],
    "maintenance": ["maintenance"],
    "admin": ["logsgamebot"]
}

BOT_VARS_DEFAULTS = {
    "members": {
        'id': 0,
        'questionned': '',
        'questions': [],
        'object_id': 0,
        'banned': False,
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
        
        "invited_members": [],
        "invited_roles": [],

        "invitations_channel_id": 0,
        "soirées_channel_id": 0,
        "logs_channel_id": 0,
        
        "created": False
    },
    "config": {
        "hours_offset": 0,
        "logs_retention_period": "1 month",
        "règles": True,
        "maintenance": "down",
        "ban_roles_backup": {},
        "maintenance_roles_backup": {},
        "rules_roles_backup": {}
    }
}

EVENT_CHANNEL_PERMISSIONS = {
    "invitations": {
        "read_messages": True,
        "read_message_history": True
    },
    "soirées": {
        "read_messages": True,
        "send_messages": True,
        "read_message_history": True
    },
    "logs": {
        "read_messages": True,
        "read_message_history": True
    },
}

MESSAGES = {
    "informations": """# <:7tadelles_logo:1289883296439730178> Bienvenue sur 7tadelles <:7tadelles_logo:1289883296439730178>

Je m'appelle GameBot et je vais tenter de rendre ton expérience sur ce serveur la plus agréable possible.

7tadelles a été créé afin de rassembler quelques amis amateurs de jeux de société. Ma principale fonction est l'organisation d'événements.\
N'importe qui sur ce serveur peut m'utiliser pour organiser un événement et y inviter des membres du serveur (ces événements ne sont pas forcément liés au domaine du jeu de société, tu peux créer n'importe quel type d'événement).

Voici les principales catégories du serveur et leur utilité :

### :speech_left: Général
Cette catégorie est là pour permettre aux membres du serveur de discuter de jeux de société, mais aussi de n'importe quoi d'autre. \
N'hésite pas à demander la création d'un salon si tu souhaites discuter d'un sujet en particulier.

### :envelope: Invitations
Si quelqu'un t'invite à un événement qu'il a créé, tu aura accès à un salon dans cette catégorie dans lequel tu pourras accepter cette invitation en \
réagissant à un message.

### :tada: Soirées
Si tu acceptes une invitation à une soirée (et qu'il reste de la place), tu auras accès à un salon dans cette catégorie dans lequel tu pourras discuter avec \
les autres membres du serveur participant à cette soirée.

### :page_facing_up: Logs
Si tu crées un événement, tu auras accès à un salon dans cette catégorie dans lequel je t'informerai de ce qu'il se passe à propos de cet événement \
(quels membres tu as invité, quels membres ont accepté l'invitation, etc.)


""",
    "règles": """# :scroll: Règles du serveur

Afin que chacun puisse avoir une expérience de ce serveur la plus agréable possible, il est nécessaire que chaque membre de celui-ci accepte les règles suivantes :

:straight_ruler: __Règle n°1__ : Chaque membre du serveur doit être respectueux envers les autres membres. 

:straight_ruler: __Règle n°2__ : Ce serveur a vocation à être un endroit agréable où tout le monde échange avec plaisir. Afin de faire en sorte que ce soit \
le cas, il est demandé à ses membres d'éviter les sujets risquant de provoquer des joutes verbales (si vous voulez en découdre il y a un réseau social qui a \
été conçu pour ça et qui s'appelle twitter X, mais ici on évite les sujets à risque et on passe des bon moments)

:straight_ruler: __Règle n°3__ : Bien évidemment, on respecte les règles prévues par les espaces englobant ce serveur. Je vous passe les détails mais si vous \
les voulez et avez quelques années de libre devant vous pour les étudier, elles sont dispo [ici](https://discord.com/terms) et [ici](https://www.legifrance.gouv.fr/codes/texte_lc/LEGITEXT000006070719/)

:straight_ruler: __Règle n°4__ : Être gentil

:straight_ruler: __Règle n°5__ : Ne pas être méchant

(Ceux qui ont la ref des deux dernières règles levez la main :raised_hand:)

En cas de non-respect de ces règles, {owner_mention} sera colère tout rouge :rage: et sanctionnera les contrevenants à coups de bâton <:baton:1297299703045816330>

Veuillez signer (:pencil:) ce message pour avoir accès au reste du serveur

Des bisous et à bientôt lors d'une soirée jeux :heart:
""",
    "maintenance": """Le serveur est temporairement indisponible pour cause de maintenance. Je ne sais pas exactement ce que fait {owner_mention}, il ajoute peut-être des salon ou me met à jour, qui sait ?\
J'espère que cela ne durera pas trop longtemps, veuillez nous excuser pour la gêne occasionnée.""",
    "anniversaires": """# JOYEUX ANNIVERSAAAAAAAAAIRE {member_mention} !!! ET SURTOUT PASSE UNE BONNE JOURNÉÉÉÉÉÉÉÉÉE !!! {age} :birthday: :tada: :tada: :tada: :tada: :tada: :tada: :tada: :tada: :tada:""",
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
            "text": "Combien veux-tu qu'il y ait de personnes au maximum à cette soirée (toi compris) ? Tu pourras inviter plus de personnes que cette valeur mais toutes ne pourront pas accepter l'invitation, je m'occuperai de gérer la liste d'attente si trop de personnes acceptent l'invitation",
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

Si la soirée n'est pas encore passée, je préviendrai tous les membres du serveur invités que celle-ci est annulée. \
Tu n'as pas besoin de désinviter tous les invités d'une soirée avant de la supprimer (et il est même préférable de ne pas le \
faire car si tu les désinvite, il recevront "tu n'es plus invité" alors que si tu supprime la soirée sans les désinviter, ils \
recevront "la soirée a été supprimée").
""",

####################################################################################################################################################################

    "invite": """Cette commande sert à inviter un membre ou un rôle du serveur à une soirée que tu as créée. Elle s'utilise de la façon suivante :

!invite __event_id__ __guest__

avec :
- event_id: l'identifiant de la soirée à laquelle tu souhaites inviter quelqu'un (tu peux utiliser la commande "!event read" pour connaitre les identifiants de tes soirées)
- guest: ce paramètre représente la personne ou le rôle que tu souhaites inviter

__Si tu invites un membre__ :

Le paramètre guest peut être l'identifiant du membre ou son pseudo (celui que tu vois dans la liste des membres)

__Si tu invites un rôle__ :

Le paramètre guest doit être la mention du rôle (tu dois mentionner le rôle). Je te conseille donc d'utiliser cette commande \
depuis ton salon avec le bot dans le serveur et non en messages privés pour pouvoir mentionner le rôle. Tous les membres \
possédant ce rôle et n'étant pas encore invités seront invités.

NB: si on ajoute un rôle invité à la soirée à un membre du serveur, ce membre sera invité à la soirée
""",

####################################################################################################################################################################

    "uninvite": """Cette commande sert à annuler l'invitation d'un membre ou un rôle à une soirée. Elle s'utilise de la façon suivante :

!uninvite __event_id__ __guest__

avec :
- event_id: l'identifiant de la soirée à laquelle tu souhaites désinviter quelqu'un (tu peux utiliser la commande "!event read" pour connaitre les identifiants de tes soirées)
- guest: ce paramètre représente la personne ou le rôle que tu souhaites désinviter

__Si tu désinvites un membre__ :

Le paramètre guest peut être l'identifiant du membre ou son pseudo (celui que tu vois dans la liste des membres)

__Si tu désinvites un rôle__ :

Le paramètre guest doit être la mention du rôle (tu dois mentionner le rôle). Je te conseille donc d'utiliser cette commande \
depuis ton salon avec le bot dans le serveur et non en messages privés pour pouvoir mentionner le rôle. Tous les membres \
invités à la soirées et ayant été invité uniquement via ce rôle seront désinvités.

Exemple :

Tu désinvite le rôle @role1, Toto est invité à la soirée et possède le rôle role1.
- si Toto possède un autre rôle qui est invité à la soirée, Toto est toujours invité
- si tu as invité Toto explicitement avec la commande "!invite __event_id__ Toto", Toto est toujours invité
- si tu n'as pas invité Toto explicitement et que Toto ne possède pas d'autre rôle encore invité à la soirée, Toto n'est plus invité

NB: si on supprime un rôle invité à la soirée à un membre du serveur et que ce membre était invité uniquement via ce rôle, le membre sera désinvité de la soirée
"""
}