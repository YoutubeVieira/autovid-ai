# Avant publication : revue et liste de contrôle

Dernière revue : tout le dépôt `second-souffle-pwa` (code, textes, contrastes, accessibilité, hors connexion, documents).

## Corrigé pendant la revue
- **Contrastes** : toutes les paires texte/fond atteignent 4,5 : 1 et les éléments graphiques 3 : 1 dans les trois ambiances, en clair et en sombre (vert de réussite, texte secondaire, accent orange, texte de la sphère du décompte).
- **Défilement** : toucher une zone du corps ne remonte plus l'écran en haut.
- **Lecteur de séance** : le décompte suit l'horloge (il rattrape les secondes si le téléphone se met en veille) ; le son est activé dès le premier appui sur « Commencer ».
- **Accessibilité** : le titre reçoit le focus à chaque changement d'écran ; l'écran entier n'est plus une zone annoncée en continu.
- **Hors connexion** : le service worker affiche tout de suite la version en cache et se met à jour en arrière-plan.
- **Textes** : les réponses du coach ne promettent plus un remplacement précis d'exercice ; les phrases d'explication (genou, dos, ventre) sont plus prudentes ; « tour(s) » accordé ; trois textes inutilisés supprimés.
- **Durées** : « 10 à 20 minutes » et « douze minutes » étaient faux (de 4 à 17 minutes selon le niveau). Corrigé dans l'application et dans la voix off.
- **Guide PDF** : 25 pages, l'ordre de tournage tient sur une page.

## Tests
- `node tests/logic.test.js` : logique pure (séance, objectifs, alimentation, poids, lecteur, réponses, textes dans les trois langues).
- `node tests/gemini.test.js` : requête, réponse et erreurs de l'IA Gemini, sans réseau.
- `node tests/smoke.js` : parcours complet dans un navigateur, débordement horizontal sur chaque écran à 320 px, texte très grand, injection de HTML, rechargement, hors connexion, objectifs, repas et coach IA avec un faux service Google (clé jamais dans l'adresse, sources sûres, réponse HTML affichée en texte, symptôme grave non envoyé).

## Ajouts de la version 2 (objectifs, alimentation, vrai coach IA)
- **Objectifs** : huit objectifs au choix (trois au maximum), qui orientent le choix des exercices ; objectif de jours de lumière par semaine ; suivi du poids facultatif, gardé sur l'appareil.
- **Alimentation** : repères généraux, cinq cases à cocher par jour, idées de repas adaptées à chaque langue. Ce ne sont pas des conseils personnalisés ni un régime.
- **Coach IA** : si l'utilisateur colle sa propre clé d'API Google, Léo répond avec l'IA Gemini, avec recherche Google facultative et sources affichées. Sans clé, il répond avec des phrases écrites d'avance. Un symptôme grave (douleur à la poitrine, vertige, engourdissement) n'est jamais envoyé à l'IA : l'application renvoie vers un médecin.
- Le nom du modèle (gemini-3.8-flash par défaut) et la forme exacte de la requête n'ont pas pu être vérifiés dans la documentation de Google (accès réseau bloqué pour moi) : le test de connexion des réglages sert à les vérifier.

## À faire avant de publier (rien de tout cela n'est fait)
**Validation par des personnes**
- [ ] Kinésithérapeute ou enseignant en activité physique adaptée : les 28 exercices, leurs consignes, les variantes, le code posture, les textes d'anatomie, les séances de relaxation.
- [ ] Relecture du portugais du Brésil (interface, voix off) par une personne de langue maternelle ; relecture de l'anglais.
- [ ] Juriste : contrats de droit à l'image, conditions d'utilisation, politique de confidentialité, mentions sur les données de santé (RGPD).

**Contenu**
- [ ] Vidéos réelles des exercices à la place des emplacements « Vidéo à tourner ».
- [ ] Fichiers audio de la voix off (411 fichiers, 137 par langue), avec la mention « voix synthétique » dans l'application.
- [ ] Remplacer l'illustration de Léo si les conditions d'usage commercial de l'outil qui l'a générée ne le permettent pas.
- [ ] Profil de la coach privé « Camille » : exemple à remplacer par une vraie personne diplômée, ou à retirer.

**Technique**
- [ ] **Clé d'API de l'IA : ne pas demander de clé aux utilisateurs dans l'application publiée.** Passer par un petit serveur qui garde votre clé, limite l'usage par utilisateur et filtre les messages. Sans cela, quiconque ouvre l'application peut lire la clé et l'utiliser.
- [ ] **Confidentialité de l'IA** : les messages et le profil de santé (âge, objectifs, zones sensibles) partent chez Google. Il faut un consentement explicite, une mention dans la politique de confidentialité et un contrat de traitement adapté (données de santé, RGPD).
- [ ] Coûts de l'IA et de la recherche Google : à chiffrer d'après la grille de Google avant de proposer le coach IA dans l'abonnement.
- [ ] Contrôler les réponses de l'IA sur un jeu de questions sensibles (douleurs, régimes, médicaments) et décider ce qu'elle doit refuser.
- [ ] Serveur : clé de l'API du coach IA gardée côté serveur, comptes, messages du coach privé, espace du responsable.
- [ ] Paiement réel (abonnement) et prix à confirmer ; essai gratuit et annulation conformes aux règles du Play Store.
- [ ] Hébergement en HTTPS ; changer `VERSION` dans `sw.js` quand la liste des fichiers change.
- [ ] Page de politique de confidentialité en ligne (obligatoire pour le Play Store) et lien dans l'application.
- [ ] Publication sur le Play Store : emballer la page dans une application Android, puis test fermé (12 testeurs pendant 14 jours pour un nouveau compte personnel).
- [ ] Essais sur de vrais téléphones Android et iPhone (Safari), petits écrans, grande taille de texte du système, lecteur d'écran.

**Limites connues**
- La taille du texte utilise la propriété CSS `zoom` : absente des anciennes versions de Firefox (avant la 126).
- Le coach IA et le coach privé sont des démonstrations (réponses écrites d'avance, aucun message envoyé).
- Les messages du coach privé gardent la langue dans laquelle ils ont été écrits si l'on change de langue ensuite.
- Le guide d'anatomie est un schéma 2D simplifié ; le modèle 3D demande une licence à vérifier (Z-Anatomy est en CC BY-SA, avec des parties non commerciales).
- Les prix, le profil de la coach et les durées de tournage sont des propositions.
