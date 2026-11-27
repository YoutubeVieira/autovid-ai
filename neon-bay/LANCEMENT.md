# Lancer Néon Bay : nom, prix, site et visibilité

## 1. Le nom : pas de « GTA Free »
Un nom comme « GTA Free », « GT Free » ou tout ce qui fait croire à un jeu Rockstar est une **contrefaçon de marque**. Concrètement :
- Google Play et l'App Store refusent l'application, ou la retirent après une plainte, et peuvent fermer ton compte développeur ;
- Rockstar / Take-Two envoient des mises en demeure et peuvent réclamer l'argent gagné ;
- les plateformes publicitaires (Google Ads, Meta, TikTok) bloquent les pubs qui utilisent la marque d'un autre.

Ce qui est permis : dire que tu proposes des **guides** sur GTA (contenu de fan, clairement non officiel), et décrire ton jeu comme un « jeu d'action en monde ouvert ». Ce qui est interdit : le nom, le logo, la police d'écriture, les personnages ou la jaquette de GTA, et toute phrase qui laisse croire que c'est un GTA.

**Noms possibles** (originaux, faciles à retenir, qui disent le genre) :
- **Néon Bay** (actuel) ; variantes : *Néon Bay : Street Kings*, *Néon Bay : City Rush*
- *Street Empire*, *Crime Coast*, *Night City Kings*, *Block Boss*
Vérifie la disponibilité du nom (store, nom de domaine, et base INPI / EUIPO) avant de le déposer.

## Accroches à utiliser (sans citer GTA)
Dire « la version moins chère de GTA » ou « pour ceux qui ne peuvent pas acheter GTA » laisse croire que Néon Bay est un GTA : c'est faux, et cela utilise leur marque. Utilise plutôt :
- « Le monde ouvert à 2,99 €. »
- « Toute l'action d'un gros jeu de rue, pour le prix d'un café. »
- « Voitures, gangs, police et poursuites. Le niveau 1 est gratuit. »
- « 4 pays, 30 missions, aucun abonnement. »
- « Le jeu d'action qui tourne sur ton téléphone, même sans console. »

## 2. Le prix : gratuit pour essayer, payant pour tout avoir
Le modèle déjà en place dans le jeu est le bon pour un jeu « pas cher mais pas 100 % gratuit » :
- **Niveau 1 gratuit**, sans inscription : les gens essaient, partagent, reviennent.
- **Jeu complet à 2,99 €**, paiement unique (réglé dans `js/data.js`, `SHOP_CONFIG.price`).
- Sur Google Play : même principe avec l'achat intégré `full_game` (voir `ANDROID.md`).
- Sur Poki / CrazyGames : version gratuite payée par la pub (voir `PORTAILS.md`).

Leviers simples :
- **Prix de lancement** à 1,99 € la première semaine, puis 2,99 €.
- **Offre au bon moment** : le jeu propose déjà le jeu complet juste après la victoire au niveau 1.
- **Guide PDF offert contre un email** (Systeme.io) : tu récupères des contacts, puis une séquence de 3 emails présente le jeu.

## 3. Le site de vente (`site/`)
`node tools/build-site.js` fabrique `site/dist/` :
- `index.html` : page de vente (bande-annonce, 4 pays, prix, FAQ, liens vers les guides) ;
- `guides/` : un article par épisode GTA, avec sommaire, encart vers ton jeu et téléchargement PDF ;
- `pdf/` : un PDF par guide + `guide-complet-gta.pdf` ;
- `jouer/` : le jeu jouable en ligne ;
- `sitemap.xml` et `robots.txt` pour Google.

Avant de publier :
1. Mets ton adresse dans `SITE_URL` (variable d'environnement ou en haut de `tools/build-site.js`) et ton lien Systeme.io dans `BUY_URL`.
2. Héberge `site/dist/` (Netlify, Cloudflare Pages ou ton hébergeur Systeme.io).
3. Déclare le site dans **Google Search Console** et envoie le `sitemap.xml`.

## 4. La visibilité, sans payer de pub au début
- **Articles** : les guides visent des recherches très fréquentes (« astuces GTA 5 », « argent GTA San Andreas », « codes GTA Vice City »…). Ajoute un nouvel article par semaine.
- **Vidéos courtes** : `marketing/bande-annonce-verticale.mp4` sur TikTok, Shorts et Reels, puis des extraits de parties (poursuites, explosions, hélicoptère). Le bouton « Photo à partager » du jeu aide les joueurs à poster.
- **Portails de jeux** (Poki, CrazyGames) : des milliers de joueurs gratuits, qui découvrent le nom Néon Bay.
- **Communautés** : Discord, Reddit (r/WebGames, r/IndieGaming), groupes Facebook de joueurs, en respectant les règles de chaque groupe.

## 5. Ce qu'il ne faut pas faire
- Pas de mots-clés « GTA » dans le nom de l'appli, l'icône ou le titre de la fiche store.
- Pas de captures d'écran de vrais jeux GTA sur ton site (droit d'auteur) : utilise les captures de Néon Bay.
- Pas de faux avis, pas de « télécharger GTA gratuit » : c'est trompeur et sanctionné.
