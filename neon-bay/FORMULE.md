# Néon Bay : la formule d'un jeu de crime en monde ouvert

> Document de travail **interne**. Il analyse les principes de design d'une série célèbre pour en tirer des leçons. **Ne le publie pas tel quel** sur le site ni dans une fiche de store : les noms de cette série sont des marques déposées (voir `LANCEMENT.md`). On n'en reprend **aucun** nom, personnage, carte, texte, musique ni image : seulement des principes de jeu, qui ne sont pas protégeables.

Sommaire
1. Ce qui a fait le succès de la série, épisode par épisode
2. La formule appliquée à Néon Bay (tableau)
3. Le réalisme atteignable sur un téléphone, honnêtement
4. Viralité, vente et rétention saine
5. Feuille de route en 3 vagues, et ce qu'un vrai budget changerait
6. Sources

---

## 1. Ce qui a fait le succès de la série

### 1.1 Les épisodes en bref

| Épisode | Année | Ce qu'il a apporté | Leçon pour nous |
|---|---|---|---|
| **GTA (1)** | 1997, vue de dessus | Né d'un projet où l'on jouait un **policier** (« Race'n'Chase ») jugé ennuyeux ; l'équipe a inversé les rôles. Un bug rendait les voitures de police « folles » (elles essayaient de passer à travers le joueur) : il a été gardé, et la poursuite est devenue le cœur du jeu. Missions prises à des **cabines téléphoniques** qui sonnent, dans l'ordre qu'on veut. Objectif chiffré par niveau (un score à atteindre), **multiplicateur** de gains perdu en cas de mort ou d'arrestation, niveau de recherche à 4 crans. | Le **chaos policier est le spectacle**. Un objectif de score clair suffit à donner du sens à la liberté. Une petite perte en cas d'échec rend chaque course tendue. |
| **GTA 2** | 1999, vue de dessus | **Jauges de respect** pour trois gangs par quartier : travailler pour un gang fâche ses rivaux, qui deviennent hostiles et ferment leurs missions. Un gang ami peut même te protéger de la police. Sauvegarde payante (à l'église du départ). | Les **choix de camp** créent de la rejouabilité sans écrire plus d'histoire. La sauvegarde payante est un « puits » d'argent intelligent. |
| **GTA III** | 2001, passage en 3D | Ville entière en 3D chargée en continu, déblocage des quartiers au fil de l'histoire, missions données par plusieurs commanditaires, étoiles de recherche jusqu'à 6, **radio** complète (pubs, jingles, une station 100 % parlée) qui porte la satire. Idée directrice des créateurs : une ville « vivante », un lieu où l'on vit plutôt qu'un niveau qu'on traverse ; « l'histoire sert à montrer les mécaniques, et les mécaniques servent à raconter l'histoire ». | La **ville est le personnage principal**. La radio est le moyen le moins cher de donner une âme et de l'humour à un monde. |
| **Vice City** | 2002 | Une époque marquée (années 80) et une **identité visuelle et musicale** forte. **Achat de propriétés** : planques (sauvegarde, garage) et **commerces** qui, après une courte série de missions, rapportent un revenu régulier. Trois fois plus de radio parlée que l'épisode précédent. | Les **propriétés** donnent un but à l'argent et une sensation d'empire qui grandit. L'ambiance (couleurs, musique) vend autant que les mécaniques. |
| **San Andreas** | 2004 | Trois villes et de la campagne (environ 4 à 6 fois la carte précédente). **Couche de jeu de rôle** : endurance, muscles, poids, capacité pulmonaire, compétences de conduite et de tir qui montent **en pratiquant**. **Guerres de territoires** : on prend un quartier en survivant à trois vagues, puis il faut le défendre contre des contre-attaques. Respect qui dépend des actes et de l'apparence. Petits boulots à volonté (taxi, pompier, ambulancier, justicier), salles de sport, mode deux joueurs. | « **Tu deviens meilleur à ce que tu fais** » est une boucle de progression très forte. Une carte qui **change de couleur** selon ce que tu contrôles est une récompense visible en permanence. |
| **GTA IV** | 2008 | Ton plus sombre et réaliste, physique des corps et des voitures beaucoup plus crédible (moteur maison + animation procédurale), **système de couverture**, téléphone portable comme menu, amis et sorties. Recherche par **zone circulaire** : il faut sortir d'un cercle autour du dernier endroit où on t'a vu, cercle qui grandit avec les étoiles. Choix moraux qui changent la fin. Note critique très haute, mais certains joueurs ont trouvé les activités annexes là « pour remplir ». | Le **poids physique** (voitures qui tanguent, corps qui tombent) rend chaque collision mémorable. Le cercle de recherche rend la fuite **lisible**. Les activités annexes doivent avoir un intérêt, pas seulement exister. |
| **GTA V** | 2013 | **Trois héros** entre lesquels on bascule à volonté, chacun avec un pouvoir spécial (ralenti en combat, ralenti en conduite, rage). Histoire construite autour de **casses** : préparation, choix d'approche (discrète ou bruyante), choix d'équipiers qui prennent une part du butin et progressent. Recherche fondée sur la **ligne de vue** : la police fouille la zone, l'indicateur grise quand tu es caché, et tout recommence si un agent te voit. Énormément d'activités (bourse, sport, propriétés, personnalisation). Mode en ligne qui a prolongé le jeu pendant des années. | Les **casses en plusieurs temps avec un choix d'approche** sont la meilleure structure de mission de la série. La **cachette lisible** (« on ne te voit plus ») est un mini-jeu de cache-cache très satisfaisant. |

Chiffres utiles pour mesurer l'ampleur : le premier épisode 3D a été fait par environ 23 personnes au cœur de l'équipe ; le cinquième a coûté, selon les estimations, plus de 265 millions de dollars (développement + marketing). **Néon Bay ne joue pas dans cette catégorie et ne doit pas essayer** : il doit reprendre les principes qui coûtent peu (systèmes, rythme, humour) et laisser de côté ce qui coûte des millions (doublage de centaines de personnages, villes photoréalistes).

### 1.2 Les mécaniques qui reviennent à chaque épisode

**1. La boucle de jeu.**
`mission → argent → équipement / propriété → mission plus dure`, avec entre deux missions une **liberté totale** (rouler, explorer, faire des bêtises). Ce temps « entre les missions » est essentiel : les critiques expliquent que ce sont les moments calmes qui donnent sa longévité au jeu, et que les meilleures histoires sont celles que le joueur crée lui-même.

**2. Le niveau de recherche (les étoiles).**
C'est le système le plus copié du genre. Il a trois qualités :
- il est **provoqué par le joueur** (on choisit de faire une bêtise) ;
- il **monte par paliers lisibles** (plus d'agents, puis barrages, puis hélicoptère, puis forces spéciales) ;
- il offre **plusieurs sorties** (se cacher, changer de voiture/peinture, sortir de la zone, payer).
Il a évolué : score de notoriété (1997) → étoiles (2001) → cercle de recherche (2008) → ligne de vue (2013). Chaque fois, l'objectif était que le joueur **comprenne** pourquoi il est encore recherché.

**3. La progression.**
- Argent : sert à l'équipement, puis aux propriétés (à partir de 2002), qui rapportent à leur tour.
- Compétences par la pratique (2004) : conduire améliore la conduite, tirer améliore le tir.
- Territoire (1999 et 2004) : la carte affiche ce que tu contrôles.
- Déblocage géographique : nouveaux quartiers ou villes au fil de l'histoire.

**4. La structure des missions.**
Courtes missions (5 à 15 minutes) avec un commanditaire, souvent **un seul objectif principal + un rebondissement** (« la livraison était un piège »). Variété de verbes : conduire, tirer, suivre, escorter, fuir, voler, chronométré. À partir de 2013 : missions en plusieurs phases avec préparation et choix.

**5. La radio et la satire.**
Stations par genre musical, animateurs, fausses publicités, flashs d'info qui parlent parfois de **ce que le joueur vient de faire**. Cible : la société de consommation, les puissants, les médias. C'est une satire « qui tape sur tout le monde ». Revers : plusieurs critiques reprochent à certains épisodes des clichés racistes et misogynes. **Leçon : on garde l'humour sur les institutions et la pub, on évite de rire de groupes réels.**

**6. Liberté / bac à sable.**
La ville réagit : les piétons fuient, la circulation panique, la police arrive. Le joueur peut **combiner les systèmes** (voler un camion, l'utiliser pour bloquer une route, faire exploser une voiture pour semer un poursuivant). Un créateur de la série résumait en 2008 : « le comportement émergent, encouragez-le ».

**7. Les personnages.**
Héros muet en 2001, puis héros avec une voix et un passé (2002 à 2008), puis trois héros en 2013. Les personnages secondaires sont des **caricatures fortes** reconnaissables en deux répliques (le patron paranoïaque, l'ami qui a toujours une mauvaise idée).

**8. Le rythme des cinématiques.**
Une scène courte (30 secondes à 2 minutes) qui **donne l'objectif et une blague**, puis le jeu. Les dialogues continuent **pendant la conduite** (le passager parle pendant le trajet) : l'histoire avance sans arrêter l'action. C'est l'astuce la plus rentable à reprendre.

---

## 2. La formule appliquée à Néon Bay

État constaté en lisant `js/data.js` et `js/engine.js` (aucun code modifié).

| Mécanique | État actuel dans Néon Bay | Ce qu'il manque | Priorité |
|---|---|---|---|
| **Poursuite policière** | Très bonne base : étoiles 1 à 5, barrages à 3 étoiles, hélicoptère à 4 étoiles, arrestation si on reste immobile près d'un agent, police semée après quelques secondes hors de vue, 3 sorties (tunnel, atelier de peinture, pot-de-vin). | Rendre la cachette **lisible** : afficher « hors de vue » + une jauge qui se remplit (aujourd'hui le compteur `unseen` est invisible). Ajouter un palier 5 étoiles distinct (unité spéciale, blindés légers). | **Haute** |
| **Équilibre des sorties de poursuite** | Pot-de-vin : `étoiles × (250 + 120 × niveau)` ; peinture : `200 + 60 × niveau`. Au niveau 30 avec 3 étoiles : pot-de-vin 11 550 $ contre peinture 2 000 $. | La peinture est **toujours** le meilleur choix, dès le niveau 1. Voir tableau 2.1. | Moyenne |
| **Boucle mission → argent → boutique** | Présente : gains par étape `100 + 60n`, bonus de niveau `1000 + 800n`, 7 armes, 3 armures, perks, tenues. | **L'argent perd son sens à mi-parcours** : voir 2.2. Il manque un but à long terme (propriétés). | **Haute** |
| **Liberté entre les missions** | Absente : chaque niveau enchaîne 10 étapes, puis écran de résultat. La ville n'existe que pendant une mission. | Un **mode balade** par pays (ville ouverte sans chrono) avec petits boulots, tags, défis, propriétés. C'est la différence n° 1 avec la référence. | **Haute** |
| **Propriétés / empire** | Absent. | Planques et commerces achetables par pays, qui rapportent un revenu **plafonné** et servent de point de départ. | **Haute** |
| **Territoires / respect** | Deux factions par pays, purement décoratives (les deux sont ennemies). | Carte des quartiers colorée selon la faction qui les tient ; choisir son allié dans certains niveaux (mission différente selon le camp). | Moyenne |
| **Compétences par la pratique** | Absent (seules les armes s'achètent). | 3 jauges simples : Conduite (nitro plus long, meilleure tenue), Tir (moins de dispersion), Endurance (sprint). Montent en jouant, plafonnées. | Moyenne |
| **Structure des missions** | 15 types d'étapes variés, ordre fixe par niveau, histoire en 2 lignes par niveau, cinématique d'intro et d'apparition du boss. | Pas de **rebondissement** scénarisé ; pas de **point de reprise** : un échec à l'étape 9 fait tout recommencer (jusqu'à 12 min perdues au niveau 30). Pas de choix d'approche. | **Haute** (reprise), Moyenne (rebondissements) |
| **Durée de session** | Temps de référence `360 + 12n` secondes : 6 min au niveau 1, 12 min au niveau 30. | Trop long pour le mobile en fin de jeu (cible 3 à 8 min par « morceau »). Le point de reprise à l'étape 5 coupe naturellement en deux sessions. | **Haute** |
| **Radio et satire** | 6 stations originales générées (synth, trap, dembow, funk, lo-fi, coupée), station par défaut selon le pays. | Aucune **voix**, aucune pub parodique, aucun flash info. Ajouter des **cartons texte** façon flash info qui commentent les actes du joueur (« un conducteur repeint sa voiture en 4 secondes : la police s'interroge »). | Moyenne |
| **Personnages** | Fil rouge : cousin Dre, MC Ozone, il Consigliere, Rosa la pilote, DJ Favelinha ; 8 boss nommés. | Ils n'apparaissent que dans le texte d'intro. Leur donner un **portrait** et **3 répliques pendant les trajets** (bulle en bas de l'écran). | Moyenne |
| **Cinématiques** | Intro 7 s (3 s en rejouant), apparition du boss 2,6 s. Bon rythme pour mobile. | Ajouter une **cinématique de fin de pays** (20 s, images fixes + texte) et des dialogues pendant la conduite. | Basse |
| **Réactions de la ville** | Piétons qui fuient, circulation qui panique, pluie qui fait glisser, cycle jour/nuit par niveau. | Bon niveau pour le support. Ajouter des petites scènes de rue (vendeur ambulant, match de foot) en mode balade. | Basse |
| **Défis quotidiens / succès** | 3 défis du jour, série de jours (bonus plafonné à +1 000 $), 18 succès, 12 tags secrets par pays, notes 1 à 3 étoiles par niveau. | Très bien. Ajouter un **défi de la semaine** commun à tous (même graine) pour un classement. | Moyenne |
| **Partage** | Bouton « Photo à partager » (partage natif ou téléchargement). | Pas de **replay** ni de clip vidéo. Voir partie 4. | **Haute** |
| **Santé du joueur** | Alerte pause chaque heure de jeu continu, pas de pub ni loot box dans la version payante. | Garder. Ajouter un récapitulatif de temps de jeu hebdomadaire dans les options (sans culpabiliser). | Basse |

### 2.1 Équilibrage des sorties de poursuite (avant / après)

Objectif : que les trois sorties aient chacune leur intérêt. Tunnel = gratuit mais il faut l'atteindre ; peinture = moyen, mais il faut une voiture et un atelier ; pot-de-vin = cher mais instantané.

| Situation | Pot-de-vin avant | Peinture avant | Peinture **après** proposée |
|---|---|---|---|
| Niveau 5, 2 étoiles | 1 700 $ | 500 $ | (150 + 40 × 5) × 2 = **700 $** |
| Niveau 15, 3 étoiles | 6 150 $ | 1 100 $ | (150 + 40 × n) × étoiles = **2 250 $** |
| Niveau 30, 4 étoiles | 15 400 $ | 2 000 $ | **5 400 $** |

Formule proposée pour la peinture : `(150 + 40 × niveau) × étoiles`, et **interdite à 5 étoiles** (« l'atelier a fermé ses volets »). Effet attendu : à faible recherche, la peinture reste la solution maline ; à forte recherche, le joueur doit vraiment fuir ou payer cher, ce qui crée les moments de tension qu'on veut filmer.

### 2.2 L'économie : l'argent n'a plus de but après le niveau 16

Gains garantis par niveau = 10 étapes × `(100 + 60n)` + `(1000 + 800n)` = **`2000 + 1400n`** (hors argent ramassé, défis, succès, tags).

| Repère | Gains garantis cumulés |
|---|---|
| Fin de Néon Bay (niveau 8) | 66 400 $ |
| Fin de Porto Lumi (niveau 16) | 222 400 $ |
| Fin du jeu (niveau 30) | 711 000 $ |

Tout ce qui s'achète de façon permanente : armes 129 500 $, armures et perks environ 52 000 $, tenues environ 55 000 $, soit **environ 236 000 $**. Le joueur peut donc **tout posséder vers le niveau 16-17** ; ensuite, les 500 000 $ restants ne servent qu'aux consommables. C'est le moment où la motivation baisse, juste au milieu du jeu payant.

Proposition : ajouter des **propriétés** (un puits d'argent qui rapporte un peu) et quelques achats de prestige en fin de jeu.

| Propriété (exemple Néon Bay) | Prix | Débloquée au niveau | Effet | Revenu |
|---|---|---|---|---|
| Planque du port | 8 000 $ | 2 | Point de départ du niveau + garage (garder 1 voiture) | — |
| Station de lavage | 20 000 $ | 4 | Peinture à −50 % dans ce pays | 400 $ par niveau joué |
| Club néon | 45 000 $ | 6 | Débloque une station de radio bonus | 900 $ par niveau joué |
| Studio d'enregistrement | 70 000 $ | 8 | Tenue exclusive + succès « Producteur » | 1 400 $ par niveau joué |

(4 propriétés par pays, prix × 1,25 à chaque pays : ≈ 143 000 $, 179 000 $, 223 000 $ puis 279 000 $, soit ≈ 820 000 $ au total. C'est volontairement un peu plus que les gains garantis : tout posséder demande de viser les 3 étoiles, les défis et les tags, ce qui donne une raison de rejouer sans rien imposer.)

Règles importantes :
- Revenu versé **à la fin d'un niveau joué**, jamais en temps réel hors ligne : **aucune incitation à revenir à heure fixe** (c'est un mécanisme de rétention malsain des jeux gratuits).
- Revenu plafonné : une propriété est rentabilisée en 15 à 25 niveaux, pas en 3.
- Ajout de 2 achats de prestige : voiture dorée personnelle (150 000 $, niveau 20) et hélicoptère de balade en mode libre (250 000 $, niveau 26).

Effet attendu : la deuxième moitié du jeu garde un objectif d'argent clair, et la carte de chaque pays se « remplit » de lieux à toi, comme un empire qui grandit.

### 2.3 Point de reprise et durée de session (avant / après)

| | Avant | Après proposé |
|---|---|---|
| Échec à l'étape 8, niveau 25 | Recommencer à l'étape 1 (environ 8 min perdues) | Reprendre à l'étape 6 (point de reprise après l'étape 5), argent des étapes 1-5 conservé |
| Coût du point de reprise | — | Gratuit la 1re fois ; ensuite 10 % des gains du niveau (puits d'argent doux) |
| Note 3 étoiles | Temps total < `360 + 12n` s | Inchangée, mais **impossible** si on a utilisé le point de reprise (le défi reste pour les bons joueurs) |
| Session typique | 6 à 12 min | **3 à 6 min par moitié de niveau** |

Effet attendu : beaucoup moins d'abandons en fin de jeu, et un niveau qui se joue en deux sessions de transport en commun.

---

## 3. Le réalisme atteignable sur un téléphone, honnêtement

Néon Bay tourne en three.js dans un navigateur, sur des téléphones parfois d'entrée de gamme, avec un poids total d'environ 1,6 Mo. Voici ce qui est **réaliste** et ce qui **ne l'est pas**.

### 3.1 Rendu (ce qu'on voit)
**Possible et déjà en partie fait** : villes générées avec immeubles en instances, néons, cycle jour/nuit, pluie, ombres et post-traitement en qualité haute, plusieurs caméras.

**Atteignable en plus** :
- Un **style assumé** plutôt que le photoréalisme : contours légers, couleurs saturées, néons qui « bavent » (bloom), reflets simples sur route mouillée (texture d'environnement fixe). Un style cohérent vieillit mieux et paraît plus « pro » qu'un réalisme raté.
- Des **niveaux de détail** (bâtiments lointains simplifiés) pour garder 30 images/s sur un téléphone moyen.
- Des **décalcomanies** (traces de pneus, impacts, brûlures) : peu coûteuses et très parlantes.

**Pas réaliste** : éclairage global en temps réel, villes détaillées façon console, foules de centaines de piétons, intérieurs de bâtiments partout. Il faut viser « un beau jeu mobile stylisé », pas « une console dans le navigateur ».

### 3.2 Animation
**Aujourd'hui** : personnages en formes simples avec articulations animées par le code, et un modèle robot animé en `.glb`.

**Atteignable** : 2 ou 3 modèles humains low-poly (moins de 3 000 triangles) **partagés** par tous les personnages, couleurs et accessoires changés par le code, avec 10 à 15 animations (marcher, courir, viser, tomber, monter en voiture). Une **chute physique simplifiée** (ragdoll à 6 articulations) quand un personnage est mis K.O. donne la moitié de « l'effet physique » des grosses productions pour un coût faible. Animations libres de droits disponibles (Mixamo, packs CC0) ; vérifier chaque licence.

**Pas réaliste sans budget** : capture de mouvement, animations faciales, synchronisation labiale.

### 3.3 Intelligence artificielle
**Aujourd'hui, c'est un point fort** : ennemis qui cherchent un abri, sortent pour tirer, contournent ; grenades dès le niveau 8 ; police qui suit le quadrillage des rues ; barrages ; hélicoptère ; limite de 4 tireurs simultanés (bon pour la lisibilité).

**Atteignable** :
- Police qui **fouille** : quand tu es hors de vue, les voitures vont au dernier endroit où on t'a vu, puis quadrillent autour (comme les épisodes récents). Gros gain de crédibilité, peu de code.
- Piétons avec 3 ou 4 comportements de plus (téléphoner/filmer la scène, appeler la police, applaudir une cascade).
- Gangs de la faction alliée qui **aident** en mode balade.

**Pas réaliste** : vie quotidienne simulée de chaque habitant, circulation dense avec respect des feux sur toute la ville.

### 3.4 Son
**Aujourd'hui** : tout est généré par le code (musiques par pays, tirs, explosions, radio), avec son spatial gauche/droite et possibilité de remplacer par des fichiers (`AUDIO.md`).

**Atteignable** :
- **Mélange dynamique** : la musique monte en intensité avec les étoiles (le crochet `setIntensity` existe déjà dans le code).
- Une banque de **20 à 40 sons enregistrés** libres de droits (moteurs, freins, portières, sirènes) : c'est souvent là que le « réalisme » se joue le plus, bien plus que dans l'image.
- Des **voix courtes sans texte** (exclamations, « Hé ! », rires) enregistrées par des amis ou des comédiens à petit prix : 50 à 100 fichiers suffisent.

**Pas réaliste sans budget** : dialogues doublés de toute l'histoire, radios parlées de plusieurs heures.

**Conclusion honnête** : Néon Bay peut devenir un **très bon jeu d'action mobile stylisé**, nerveux et drôle. Il ne ressemblera jamais à une superproduction sur console, et la communication ne doit jamais le laisser croire (déception = mauvais avis = ventes perdues).

---

## 4. Viralité, vente et rétention saine

### 4.1 Les moments partageables (à fabriquer exprès)
Les vidéos qui marchent sur TikTok, Shorts et Reels font **moins de 15 secondes** et montrent **un moment absurde ou spectaculaire** compréhensible sans le son. Le jeu en produit déjà : explosion de convoi, hélicoptère abattu, fuite par le tunnel, voiture repeinte sous le nez de la police.

À ajouter :
1. **Replay automatique des 10 dernières secondes** : le jeu garde en mémoire les positions (voitures, personnages, explosions) des 10 dernières secondes, ce qui est léger, et peut les rejouer au ralenti avec une caméra cinéma. Bouton « Revoir » après une explosion, un boss ou un échec spectaculaire.
2. **Export du replay en vidéo verticale** (enregistrement du canevas, format 9:16) avec le logo Néon Bay et l'adresse du jeu en bas. Faisable dans les navigateurs récents ; prévoir un repli « photo » si le téléphone ne le permet pas.
3. **Mode photo** : pause, caméra libre, 4 filtres (néon, polaroid, noir et blanc, VHS), masquer l'interface.
4. **Cascades notées** : saut, tonneau, « presque raté » entre deux voitures, affichés avec un score (« Cascade x3 ! »). C'est exactement le genre de chose que les joueurs filment.
5. **Écran de fin de niveau partageable** : carte avec temps, étoiles, K.O., explosions, au format carré, prête à poster.

### 4.2 Défis et classements (sans compte obligatoire)
- **Défi de la semaine** identique pour tous (même graine aléatoire) : « Course de Porto Lumi », « Survie à 5 étoiles ». Classement par pseudo seulement, sans adresse email, sans photo.
- **Code de défi** : un joueur partage un code (par exemple `NB-7Q4K`) qui recrée exactement son défi ; son ami tente de battre le temps. Viral, et ne demande aucun serveur.
- Pas de classement global sur l'argent gagné (pousse au « grind »), uniquement sur l'adresse (temps, cascades).

### 4.3 Prix et modèle
Le modèle actuel est sain et doit être gardé : **niveau 1 gratuit, jeu complet à 2,99 € en une fois**, pas d'abonnement, pas de monnaie premium, pas de coffre aléatoire.

| Levier | Proposition | Effet attendu |
|---|---|---|
| Démo | Donner aussi accès au **mode balade de Néon Bay** (sans missions 2-8) | Le joueur goûte la liberté, ce qui est le vrai argument de vente |
| Lancement | 1,99 € la 1re semaine (déjà prévu dans `LANCEMENT.md`) | Avis et bouche-à-oreille plus rapides |
| Après le niveau 1 | L'offre apparaît déjà au bon moment : garder | — |
| Extension | Un 5e pays plus tard à 1,99 € (ou gratuit pour fidéliser) | Revenus récurrents sans mécanique abusive |
| Tarif | Ne pas dépasser 4,99 € sans vrai contenu en plus | Le prix bas est un argument central |

**À ne jamais faire** : boîtes à butin, roues de la fortune, monnaie virtuelle achetable, compte à rebours « offre qui expire dans 10 min », pub forcée dans la version payante, achats faciles pour un enfant sans validation parentale.

### 4.4 Portails (Poki, CrazyGames)
Déjà préparés (`PORTAILS.md`) : version gratuite financée par la publicité, avec pub récompensée facultative pour doubler le bonus. Les conditions ne sont pas publiées de façon uniforme : des sources tierces évoquent chez Poki 100 % des revenus sur le trafic que tu amènes et un partage 50/50 sur le leur, avec une exclusivité web par défaut ; chez CrazyGames, des taux d'environ 60 % sur la pub sont cités dans certaines conditions. **À vérifier directement auprès de chaque portail**, et attention : l'exclusivité web de Poki peut entrer en conflit avec la vente sur ton propre site. Décide avant de signer.

Pour les portails, le jeu doit être **compréhensible en 10 secondes** : le niveau 1 qui démarre directement en voiture avec la police aux trousses est un très bon choix, à garder.

### 4.5 TikTok et vidéos courtes
- Une vidéo par jour pendant 30 jours, toujours le même format : **accroche texte en 1 seconde** (« Il a repeint sa voiture SOUS les yeux de la police »), action, logo à la fin.
- Séries : « 1 pays, 1 minute », « le boss le plus nul », « je vole uniquement des scooters ».
- Utiliser les replays exportés par les joueurs (avec leur accord) comme contenu.
- Ne jamais citer la série de référence dans les titres ou les hashtags (voir `LANCEMENT.md`).

### 4.6 Rétention saine
Ce qui existe déjà est très bien : alerte pause toutes les heures, défis du jour peu nombreux, bonus de série plafonné, rien qui punit l'absence.

À ajouter ou à garder en tête :
- **Récompense de retour** douce : un cadeau modeste (1 000 $) quand on revient après 3 jours ou plus, **jamais** de perte si on ne vient pas.
- La série de jours ne doit **pas** se remettre brutalement à zéro : proposer « un jour de joker par semaine ».
- Pas de notification push insistante (au maximum une par semaine, désactivable).
- Point de reprise à mi-niveau (partie 2.3) : permet de **s'arrêter** sans perdre sa progression, ce qui est l'inverse d'une boucle addictive.

### 4.7 Point d'attention : stéréotypes
Les quatre pays reprennent des clichés forts (mafia italienne, cartels colombiens, gangs des favelas). Le ton cartoon aide, mais pour éviter les critiques (et les refus de portails) :
- montrer dans chaque pays des **habitants ordinaires sympathiques** (commerçants, musiciens, pêcheurs) et des alliés locaux positifs, comme Rosa ou Nonna Lia ;
- faire porter la satire sur les **puissants et les institutions** (préfet corrompu, colonel acheté, promoteur immobilier), pas sur les habitants ;
- ne jamais associer la criminalité à une couleur de peau ou à une origine dans les dialogues ou la radio.

---

## 5. Feuille de route priorisée

### Vague 1 : la semaine qui vient (réglages et petits ajouts, sans nouvel asset)
| # | Tâche | Pourquoi |
|---|---|---|
| 1 | **Point de reprise après l'étape 5** (partie 2.3) | Moins d'abandons, sessions mobiles de 3 à 6 min |
| 2 | **Jauge « hors de vue »** visible pendant une poursuite | La fuite devient lisible et satisfaisante |
| 3 | Rééquilibrer la **peinture** (partie 2.1) | Les trois sorties redeviennent intéressantes |
| 4 | **Écran de fin partageable** (carte carrée avec stats) | Premier levier de viralité, très simple |
| 5 | Faire tester les 30 niveaux par 5 joueurs et noter **où ils abandonnent** | Régler la difficulté sur des faits |

### Vague 2 : le mois qui vient (nouvelles mécaniques)
| # | Tâche | Pourquoi |
|---|---|---|
| 1 | **Mode balade** par pays débloqué (Néon Bay jouable dans la démo) | Le cœur de la formule : la liberté |
| 2 | **Propriétés** (4 par pays, partie 2.2) | Donne un but à l'argent après le niveau 16 |
| 3 | **Replay des 10 dernières secondes** + mode photo | Contenu partageable sur les réseaux |
| 4 | **Police qui fouille** le dernier endroit connu | Crédibilité, tension |
| 5 | Dialogues en bulles **pendant les trajets** (3 répliques par niveau) | Les personnages existent enfin, sans cinématique |
| 6 | Flashs info texte sur la radio, qui commentent les actes du joueur | Satire et humour à coût presque nul |

### Vague 3 : les 3 mois qui viennent (profondeur et communauté)
| # | Tâche | Pourquoi |
|---|---|---|
| 1 | **Territoires** : carte des quartiers, choix de l'allié dans certains niveaux | Rejouabilité (deux chemins par pays) |
| 2 | **Compétences par la pratique** (conduite, tir, endurance) | Progression ressentie, pas seulement achetée |
| 3 | **Défi de la semaine** + codes de défi entre amis | Retour régulier, viralité sans serveur |
| 4 | **Export vidéo vertical** des replays | Les joueurs font la pub du jeu |
| 5 | **Casses en plusieurs temps** dans les niveaux de boss (repérage, choix discret ou bruyant) | La meilleure structure de mission du genre |
| 6 | Modèles humains low-poly + chute physique simplifiée | Saut visuel le plus visible |
| 7 | Cinématique de fin de chaque pays (images fixes + texte) | Sentiment d'aboutissement |

### Ce qu'un vrai budget changerait

| Budget | Ce qu'on achète | Effet |
|---|---|---|
| **≈ 2 000 à 5 000 €** | 1 artiste 3D indépendant pour 3 modèles humains, 8 voitures et 10 bâtiments repères dans le style néon ; packs de sons pro | Le jeu « a l'air d'un vrai jeu » sur les captures d'écran : meilleure conversion sur les stores et portails |
| **≈ 1 000 à 3 000 €** | **Doublage court** : 5 comédiens, environ 300 répliques courtes (exclamations, répliques de trajet, animateurs radio), en français et en anglais | Personnalité, humour, radio vivante ; énorme gain d'ambiance |
| **≈ 500 à 1 500 €** | **Tests** : 20 à 30 joueurs rémunérés ou une plateforme de test, sur 10 téléphones différents (dont 3 d'entrée de gamme) | Moins de bugs au lancement, difficulté réglée, avis meilleurs |
| **≈ 1 000 à 3 000 €** | Compositeur pour 5 morceaux originaux (un par pays + menu) | Identité sonore mémorable, réutilisable dans toutes les vidéos |
| **≈ 500 à 2 000 €** | Publicité test sur TikTok/Meta (sans la marque de référence) | Mesurer le coût d'un acheteur avant d'investir plus |

Ordre de priorité si l'argent est limité : **1. tests, 2. artiste 3D, 3. doublage court, 4. musique, 5. publicité**. Les tests d'abord, parce qu'un jeu qui plante sur la moitié des téléphones ne se rattrape pas avec de beaux modèles.

---

## 6. Sources

Histoire et mécaniques de la série :
- Wikipedia, *Grand Theft Auto (video game)* : https://en.wikipedia.org/wiki/Grand_Theft_Auto_(video_game)
- Wikipedia, *Grand Theft Auto 2* : https://en.wikipedia.org/wiki/Grand_Theft_Auto_2
- Wikipedia, *Grand Theft Auto III* : https://en.wikipedia.org/wiki/Grand_Theft_Auto_III
- Wikipedia, *Grand Theft Auto: Vice City* : https://en.wikipedia.org/wiki/Grand_Theft_Auto:_Vice_City
- Wikipedia, *Grand Theft Auto: San Andreas* : https://en.wikipedia.org/wiki/Grand_Theft_Auto:_San_Andreas
- Wikipedia, *Grand Theft Auto IV* : https://en.wikipedia.org/wiki/Grand_Theft_Auto_IV
- Wikipedia, *Grand Theft Auto V* : https://en.wikipedia.org/wiki/Grand_Theft_Auto_V
- PC Gamer, sur le bug de la police qui a sauvé le premier épisode : https://www.pcgamer.com/the-original-grand-theft-auto-was-almost-axed-saved-by-psycho-police-car-bug
- GamesRadar, *The making of Grand Theft Auto* : https://www.gamesradar.com/making-of-grand-theft-auto/2
- Wiki de fans, système de respect (GTA 2) : https://gta.wiki/w/Respect
- Wikis de fans, niveaux de recherche (épisodes IV et V) : https://gta.wiki/wiki/Wanted_Level_in_GTA_IV et https://gta.wiki/wiki/Wanted_Level_in_GTA_V
- Sportskeeda, évolution du niveau de recherche : https://www.sportskeeda.com/gta/how-wanted-level-system-changed-gta-franchise-years

Analyses de game design :
- Game Developer, *The History and Theory of Sandbox Gameplay* (S. Breslin) : https://www.gamedeveloper.com/design/the-history-and-theory-of-sandbox-gameplay
- Game Developer, *Magic moments in GTA IV* : https://gamedeveloper.com/game-platforms/analysis-magic-moments-in-i-grand-theft-auto-iv-i-
- Game Developer, *The beautiful mundanity of GTA IV* : https://gamedeveloper.com/game-platforms/opinion-the-beautiful-mundanity-of-i-gta-iv-i-
- Game Developer, GDC 2008, Dave Jones sur le comportement émergent : https://gamedeveloper.com/game-platforms/gdc-dave-jones-talks-i-apb-i-emergent-behavior
- Game Developer, *3 things game designers can learn from GTA V* : https://gamedeveloper.com/game-platforms/3-things-game-designers-can-learn-from-gta-v
- Vice, *GTA III was special because it was mundane* : https://www.vice.com/en/article/grand-theft-auto-iii-was-special-because-it-was-mundane/
- The Ringer, regard critique sur l'épisode III : https://www.theringer.com/2021/10/22/video-games/gta-grand-theft-auto-iii-liberty-city-2001-first-time

Portails web :
- Playgama, comparatif des partages de revenus (source tierce, à vérifier) : https://playgama.com/blog/business-faqs/poki-vs-crazygames-vs-gamedistribution-revenue-share/
- Poki, rapport 2026 sur le jeu web : https://poki.com/blog/state-of-web-gaming-report-2026
- Guide de publication CrazyGames (source tierce) : https://app.cinevva.com/guides/publish-game-crazygames

Note sur la fiabilité : les pages Wikipedia et les articles de presse ont été privilégiés ; les wikis de fans et guides tiers ne servent qu'à des détails de mécanique et sont signalés comme tels. Les montants des budgets (partie 5) sont des ordres de grandeur pour des indépendants en Europe, pas des devis.
