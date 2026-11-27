# Néon Bay : comment le vendre

## Ce que contient le jeu
- 30 niveaux de 10 étapes (300 étapes) dans 4 pays inventés : Néon Bay (États-Unis), Porto Lumi (Italie), Sierra Verde (Colombie), Morro Azul (favelas du Brésil).
- 15 types d'étapes : rendez-vous, vol de voiture, garage, boutique, livraison chronométrée, récupération de valises, fusillade, chef de gang, fuite, survie, tunnel souterrain, corruption d'un agent, escorte (rappeur, Consigliere, pilote, DJ), destruction de convoi, course.
- Difficulté qui monte à chaque niveau : plus d'ennemis, plus résistants et plus précis, chronos plus serrés, police plus forte.
- Boutique : 7 armes (pistolet, mitraillette, fusil à pompe, fusil d'assaut, fusil de précision, lance-roquettes, minigun), 3 armures, trousses de soins, nitro, blindage de voiture, brouilleur radio, carnet de contacts.
- Soudoyer la police (touche B), tunnels souterrains, atelier de peinture, récompenses par étape et par niveau.
- Sauvegarde automatique dans le navigateur du joueur.

## Modèle de vente : niveau 1 gratuit, le reste payant
1. **Choisis où encaisser** : un Stripe Payment Link, Systeme.io, Gumroad ou Lemon Squeezy.
2. **Mets ton lien** dans `js/data.js` → `SHOP_CONFIG.buyUrl`, et ton prix dans `SHOP_CONFIG.price`.
3. **Change le sel secret** `SHOP_CONFIG.salt` (dans `js/data.js`) **et** `SALT` (dans `tools/generate-codes.js`) avec la même valeur, avant de vendre.
4. **Génère des codes** : `node tools/generate-codes.js 200 > codes.txt`. Chaque client reçoit un code après paiement (Gumroad et Lemon Squeezy peuvent envoyer un code de licence automatiquement depuis une liste).
5. Le joueur clique sur « Jeu complet », saisit son code, et les 29 niveaux se débloquent.

## Mettre le jeu en ligne
- `node tools/build-standalone.js` crée `dist/index.html`, un seul fichier qui contient tout le jeu.
- Tu peux l'envoyer sur **itch.io** (projet « HTML », jouable dans le navigateur), sur ton site, ou sur Netlify / GitHub Pages.

## Limites à connaître
- Les codes sont vérifiés dans le navigateur : quelqu'un de très motivé peut lire le code source et contourner le verrou. C'est suffisant pour démarrer, mais pour une vraie protection il faut un petit serveur qui vérifie les achats (par exemple Supabase + Stripe), ou vendre la version complète comme fichier séparé sur itch.io.
- La progression est enregistrée dans le navigateur du joueur : s'il change d'appareil ou vide ses données, il recommence (son code reste valable).
- Avant de vendre, fais tester les 30 niveaux par quelques joueurs pour régler la difficulté (valeurs dans `makeStep` et `updEnemy` de `js/engine.js`).
