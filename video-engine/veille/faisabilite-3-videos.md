# Faisabilité : 1 short + 2 vidéos longues (10 min)

Mesures faites le 2026-11-03 depuis la session de développement.

| # | Vidéo | Statut |
|---|---|---|
| 1 | Short « France vs Allemagne : l'écart de taux » (59 s) | **Terminé** : `out/spread-france-allemagne-60s-final.mp4`, miniatures, SEO |
| 2 | Longue « Pourquoi ton crédit coûte plus cher » (10 min) | Faisable après adaptation du moteur (format 16:9, chapitres, médias) |
| 3 | Longue « Guerre France-Russie : pouvoir d'achat des ménages ? » (10 min) | Faisable en **scénario d'école**, avec réserves sur les sources et sur le cadrage |

## Ce qui est mesuré

| Ressource | Mesure | Conséquence |
|---|---|---|
| Voix Gemini (compte gratuit) | **10 requêtes par jour et par modèle** (message d'erreur de l'API). 3 modèles testés : 3.8-flash, 3.8-flash-lite, 2.5-flash | Une requête = un chapitre. Une requête de **182 mots a donné 59 s d'audio** (testé). 10 min ≈ 1 500 mots ≈ **9 requêtes** : une vidéo longue = presque tout le quota d'un modèle pour la journée. Deux vidéos = deux jours, ou deux modèles (voix légèrement différentes) |
| Calage voix ↔ scènes | Sur 9 phrases, `silencedetect` trouve 30 pauses (virgules comprises) | Il faut découper chaque chapitre sur les pauses les plus longues ; calage approximatif, à vérifier à l'écoute |
| Rendu | Court de 59 s (1 764 images) : environ 25 min pour 4 cœurs, rendu partagé avec d'autres tâches. 10 min = 18 000 images | ≈ 4 h par vidéo avec les réglages actuels ; ≈ 1,5 à 2 h en 1080p sans grain ni flou (à mesurer). À découper en blocs pour survivre à une coupure de session |
| Disque | 29 Go libres ; le rendu brut d'un short pèse 150 Mo | 10 min brut ≈ 1,5 Go : compresser (CRF) et supprimer les blocs au fur et à mesure |
| 3D / WebGL | WebGL 2 disponible dans le navigateur de rendu | Un globe 3D « vue depuis l'espace » est possible avec la texture Natural Earth (domaine public) |
| Images et vidéos libres | **Bloqués** depuis la session : NASA (images-assets, earthobservatory, visibleearth), Wikimedia, archive.org, Pexels, Pixabay, Unsplash, Openverse, ESA, Mixkit, Google Earth. Seul GitHub passe | Je ne peux pas télécharger de séquences NASA ni d'images Google Earth |
| Sources officielles | BCE, INSEE, AFT, Banque de France, Bundesbank : bloquées. La recherche web fonctionne (presse, courtiers) | Les chiffres de marché restent « à confirmer » ; on s'appuie sur des exemples calculés et des faits historiques sourcés par la presse |
| Crédits | Je ne vois ni votre consommation Claude ni votre facturation Google | Consultez vos réglages d'utilisation. Chaque vidéo longue demande de nombreuses étapes ; l'avancer par phases |

## Médias : ce qui est possible, ce qui ne l'est pas

- **NASA** : les images et vidéos NASA sont en général réutilisables avec mention de la source, hors exceptions (logos, personnes, contenus de tiers). **À télécharger par vous** (images.nasa.gov) et déposer dans `public/media/`. Je ne peux pas les récupérer d'ici.
- **Google Earth** : Google autorise l'usage d'images dans une vidéo sous conditions (mention « Google Earth », ©, données de source), à lire dans les règles d'utilisation de Google. Pas d'API : il faut enregistrer vous-même (par exemple avec Google Earth Studio) puis déposer le fichier. Je ne l'ai pas fait et je n'ai pas relu ces règles depuis la session.
- **Ce que je peux produire moi-même** (aucun droit à vérifier) : globe 3D depuis l'espace avec zoom jusqu'à l'Europe, cartes animées, flux, graphiques, compteurs, schémas de mécanismes.
- **Règle à ajouter** : un fichier `media-manifest.json` où chaque média déposé a sa source, sa licence et sa mention ; `npm test` refuse un média sans licence, et la mention s'affiche à l'écran et dans la description.

## Travaux à faire avant les longues (phase A)

1. **Format 16:9** (1920×1080) : le moteur est vertical (1080×1920) en dur ; remplacer les constantes par la taille de la composition.
2. **Structure longue** : chapitres, intertitres, bandeaux, graphiques, séquences d'images/vidéos déposées (`broll`) avec zoom lent et mention de source.
3. **Voix par chapitre** : une requête par chapitre, découpage sur les pauses, cache par empreinte.
4. **Rendu par blocs** : `--frames` par tranche, assemblage ffmpeg, compression.
5. **Globe 3D** d'ouverture (Natural Earth) pour l'accroche « qui fait réfléchir ».

## Vidéo longue n° 2 (guerre France-Russie) : réserves

- Sujet d'actualité sensible : le traiter comme **scénario d'école** (« et si ? »), jamais comme prédiction, sans alarmisme ni consigne de panique.
- Structure possible : (1) une question qui fait réfléchir en ouverture ; (2) ce que montrent les précédents (choc énergétique de 2022 en Europe, chocs pétroliers des années 1970, économies de guerre du XXe siècle) ; (3) les canaux qui touchent un budget : énergie, alimentation, taux et crédit, épargne, impôts, emploi, dépenses de défense ; (4) exemples chiffrés calculés ; (5) ce qui dépend de l'ampleur du conflit ; (6) gestes d'éducation financière génériques ; (7) avis non-obligation d'achat.
- Chaque fait historique doit passer par `verificateur-faits` ; une source primaire est préférable. Sans accès aux sites officiels, le contrôle reste partiel : à dire dans la vidéo si besoin.

## Ordre conseillé

1. Short : prêt à publier (relire le SEO, régler la case « contenu synthétique »).
2. Phase A (moteur long-format) + essai de 60 s en 16:9 pour valider le rendu.
3. Longue n° 2 « Pourquoi ton crédit coûte plus cher » (sujet le plus solide, facts calculables).
4. Longue n° 3 « Guerre France-Russie », après avoir autorisé les domaines de sources officielles et déposé vos images NASA / Google Earth.
