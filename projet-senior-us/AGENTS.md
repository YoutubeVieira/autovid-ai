# Auto Video Senior (US) — consignes communes aux agents

Ce fichier est lu par **Google Antigravity** (règles de l'espace de travail) et importé par **Claude Code** (`CLAUDE.md`). Toute règle ajoutée ici s'applique aux deux.

## Le produit
Des séances de gym douce sur YouTube pour les **seniors américains (60–85 ans)**. Vidéo 16:9, 1920×1080, 30 i/s. Charte complète : `docs/kit-gym-douce-senior.md` ; version US : `config/brand.json`.

## Langue
- Tout ce qui apparaît à l'écran ou s'entend (textes, voix off, titres, descriptions, sous-titres) est en **anglais américain** : « Rest », « Great job! », « Grab a sturdy chair ».
- Ton chaleureux, simple et rassurant. Phrases courtes. Vouvoiement implicite (« you »), jamais condescendant (pas de « sweetie », pas de « elderly »).
- Les échanges avec l'utilisateur et les notes de travail restent en français.

## Style à l'écran (non négociable)
- Coach **en plein écran**, toujours visible ; ne jamais couvrir le visage, les mains, les pieds ni les articulations utiles.
- **Aucun cadre, panneau ni bandeau permanent.** Les textes sont posés sur la vidéo avec un halo doux.
- Seulement : nom de l'exercice, temps restant, **une** consigne courte (≤ 48 caractères), parfois un encouragement.
- Fondus doux (0,35 à 0,5 s), pas de flash, de zoom brusque, de clignotement ni de bip à chaque seconde.
- Couleurs : vert sauge `#8FB996`, beige `#F6F4EC`, vert olive `#5B725E`, jaune doux `#F6C667` (conseils, avec parcimonie). Polices : Montserrat SemiBold (titres), Inter Medium (consignes), Roboto Mono Medium (chronomètre).

## Sécurité (public senior)
- Chaque exercice debout propose un appui sur une chaise stable ou une variante assise.
- Rappel à l'écran au moins une fois par séance : « Stop if you feel pain, dizziness, or unusual shortness of breath. » (`"safety": true` sur un repos).
- Avertissement médical dans la description YouTube (ajouté automatiquement).
- Ne jamais promettre de résultat médical (« cure », « reverse arthritis »…). On parle d'équilibre, de mobilité, de confort, d'autonomie.

## Outil
`autovideo.py` fait tout le montage (Python + FFmpeg) :
```
python3 autovideo.py plan --minutes 10|20|30 --focus balance|strength|mobility
python3 autovideo.py check  sessions/<slug>.json
python3 autovideo.py still  sessions/<slug>.json --at <secondes>
python3 autovideo.py render sessions/<slug>.json [--preview] [--until S] [--alpha [qtrle|prores]]
```
- Le chronomètre est calculé depuis le début et la fin de chaque segment : ne jamais ajouter de minuteur indépendant.
- Le ton du texte (olive ou blanc) est choisi automatiquement d'après le décor ; forcer avec `"text_tone": "light"|"dark"` sur un segment si une image de contrôle le montre mal lisible.
- Placer le texte à gauche si le coach est à droite : `"text_side": "left"`.

## Fichiers de l'utilisateur (voix off, vidéos du coach, musique)
- Ils vont dans `entrees/<slug>/` : `coach/NN.*`, `voix/NN.*` (ou `voix/complete.*`), `musique.*` — `NN` = numéro du segment affiché par `check` (01 = intro). Mode d'emploi : `entrees/LISEZMOI.md`.
- Copier, ne jamais déplacer ni supprimer les originaux ; ne jamais les committer (ignorés par git).
- Une voix plus longue que son segment est signalée par `check` : ajuster la durée du segment, pas couper la voix.

## Avant de dire qu'une vidéo est prête
1. `check` sans avertissement (ou chaque avertissement justifié).
2. Images de contrôle (`still`) regardées : intro, un exercice avec flèche, un repos avec rappel de sécurité, la fin.
3. Rendu complet terminé ; durée de la vidéo = durée annoncée.
4. Dossiers `out/<slug>/youtube/` et `out/<slug>/capcut/` présents.
5. Ne jamais publier sur YouTube ni téléverser à la place de l'utilisateur.
