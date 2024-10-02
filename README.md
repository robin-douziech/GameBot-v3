# GameBot - v3

## Présentation

GameBot est un bot que j'ai développé pour le serveur discord où sont présents mes amis et moi. J'ai utilisé la bibliothèque discord.py qui requête l'API de discord. La documentation de cette bibliothèque est présente ici : https://discordpy.readthedocs.io/en/stable/.

Mes amis et moi apprécions les jeux de société, c'est pourquoi les fonctionnalités de GameBot gravitent autour de ce domaine. Sa principale fonctionnalité est l'organisation de soirées jeux (mais rien ne lie ces soirées au domaine du jeu de société, on pourrait utiliser GameBot pour organiser tout autre type d'événement entre amis).

## Installation

## Fonctionnalités

### Un bot robuste

GameBot a été développé pour être résistant aux crashs (c'est-à-dire qu'il est capable de récupérer au redémarrage un état identique à l'état qu'il avait lorsqu'il s'est arrêté). Il prend aussi en compte les réactions ajoutées aux messages importants lorsqu'il était éteint (par exemple: le message des règles auxquel il faut réagir pour avoir accès aux salons du serveur, ou un message d'invitation à une soirée auquel il faut réagir pour accepter l'invitation).

### Les fichiers du bot

```
json/                (non suivi)
  channels.json
  config.json
  events.json
  members.json
  messages.json
  roles.json
logs/                (non suivi)
  ...
src/
  .env               (non suivi)
  variables_test.py
  variables_prod.py
  variables.py
  utils.py
  GameBot.py
  bot_instanciation.py
  bot_clock.py
  bot_events.py
  commands_event.py
  commands_utils.py
  __main__.py
```



### Les logs

Afin de savoir ce qu'il s'est passé en cas de pépin avec le bot, je lui ai ajouté des logs (la bibliothèque interne logging de python s'en occupe très bien). Pour ne pas avoir un immense fichier de logs, je fais un fichier de logs par jour (le chemin du fichier est logs/AAAA/MM/JJ.log). Pour ne pas faire exploser la mémoir de mon serveur, je supprime les fichiers de logs trop vieux (il y a un paramètre dans json/config.json pour définir combien de temps les logs sont conservés, je ferai sûrement une commande pour modifier cette valeur sans devoir aller sur le serveur).

La commande !logs permet de récupérer les dernière lignes de logs du bot par message. Un paramètre optionel permet de dire combien de lignes de logs on veut récupérer (10 par défaut). Les logs récupérés sont les logs du jour courant, on ne peut pas récupérer les logs de la veille de cette manière, il faudra se déplacer sur le serveur (pas en personne hein, un coup de ssh suffira).

### Acceptez les règles !

Le bot ne donne accès aux différents salons du serveur à un nouvel arrivant qu'une fois qu'il a "accepté les règles" (= réagis avec une réaction particulière à un message du bot). Cela est géré grâce à un rôle qui est donné aux membres quand ils réagissent au message, les salons du serveur sont privés et réservé à ce rôle. Si vous ne souhaitez pas utiliser cette fonctionnalité sur votre serveur, c'est possible : il suffit de ne pas créer de salon pour le message des règles, ne renseignez pas l'identifiant du salon dans les variables, le bot échouera à récupérer le salon (que vous n'avez pas créé) et dans ce cas, il donne le rôle 7tadellien(ne) à tout le monde. __ATTENTION__: on pourrait penser qu'il est possible de ne pas rendre les salons du serveur privés si on ne souhaite pas utiliser cette fonctionnalité mais c'est une mauvaise idée car cela empêcherait la fonctionnalité "maintenance" de fonctionner (cf. plus bas).

### Joyeux anniversaire !

La commande !birthday permet à chaque membre du serveur de partager sa date d'anniversaire avec le bot afin qu'il puisse le lui souhaiter dans un salon dédié le jour venu (et par la même occasion informer les autres membres du serveur de cet événement). Cette fonctionnalité m'a été demandée par certains membres de mon serveur à la sortie de la v2 de GameBot. Les informations à donner au bot sont le mois et le jour de l'anniversaire au format JJ/MM et, de manière optionnelle, l'année et l'heure. Si l'année est précisée, le bot donnera l'âge du membre. Si l'heure est précisée, le bot souhaitera l'anniversaire à l'heure renseignée (à minuit sinon). Le format complet est donc JJ/MM\[\/AAAA\] \[HH:MM\].

### /!\ SERVEUR EN MAINTENANCE /!\

La commande !maintenance permet à un membre du serveur ayant le rôle "admin" de mettre le serveur en maintenance et de l'en faire sortir. Quand le serveur est en maintenance, les membres non-admin du serveur n'ont accès qu'à un seul salon du serveur dans lequel figure un message les informant de cette maintenance (salon auquel ils n'ont pas accès en temps normal). Pour obtenir ce comportement, j'utilise un rôle "maintenance" et je crée un salon privé réservé à ce rôle sur le serveur. Quand on entre en mode maintenance, tous les rôles de chaque membre du serveur sont retirés (à l'exception de "@everyone" qui est aussi un rôle et "admin"). Quand on quitte le mode maintenance, les rôles sont restitués. Un challenge de l'implémentation de ce comportement à été de restituer également les rôles administrés manuellement (et non par le bot). Ces rôles ne sont pas directement connus par le bot et il a fallu stocker leur identifiant pour chaque utilisateur (je fais ça dans le fichier json/members.json, dans la section "roles" de chaque membre). Un autre point auquel il faut faire attention est qu'aucun salon du serveur ne doit être publique, un tel salon serait visible de tous même quand le serveur est en maintenance.

### Organiser des soirées

Quand j'écris ces lignes, cette fonctionnalité n'est pas encore implémentée, mais j'ai déjà une idée de ce que j'aimerais faire pour celle-ci. J'utilise donc cette section comme un mémo, pour ne rien oublier quand je m'en occuperai.

Contrairement à la v2 de GameBot, cette version laissera n'importe quel membre du serveur créer des événements. Pour rendre cela possible, je vais modifier légèrement la façon de faire.

Avec GameBot-v2, il y avait deux types de soirées : les soirées où on invite des membres du serveur un par un et les soirées où on invite des rôles du serveur (quand on invite un rôle, tous les membres ayant ce rôle sont invités). Cela n'était pas tout le temps pratique (la manière de créer la soirée était un peu différente selon le type de soirée et ce que voyaient les personnes invitées différait aussi avec le type de soirée). De plus, il n'était pas possible de mixer les types de soirées (inviter quelques membre + un rôle).

Avec GameBot-v3, il y aura donc......... deux types de soirées (ah !). En fait pas vraiment, ça sera un peu différent : on pourra inviter des membres un par un, on pourra aussi inviter des rôles, mais surtout, on pourra inviter les deux en même temps. Comment ça marche ? Quand on crée une soirée jeux, on crée un salon pour celle-ci dans la catégorie "invitations" et un autre dans la catégorie "soirées". Quand quelqu'un est invité à une soirée, il est téléporté dans le salon de la catégorie "invitation" dans lequel figure un message d'invitation auquel il faut réagir pour accepter l'invitation (**personne ne peut écrire dans le salon à part le bot**). Quand une personne accepte l'invitation (en réagissant au message), elle est téléportée dans le salon de la catégorie soirée (**sans être retirée du salon d'invitation**), et c'est officiel, cette personne sera présente à le soirée (youpi !).
Les intérêt de cette nouvelle façon de faire :
- Pour les personnes invitées, il n'y a aucune différence entre ce qu'elle voit quand elle est invitée "en personne" ou via un rôle.
- Les invités peuvent voir facilement qui d'autre est invité (c'était possible avec la v2 mais cela a nécessité des complication dans l'utilisation des commandes)

Note pour moi-même, les trucs à pas oublier :

- faire une liste d'attente en cas de soirée complète
- salon de logs de la soirée -> y donner accès à son créateur (faire aussi un salon de logs du bot dans la catégorie admin)

Suppression de soirée :
- automatique une semaine après la soirée ???
- sinon: manuelle, mais bien faire attention à ne pas embêter les participants comme si on annulait la soirée avant qu'elle n'ait lieu (je me suis fait avoir lors de la v2)

### Vous avez dit jeu de socété ?

-> aller relire le premier paragraphe de la section précédente
GameBot permet aussi depuis sa première version d'avoir accès à des informations sur des jeux de sociéte. Jusqu'à la dernière version, il maintenait ~~sa propre base de données~~ son propre fichier JSON avec des jeux dedans et gérait la recherche de jeux. C'était plutôt bien fait : on pouvait même rechercher un jeu sans donner son nom complet, tant que le morceau donné suffit à l'identifier (oui, c'est de la recherche par clé incmplète dans un JSON, ou comment rendre des choses simples compliquées :D ). Mais maintenant, c'est fini ! Je délègue ce boulot à une API (il me semble que BGG possède une API pour chercher des jeux de société, sinon j'en trouverai une autre)

### C'est qui le meilleur ?

La deuxième version de GameBot permettait d'enregistrer des parties de jeu de société jouées afin de réaliser un classement entre les membres du serveur. J'ai supprimé cette fonctionnalité pour cette nouvelle version de GameBot et justifie ce choix grâce au nombre de parties enregistrées avec GameBot-v2 qui atteint la valeur vertigineuse de...... 0.