Description des protocoles de communication utilisés:

- Protocole TCP pour la communication client/serveur

Notre application fonctionne sur base de commandes entrées par l'utilisateur dans son shell.
Chaque commande fait appel à une fonction qui communique avec le serveur en lui envoyant un 'parcel', qui est
un objet pyhton de type dictionnaire. Celui-ci contient deux clé: 'message', qui permet au serveur de lancer 
la fonction correspondante, et 'data', qui est un objet contenant de l'information. 
Le 'parcel' est compilé et envoyé par la méthode 'datatoserver(data)' du fichier 'Chatclient',
qui attend ensuite une réponse du serveur et la retourne au client. 
(Pour créer un lien avec le serveur, la méthode crée à chaque nouvel envoi un socket associé 
à l'adresse du serveur et le ferme lorsque la réponse a été reçue.)

Le serveur, qui met en attente les clients pour les traiter un par un, recoit le 'parcel' du client avec lequel
il est connecté, lance la fonction adéquate et utilise ensuite un procédé équivalent pour répondre au client.
C'est-à-dire, il crée un dictionnaire python 'response' (de contenu variable selon la fonction appelée) et l'envoie 
via la méthode 'datatoclient(data)' du fichier 'Chatserver'. Suite à cela, le serveur coupe alors la connection
avec ce client et traîte le suivant.

- Protocole UDP pour la communication client/client

Au lancement du fichier 'Chatclient', un socket de type SOCK_DGRAM est créé avec une adresse par défaut
si elle n'est pas spécifiée par l'utilisateur.
Lorsqu'un client souhaite entamer une conversation (voir fichier README concernant les commandes),
il introduit une requête au serveur qui lui fournit alors l'adresse de son correspondant, 
c'est-à-dire son adresse IP et le port d'écoute du socket.
La connection entre les deux utilisateurs se fait ensuite en peer-to-peer:
	-Chaque message est encodé et envoyé au moyen de la méthode 'send(message)'. 
	-Une méthode 'receive(param)', qui tourne en permanence sur le programme, permet de recevoir, decoder
	 et afficher les messages réceptionnés. Si l'expéditeur du message reçu n'est pas le correspondant actuel 
	 du client, une notification est alors envoyée à celui-ci pour l'en avertir.
