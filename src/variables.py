BOT_GUILD_ID = 1282342173022621726
ADMIN_ROLE_ID = 1288199614306189383
DISCORD_MAX_MESSAGE_LENGTH = 2000

CHANNEL_IDS = {
    "informations" : 1289260988830580868,
    "règles": 1288199250764763250,
    "annonces": 1282367924291502161
}

BOT_VARS_DEFAULTS = {
    "members": {
        'id': 0,
        'questions': [],
        'object_being_created': {
            'type': '',
            'id': 0
        }
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
    "rules": """

"""
}