---
name: veille-sujets-finance
description: Trouver et classer des idées de vidéos « finance mondiale / géopolitique avec conséquences pour la France » (éducation financière, économie des ménages), neuves ou à refaire depuis une vidéo existante. À utiliser dès qu'on demande une veille, des idées de sujets, « quelle vidéo faire », ou d'adapter une vidéo étrangère à la France.
---

# Veille de sujets : finance mondiale → conséquences pour la France

Chaîne : français, public familial, éducation financière, ton **anti-hype** (pas de panique, pas de promesse de gains). Format : shorts verticaux 60-90 s sur carte animée (voir `video-engine/`), avec chiffres qui défilent.

## Méthode

1. **Cadrer** : période (actualité des 7 jours ? sujet de fond ?) et angle. Sans précision : 8 idées, moitié actualité, moitié intemporelles.
2. **Chercher** (WebSearch / WebFetch). Sources à privilégier, par ordre de fiabilité : Banque de France, INSEE, BCE, Eurostat, Agence France Trésor, Cour des comptes, Légifrance / service-public.fr, OCDE, FMI, BRI, Banque mondiale, Trésor. La presse sert à *repérer* un sujet, jamais à *prouver* un chiffre.
3. **Deux chemins** :
   - **Actualité** : un événement mondial (taux, sanctions, matières premières, dette, monnaie, commerce, énergie) → ce que ça change *pour un foyer français* (prix, crédit, épargne, impôts, emploi).
   - **Refaire** : une vidéo existante (celle d'une chaîne étrangère, par exemple) → extraire la *mécanique* (question d'accroche, enchaînement, effets) et la transposer à un sujet français. Jamais copier le script ni les visuels ; refaire = même structure, autre sujet ou autre angle, texte et sources originaux. Pour analyser la vidéo : skill `analyser-video-reference`.
4. **Noter** chaque idée (0-5) :
   | Critère | Question |
   |---|---|
   | Impact France | un foyer français le ressent-il dans son budget ? |
   | Clarté 60 s | explicable en une chaîne cause → effet de 4 à 6 maillons ? |
   | Visuel | carte, flux, flèche ou gros chiffre à montrer ? |
   | Vérifiable | chiffres et dates trouvables dans une source officielle ? |
   | Accroche | une question qu'on a envie de se poser ? |
   | Différenciation | pas déjà traité mille fois à l'identique ? |
   Score = somme /30. **Pénalités** : −5 si prédiction de marché présentée comme certaine ; −5 si la vidéo pousserait un achat/vente ; −3 si dépend d'un chiffre non confirmé.
5. **Livrer** un tableau classé dans `video-engine/veille/AAAA-MM-JJ-idees.md` : titre-accroche, angle France, chaîne cause→effet en une ligne, visuel envisagé, sources à ouvrir (URL), score, risque. Puis recommander **une** idée et dire pourquoi.

## Garde-fous
- Aucun chiffre dans une idée sans source ouverte pendant la veille ; sinon écrire « à vérifier ».
- Pas de conseil personnalisé d'investissement (AMF) : on explique des mécanismes, on ne dit pas quoi acheter.
- Distinguer **fait** (chiffre daté et sourcé), **estimation** (écart attendu) et **opinion**.
- Écarter les sujets qui reposent sur une rumeur, un document fuité non confirmé, ou une personne privée.
