# Néon Bay : audit complet (24 novembre 2026)

Version auditée : branche `ccr-aa948da6-7gw6pi`, build web du 24/11. Méthode :
- captures sur PC, téléphone en paysage et en portrait ;
- audit automatique des chevauchements sur 5 tailles d'écran ;
- test de non-régression des 30 niveaux ;
- relance des testeurs automatiques ;
- lecture du code et des fichiers ;
- comparaison avec la recherche marché (`reports/RECHERCHE-AAA.md`, chaque chiffre y a sa source).

Notes sur 10. **10 = au niveau d'un jeu commercial de sa catégorie (jeu web et mobile)**, pas au niveau de GTA VI.

---

## 1. Résumé en une page

| Domaine | Note | En une phrase |
|---|---|---|
| Interface et mise en page | 7/10 (5 avant aujourd'hui) | Refonte faite aujourd'hui : accueil en deux colonnes, écran Options, panneaux et arrondis cohérents. Restent la carte des niveaux, les icônes et les animations d'entrée. |
| Rendu 3D | 6/10 | Humains Blender animés, voitures PBR, façades détaillées, lumière jour/nuit, ralentis. La caméra de dessus reste la vue par défaut et trahit le côté « jeu web ». |
| Gameplay et équilibrage | 5/10 | Beaucoup de systèmes (police, bateaux, fusée, prison, turbo, alliés). La difficulté reste le risque n° 1 : les testeurs automatiques échouaient en masse avant les corrections du 21/11. |
| Écriture et textes | 5/10 | Missions lisibles et aide sur l'objectif. Pas encore de vraie voix d'auteur : satire, radio, personnages récurrents. |
| Son | 4/10 | Musique et bruitages synthétisés, voix off par pays. Pas de radio, pas d'ambiance de ville riche. |
| Performance et poids | 6/10 | 1,5 Mo de code, mais environ 5 Mo de modèles 3D chargés dès le lancement, et 33 Mo pour la version web complète. |
| Monétisation | 3/10 | Le lien de paiement n'est pas configuré : aujourd'hui, personne ne peut acheter le jeu. |
| Juridique et confidentialité | 4/10 | La politique de confidentialité existe mais contient encore [DATE], [TON NOM], [ADRESSE]. Aucune classification d'âge n'est faite. |
| Accessibilité | 3/10 | Pas de taille de texte réglable, pas de mode daltonien, pas de sous-titres réglables. Les cibles tactiles font 44 px (conforme). |
| Traduction | 7/10 | 4 langues (fr, en, es, pt) et 603 textes suivis. Il manque l'allemand et l'italien, gros marchés pour un jeu à 2,99 €. |
| Distribution | 5/10 | Versions web, portails (Poki, CrazyGames) et Android (TWA) prêtes. Rien n'est publié sur un store. |

**Les 3 blocages qui empêchent de vendre aujourd'hui :**
1. Aucun lien de paiement : `SHOP_CONFIG.buyUrl` est vide dans `js/data.js`. Il faut un compte Stripe, Lemon Squeezy ou Google Play Billing, que seul le propriétaire peut créer.
2. La politique de confidentialité n'est pas remplie : nom de l'éditeur, adresse, email de contact et date.
3. Aucune classification d'âge (IARC sur Google Play, PEGI). Avec des armes, des explosions et la police, il faut s'attendre à un PEGI 16 environ.

---

## 2. Le contexte : qu'est-ce qu'un « jeu à 100 millions » ?

Chiffres sourcés dans `reports/RECHERCHE-AAA.md` :

| Jeu | Budget | Équipe | Durée |
|---|---|---|---|
| GTA V (2013) | ~265 M$ marketing compris (estimation) | plus de 1 000 personnes | ~3 ans de pleine production, 5 au total |
| GTA VI (sorti le 19/11/2026) | non officiel : 1 à 1,5 Md$ estimés, démentis par Rockstar ; ~2,7 à 3 Md$ de salaires chez Rockstar North seul entre 2019 et 2025 | 4 711 salariés chez Rockstar | ~8 ans |
| Red Dead Redemption 2 | 370 à 640 M$ (estimations) | ~1 600 développeurs | 7 à 8 ans |
| Cyberpunk 2077 | ~316 M$, plus ~120 M$ après la sortie | — | ~8 ans |
| Clair Obscur : Expedition 33 | moins de 10 M$ | ~30 personnes | ~5 ans |
| Shakedown : Hawaii / Retro City Rampage | non publié | 1 personne | plusieurs années |

**Ce que veut dire 100 M$ en pratique** : environ 300 personnes pendant 3 ans (à ~110 k$ par personne et par an, charges comprises), puis autant en marketing. Le marketing représente 75 à 100 % du coût de développement dans un AAA.

**Conclusion honnête.** Néon Bay ne peut pas rivaliser avec GTA VI en volume : 600 000 animations, 1 200 acteurs, une ville faite à la main. Il peut en revanche **paraître premium dans sa catégorie**, celle du jeu de crime jouable dans le navigateur et sur téléphone. C'est la catégorie de Shakedown : Hawaii, et elle n'a pas de leader moderne. Les leviers les moins chers pour « paraître cher » sont, dans l'ordre :
1. une interface cohérente (fait aujourd'hui) ;
2. l'éclairage et le post-traitement (en grande partie fait) ;
3. le ressenti des commandes et les effets (fait en partie) ;
4. le son et une radio satirique (à faire) ;
5. les 30 premières secondes de jeu et les captures pour les stores (à faire).

---

## 3. Interface et mise en page

### Fait aujourd'hui
- **Système visuel unique :**
  - 3 rayons d'arrondi (10, 16 et 24 px) ;
  - des panneaux « verre » dégradés avec un liseré clair en haut ;
  - des ombres et un léger relief au survol ;
  - des transitions de 180 à 200 ms avec ralenti en fin de mouvement.
- **Typographie :** la police Bungee est réservée aux grands titres. Chakra Petch, plus lisible, sert pour les boutons, les cartes et les étiquettes. C'était le principal défaut de lisibilité relevé par l'audit.
- **Accueil refait** comme dans un grand jeu :
  - à gauche, le logo, une phrase d'accroche (« 30 nuits. 4 pays. Une fusée. ») et un menu principal de 6 entrées, chacune avec un sous-titre (Jouer/Continuer, Boutique, Succès, Bande-annonce, Options, Jeu complet) ;
  - à droite, la fiche du joueur (argent, niveaux, étoiles, tags), les défis du jour et les langues.
  - Avant, il y avait 7 boutons et 13 réglages en vrac.
- **Nouvel écran Options :** réglages, langue et commandes au clavier, regroupés en sections. L'écran de pause y renvoie au lieu d'afficher ses propres réglages.
- **Onglets de la boutique** sous forme de pastilles (contrôle segmenté).
- **En-tête des écrans** qui reste en haut quand on fait défiler.
- **Message d'achat :** le texte technique destiné au développeur (« SHOP_CONFIG.buyUrl dans js/data.js ») est remplacé par un message pour le joueur, traduit en 4 langues.
- **Flèche d'objectif :** elle ne passe plus sous la boîte d'objectif en haut de l'écran.
- **Flou d'arrière-plan :** il est limité aux menus. Il est retiré du HUD en jeu, car il coûte cher sur les Android d'entrée de gamme.
- **Vérifications :** 0 chevauchement sur les 5 tailles d'écran (petit téléphone, téléphone en paysage, tablette, PC).

### Reste à faire (par priorité)
1. **Carte des niveaux :** donner une vignette illustrée à chaque pays, au lieu de cartes de texte seules. Recommandation : rendre 4 images avec Néon Studio.
2. **Icônes :** les boutons et les onglets n'en ont pas. Un jeu de 20 icônes SVG maison (arme, armure, argent, étoile, police…) changerait beaucoup la perception.
3. **Animations d'entrée en cascade** sur les menus : chaque carte apparaît avec 30 ms de décalage.
4. **HUD contextuel** à la manière de RDR2 : la mini-carte et les jauges s'effacent quand il ne se passe rien, et un mode « photo » sans HUD.
5. **Boutique :** ajouter une image ou une silhouette par arme, comme dans les vitrines des jeux de voiture.
6. **Écran de fin de niveau :** décompte animé de l'argent et des étoiles. C'est le moment le plus partagé en capture.

---

## 4. Rendu 3D

| Point | État |
|---|---|
| Personnages | 4 humains Blender (2 hommes, 2 femmes), animés : marche, course, visée, doigts. Peau et tissus texturés. |
| Véhicules | Voitures PBR (berline, sport, SUV, van), bateaux, hélicoptère, fusée. |
| Villes | Façades à fenêtres, briques et vitrines, auvents, climatiseurs, réservoirs, lampadaires avec flaques de lumière, sol en asphalte détaillé, ombre de contact. |
| Lumière | Cycle jour/nuit, reflets (carte d'environnement), bloom la nuit, étalonnage par pays, ralentis cinéma. |
| Caméra | Vue de dessus par défaut, plus une vue poursuite et une vue embarquée. |

**Faiblesses :**
- La vue de dessus par défaut écrase tout le travail sur les façades et les personnages. **Recommandation :** passer la caméra « poursuite » par défaut sur PC et la garder de dessus sur petit téléphone.
- Les passants se ressemblent : 4 modèles de base. GTA VI a un studio entier consacré aux passants. Visé ici : 8 à 10 silhouettes par la chaîne Blender, et des couleurs de vêtements aléatoires (déjà en place).
- Il n'y a pas d'ombres portées dynamiques pour les personnages en qualité moyenne.

---

## 5. Gameplay et équilibrage

**Systèmes en place :**
- 30 niveaux de 10 étapes dans 4 pays, plus la Lune et Mars ;
- police à étoiles avec voitures, hélicoptère, barrages et garde-côtes ;
- prison et évasion ;
- armes à débloquer gratuitement par défis ;
- armures et entraînement ;
- propriétés qui rapportent ;
- balade libre avec petits boulots ;
- turbo à pied et en voiture ;
- renforts alliés ;
- reprise à l'étape 6 ;
- 5 niveaux de difficulté.

**Testeurs automatiques :** rejoués le 24/11 sur les niveaux 1 à 10, 4 profils, 3 essais par niveau.
- **Avant les corrections du jour,** le joueur moyen mourait dès la 1re étape du niveau 1. Selon le journal des dégâts, la cause était un mélange de voitures qui le renversaient, d'explosions en chaîne et d'hélicoptère de police.
- **Corrections apportées :**
  - une voiture détruite par des chocs brûle 3,5 s avant d'exploser, ce qui supprime les explosions en chaîne ;
  - les dégâts de collision et d'explosion sont adoucis jusqu'au niveau 10 ;
  - pas d'hélicoptère avant le niveau 3 ;
  - le chrono des courses laisse plus de marge au début ;
  - les personnages à protéger sont plus résistants au début.
- **Résultat :**

| Testeur | Niveaux 1 à 10 réussis |
|---|---|
| Tunnelier (sème la police par les tunnels) | 7/10 |
| Débutant prudent | 0 à 2/10 selon les essais |
| Joueur moyen | 0/10 |
| Expert | 0 à 1/10 |

- **Lecture :** jouer « comme le jeu l'explique », c'est-à-dire semer la police par les tunnels, permet d'avancer. Les profils qui se battent avec la police ou qui conduisent mal échouent encore souvent. Les causes principales sont le chrono des courses, les K.O. pendant les ramassages et les destructions, et le chrono de l'atelier.
- **Limites :** les testeurs conduisent et visent moins bien qu'un humain, et les résultats varient beaucoup d'une série à l'autre. **C'est le principal risque restant** : un jeu jugé trop dur dans les 10 premières minutes perd ses joueurs.
- **Prochaines étapes conseillées :**
  - faire jouer 5 vraies personnes au niveau 1 à 3, en les filmant ;
  - mettre la difficulté « Facile » par défaut pour une première partie ;
  - afficher un conseil « prends un tunnel » au premier avis de recherche.

**Recommandations :**
- Garder le test de non-régression des 30 niveaux (`t3`) et la relance des testeurs après chaque modification d'équilibrage.
- Ajouter une **mesure réelle** : enregistrer, sans donnée personnelle, à quelle étape les joueurs abandonnent. C'est la seule façon de savoir si un vrai joueur bloque au même endroit que les testeurs. Il faut alors mettre la politique de confidentialité à jour.

---

## 6. Écriture et textes

**Points forts :**
- objectifs courts et clairs ;
- aide détaillée sur l'objectif (touche I ou bouton « ? ») ;
- 4 langues ;
- voix off par pays ;
- introduction avant le niveau 1.

**Ce qui manque par rapport aux jeux de référence** (GTA V : 69 missions et plus de 150 000 lignes doublées) :
1. **Une voix d'auteur.** La satire de GTA fonctionne parce qu'elle vise un lieu et une époque précis. Il faut choisir pour Néon Bay une cible, par exemple les influenceurs, la crypto et l'immobilier de luxe, et l'appliquer partout : noms des boutiques, publicités, dialogues.
2. **Des personnages récurrents :** un mentor, un rival, un flic corrompu, qui reviennent d'un pays à l'autre avec 2 ou 3 répliques par niveau.
3. **Une structure de mission plus dramatique :** accroche (appel), trajet dialogué, action, retournement, fuite, conclusion. Aujourd'hui les étapes s'enchaînent sans retournement scénarisé.
4. **2 radios satiriques courtes** (5 à 10 minutes chacune) : un animateur, de fausses publicités et de faux flashs info. Elles s'écrivent en interne et se produisent avec une voix de synthèse sous licence commerciale.
5. **Des textes de store** : description courte, description longue, 8 captures avec légende, en 4 langues.

---

## 7. Son

- **Présent :** musique générée, bruitages, voix off par pays.
- **Manquant :**
  - ambiance de ville en couches : circulation, foule, sirènes lointaines, mer ;
  - sons d'interface (survol, validation, achat) ;
  - radio en voiture ;
  - son qui change dans les tunnels et à l'intérieur.
- **Priorité :** les sons d'interface et l'ambiance. C'est ce que le joueur entend en premier.

---

## 8. Performance et poids

| Élément | Taille |
|---|---|
| Code du jeu et bibliothèques 3D | ~1,5 Mo |
| Modèles 3D (.glb) chargés au lancement | ~5,0 Mo (24 fichiers) |
| Bande-annonce dans le jeu | 8,2 Mo (chargée seulement si on la lance) |
| Version web complète (avec doublons de secours en base64) | 33 Mo |
| Version tout-en-un (sans modèles) | 1,25 Mo |

**Recommandations :**
1. **Chargement progressif.** Charger d'abord la voiture du joueur, un humain et le décor, puis le reste en arrière-plan. Les humains pèsent 0,8 Mo chacun.
2. **Compresser les modèles** (quantification ou Draco) : on peut viser −50 à −70 %.
3. **Ne pas livrer les copies base64** (`.glb.js`) avec la version store. Elles ne servent qu'en ouverture locale du fichier.
4. Mesurer la fréquence d'images sur un vrai téléphone Android d'entrée de gamme. Les tests automatiques tournent en rendu logiciel et ne mesurent pas ça.

---

## 9. Monétisation

- **Modèle actuel :** niveau 1 gratuit, puis 2,99 € pour tout le jeu.
- **Problème bloquant :** le paiement n'est pas branché.
- **Ce que dit le marché** (sources dans la recherche) :
  - le jeu payant marche mal sur mobile, même pour Rockstar : le portage payant de Red Dead Redemption a fait environ 10 k ventes en 5 semaines (estimation) ;
  - les jeux de crime gratuits (Gangstar Vegas) font beaucoup de téléchargements mais peu de revenu par joueur.

**Recommandations :**
1. Brancher le paiement : Google Play Billing pour l'app Android (`android/verify-purchase.js` existe déjà), un lien Stripe ou Lemon Squeezy pour le web.
2. **Tester une démo plus longue** : niveaux 1 à 5 gratuits au lieu du seul niveau 1, et mesurer la conversion. Un seul niveau gratuit est souvent trop court pour donner envie.
3. Sur les portails (Poki, CrazyGames), la monétisation se fait par la publicité, gérée par le portail. C'est la voie la plus rapide pour avoir des joueurs.
4. Pas de « pay-to-win ». Les armes restent gratuites par défis, ce qui est un argument marketing.

---

## 10. Juridique, confidentialité, classification

1. **Politique de confidentialité :** remplacer [DATE], [TON NOM OU TA SOCIÉTÉ], [ADRESSE] et [ADRESSE EMAIL] dans `privacy.html`. Le propriétaire doit le faire lui-même : ce sont ses informations.
2. **Classification d'âge :** remplir le questionnaire IARC dans la console Google Play (violence armée, police, explosions). Prévoir PEGI 16 et l'indiquer sur le site.
3. **Originalité :** aucune marque, aucun nom ni aucun visuel de GTA n'est utilisé. Lieux, gangs et personnages sont inventés, et c'est écrit sur l'accueil. À garder ainsi, y compris dans les publicités : ne pas écrire « GTA » dans les titres de store.
4. **Licences :** les modèles 3D sont générés par la chaîne Blender maison (`models/CREDITS.md`). La police vient de Google Fonts (licence libre). Si des voix de synthèse ou de la musique externes sont ajoutées, vérifier qu'elles autorisent un usage commercial.

---

## 11. Accessibilité

| Point | État | Référence |
|---|---|---|
| Cibles tactiles | 44 px | Apple 44 pt, Android 48 dp : **à passer à 48 px sur Android** |
| Taille du texte réglable | absente | XAG 101 de Xbox : jusqu'à 200 % |
| Mode daltonien | absent | les objectifs magenta et cyan sont difficiles à distinguer pour certains joueurs |
| Sous-titres de la voix off | à vérifier : taille et fond | — |
| Réduire les mouvements | partiel : ralentis désactivables | — |
| Aide à la conduite | présente | — |
| Difficulté réglable | 5 niveaux | — |

**À faire :** ajouter dans Options un réglage « Taille du texte » (100 %, 125 %, 150 %), un « Mode daltonien » qui change les couleurs des objectifs et de la police, et « Réduire les tremblements ».

---

## 12. Traduction

- **Langues :** français, anglais, espagnol et portugais, avec 603 textes suivis dans `i18n/strings-fr.json`.
- Les nouveaux textes de l'interface d'aujourd'hui ont été traduits.
- **À faire :**
  - ajouter l'allemand et l'italien (gros marchés européens) ;
  - faire relire par des natifs, au moins l'anglais et le portugais du Brésil ;
  - traduire les textes de store.

---

## 13. Distribution

| Canal | État | Prochaine étape |
|---|---|---|
| Web (site) | build prêt (`dist-web`) | héberger et brancher le paiement |
| Poki / CrazyGames | builds prêts (`dist-portal`) | soumettre ; la publicité est gérée par le portail |
| Google Play | TWA préparée (`android/`) | compte développeur (25 $), fiche, captures, classification, paiement |
| App Store | non préparé | demande un Mac ou un service de build et un compte développeur Apple (99 $/an) |

**Calendrier :** GTA VI est sorti le 19/11. Selon Sensor Tower, les autres jeux perdent plus de 10 % de joueurs quotidiens dans le mois qui suit. Mieux vaut lancer les actions marketing fin décembre ou en janvier, avec l'angle « crime en monde ouvert, jouable gratuitement dans le navigateur ».

---

## 14. Production : moyens réalistes

| Scénario | Équipe | Budget indicatif | Durée | Ce qu'on obtient |
|---|---|---|---|---|
| A. Actuel | 1 personne + Claude (code, 3D Blender, studio vidéo, testeurs automatiques) | quelques centaines à quelques milliers d'euros par an : comptes stores, nom de domaine, voix et musique sous licence, tests publicitaires | continu | Un jeu web et mobile soigné dans sa catégorie. Publication possible dès que le paiement et la fiche légale sont faits. |
| B. Petit studio | 5 à 8 personnes : direction artistique, 3D, son, écriture, test qualité, marketing | ~0,6 à 1,2 M€ (salaires français chargés) | 18 mois | Néon Bay 2 en vue à la 3e personne, doublage pro, radios, 8 à 10 heures de jeu. |
| C. Modèle Clair Obscur | ~30 personnes + sous-traitance | ~8 à 10 M€ | 3 à 5 ans | Jeu PC et console sous Unreal Engine, direction artistique forte. |
| D. AAA « 100 M$ » | ~300 personnes | ~100 M$ de dev + ~100 M$ de marketing | 3 à 4 ans | Nécessite un éditeur ou un financement de type capital-risque. |

**Recommandation :** faire réussir le scénario A (sortie, premières ventes, chiffres de rétention). C'est la preuve qu'il faut pour financer le scénario B.

---

## 15. Plan d'action par priorité

### P0 : bloquant pour vendre (à faire par le propriétaire, je ne peux pas le faire à sa place)
1. Créer le compte de paiement et coller le lien dans `SHOP_CONFIG.buyUrl` (`js/data.js`), ou me le donner pour que je l'intègre. **Ne pas coller de clé secrète dans la conversation**, seulement le lien de paiement public.
2. Remplir l'identité de l'éditeur dans `privacy.html`.
3. Ouvrir le compte Google Play et remplir le questionnaire de classification.

### P1 : qualité perçue (je peux le faire)
1. Vignettes illustrées des pays et des armes, et icônes SVG.
2. Caméra poursuite par défaut sur PC.
3. Sons d'interface et ambiance de ville.
4. Réglages d'accessibilité : taille du texte, mode daltonien.
5. Chargement progressif et compression des modèles.
6. Démo de 5 niveaux gratuits (si le propriétaire est d'accord).

### P2 : profondeur
1. Personnages récurrents et retournements scénarisés.
2. 2 radios satiriques.
3. Allemand et italien.
4. Écran de fin de niveau animé et mode photo.
5. 8 à 10 silhouettes de passants.
