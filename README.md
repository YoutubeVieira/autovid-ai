# AutoVid AI — monteur vidéo automatique

Tu lui donnes des rushs et une musique, il sort un short 9:16 prêt à poster : coupes calées sur le tempo,
meilleur moment de chaque plan trouvé tout seul, recadrage vertical, titres animés, annotations, filigrane,
CTA et son normalisé à −14 LUFS. Les deux styles fournis sont reconstitués à partir de deux vidéos
virales de sports de combat (voir [docs/analyse-videos.md](docs/analyse-videos.md)).

Tout tourne en local avec **ffmpeg + Python** (numpy, PyYAML, requests). Pas d'After Effects, pas de Premiere.

## Installation
```bash
./scripts/install.sh             # ffmpeg, dépendances Python, modèle de pose, skills (Claude Code + Antigravity)
```

## ⭐⭐ Une vidéo → vidéo longue YouTube + shorts (automate)
```bash
python -m autovid viral roda.mp4 -o projet_roda/ --discipline capoeira --handle @toncompte \
  [--courbe heros|bullet|montage|flash_in|flash_out] [--transition zoom|whip|glitch|flash|mix] [--filtre cine|vif|chaud|froid|nb]
```
Short principal, vidéo longue 16:9 à chapitres (intro + plan, en vrai, analyse + fiche, meilleur moment aux 2/3),
un short par mouvement, plan de publication `a_publier.md`. Correspondance avec CapCut : `docs/capcut-pro.md`.

## Documentaire YouTube (archives libres)
```bash
python -m autovid documentaire "L'affaire Landru" -o doc_landru/ [--plan plan.json] [--minutes 8]
```
Recherche et script par Claude (ou `plan.json`), archives libres de droits trouvées automatiquement (Wikimedia Commons,
Library of Congress, Openverse, Internet Archive) avec licence vérifiée et crédits, voix off, zoom lent, cartes de
dates / lieux / citations, nappe sombre, chapitres, sous-titres, shorts, `a_publier.md`. Règles : skill `documentaire`.

## Clip d'humour, d'animaux ou généré par IA
```bash
python -m autovid fun clip.mp4 -o sorties/fun.mp4 --handle @toncompte --ia \
  --texte "LA DINDE A PRIS/SA REVANCHE" --texte "ELLE A SORTI/LE COUTEAU" --texte "ET ELLE A RAMENÉ/SES AMIS"
```
Moment fort trouvé tout seul (pic de mouvement) : ralenti + zoom, flash, micro-pause, beat phonk et bruitages,
textes en deux lignes (ou écrits par Claude avec `--ai claude`), mention « VIDÉO GÉNÉRÉE PAR IA » avec `--ia`.
Le mode combat, lui, refuse d'analyser un sujet qui n'est pas une vraie personne (`--force` pour passer outre).

## ⭐ Une vidéo → un short prêt à poster
```bash
python -m autovid combat ma_video.mp4 -o sorties/short.mp4 --handle @toncompte [--music m.mp3] [--ai claude]
```
Sans rien d'autre que la vidéo :
1. recadrage 9:16, étalonnage contrasté ;
2. squelette de chaque combattant (MediaPipe) ;
3. détection des coups et nom de la technique (direct, crochet, uppercut, high / middle / low kick, genou) ;
4. accroche, puis pour chaque coup : ralenti → flash + impact → arrêt sur image expliqué → reprise ;
5. silhouette mise en avant, jambe d'appui en orange, chaîne qui frappe en vert néon, cercles sur les articulations,
   angle du genou ou du coude, étiquettes d'anatomie (psoas, quadriceps, triceps…), astuce, barre de progression, grain ;
6. beat généré libre de droits (ou ta musique) + whoosh, impacts, ticks, son d'origine, −14 LUFS ;
7. export 1080p (réseaux), 1440p, 4K (YouTube) ou 8K.

`--ai claude` : Claude regarde les images de chaque coup et réécrit nom, accroche, muscles, placement, risque et voix off.

Chaque rendu écrit aussi :
| fichier | contenu |
|---|---|
| `short.mp4` | sous-titres FR incrustés + pistes FR / PT-BR / EN activables |
| `short.fr.srt`, `.pt.srt`, `.en.srt` | sous-titres à envoyer sur YouTube (PT/EN : traduits par Claude) |
| `short.voix.txt` | le script de la voix off (termes capoeira balisés `[pt]`) |
| `short_youtube.jpg`, `short_cover.jpg` | miniature 1280×720 et couverture 9:16 |
| `short.seo.txt` / `.seo.json` | 3 titres, description horodatée, tags, hashtags × 3 langues |
| `short.analyse.json` | coups détectés, muscles, placement, risques |

### 🎙️ Voix off avec ta voix (ElevenLabs)
```bash
export ELEVENLABS_API_KEY=...
python -m autovid voice-clone ma_voix_1.m4a ma_voix_2.m4a --name "Ma voix" --i-own-this-voice   # une fois
python -m autovid combat roda.mp4 -o sorties/roda.mp4 --discipline capoeira --ai claude --subs fr,pt,en
```
Le texte est en français, les mots brésiliens (ginga, rasteira, aú, meia-lua…) sont synthétisés en portugais.
Les arrêts sur image durent le temps de la phrase ; la musique baisse sous la voix.

### 🎞️ Motion design par le code (HyperFrames + Remotion)
`cd motion && npm install` une fois : chaque montage reçoit alors une **intro 3D HyperFrames** (HTML/CSS/GSAP,
placée juste après l'accroche) et une **carte de fin Remotion** (React : clic sur « S'abonner », cloche, teaser).
`--no-motion` pour s'en passer. Détails : skill `motion-design`.

### 📦 Skills en .zip
```bash
python -m autovid skills install skill-montage-video.zip   # vérifié : chemins, liens, SKILL.md ; scripts listés
python -m autovid skills pack -o dist/skill-montage-video.zip
```

### 🖼️ ADN de miniatures
```bash
python -m autovid thumbs captures_miniatures/ -o analyse/miniatures.json
```

## 📱 Plateforme téléphone ↔ PC
```bash
python -m autovid serve                       # page web + QR code : envoie depuis le téléphone, récupère le MP4
python -m autovid watch ~/Drive/entree ~/Drive/sorties --handle @toncompte   # dossier synchronisé
```
Détails, connecteurs (Canva, CapCut, Gemini, Flow, Antigravity, ElevenLabs, HyperFrames, Video-Use) et limites :
[docs/plateforme.md](docs/plateforme.md).

## 🤖 Skills Claude Code (`.claude/skills/`)
| skill | quand |
|---|---|
| `montage-combat` | « monte cette vidéo de boxe / MMA » — lance, puis **vérifie le rendu image par image** |
| `couper-les-blancs` | vidéo parlée : silences, « euh », faux départs, sous-titres |
| `copier-style` | « fais le même montage que cette vidéo » |
| `feedback-montage` | tes retours → réglages et `APPRENTISSAGES.md`, chaque montage s'améliore |
| `publier` | formats, légendes, hashtags, couverture (Canva), règles de monétisation |
| `voix-off` | clonage de ta voix, voix off FR + termes PT-BR, sous-titres FR / PT-BR / EN |
| `miniature-seo` | ADN des miniatures et titres d'une chaîne modèle → nos miniatures, titres, tags |
| `motion-design` | intro HyperFrames et carte de fin Remotion paramétrées, insérées dans le montage |

Skills officiels installés par `scripts/install.sh` : HyperFrames (`hyperframes`, `motion-graphics`, `hyperframes-core`…)
et Remotion (`remotion-best-practices`, `remotion-create`, `remotion-render`…).

Ce qui reste à construire : [docs/feuille-de-route.md](docs/feuille-de-route.md).

## Les autres commandes

### `analyze` — extraire l'« ADN » d'une vidéo qui marche
```bash
python -m autovid analyze reference.mp4 -o analyse/
```
Sortie : format, codecs, chaque coupe, durée des plans, BPM, part des coupes sur le temps, loudness,
mise en page seconde par seconde (`adn.json`, `resume.md`) + une planche contact (`planche.jpg`).

### `auto` — montage autonome d'un dossier de rushs
```bash
python -m autovid auto rushs/ -o out/short.mp4 --music musique.mp3 \
    --style bincombat --reference reference.mp4 --watermark "MonCompte" --cta "SAVE AND TRY" \
    --save-brief out/brief.json
```
- Les titres viennent des noms de fichiers : `01_mma__smart-back-kick.mp4` → surtitre **MMA**, titre **SMART BACK KICK**.
- `--reference` : copie le rythme (temps par plan) et la mise en page d'une vidéo existante.
- `--save-brief` : écrit le brief généré pour le retoucher et le relancer avec `render`.

### `render` — montage piloté par un brief (contrôle total)
```bash
python -m autovid render examples/pull_counter.yaml -o out/pull_counter.mp4
```
Voir [examples/pull_counter.yaml](examples/pull_counter.yaml). Options par plan :

| clé | valeurs |
|---|---|
| `clip` | chemin du rush (relatif au brief) |
| `start` | `auto` (pic de mouvement) ou secondes |
| `beats` / `duration` | longueur en temps musicaux ou en secondes |
| `layout` | `auto`, `cover`, `fit_blur`, `letterbox` |
| `kicker`, `title`, `subtitle`, `step` | textes |
| `transition` | `cut`, `flash`, `fade` |
| `zoom` | `punch` (sur l'impact), `push` |
| `speed` | `0.5` = ralenti ×2 |
| `markers` | `[{shape: ring/ellipse, x, y, r, color, at, dur}]` cercles qui pulsent |

Au niveau du brief : `style`, `music`, `bpm`, `music_offset`, `watermark`, `cta`, `keep_clip_audio`,
`clip_audio_volume`, `target_lufs`, `style_overrides`.

### `talk` — vidéo face caméra (façon Video-Use)
```bash
export ELEVENLABS_API_KEY=...      # facultatif : sans clé, pas de sous-titres
python -m autovid talk face_cam.mp4 -o out/talk.mp4 --language fra
```
Coupe des silences → recadrage 9:16 → transcription mot à mot ElevenLabs (scribe_v2) → retrait des « euh »
et des faux départs (on garde la dernière reformulation) → sous-titres dynamiques (mot prononcé en jaune avec un pop) → −14 LUFS.

## Styles
- **bincombat** — titre pinceau 2 lignes (jaune/blanc), coupe tous les 2 temps, changement de titre sec.
- **stepbystep** — titres condensés gras, étapes numérotées, pop, flash, forte accentuation.

Polices incluses : Anton (OFL) et Permanent Marker (Apache 2.0), dans `autovid/fonts/`.

## Pipeline
```
rushs ─► analyse (mouvement, format) ─┐
musique ─► BPM + premier temps ───────┼─► plan (timeline sur la grille du tempo)
référence ─► ADN (rythme, layout) ────┘        │
                                               ▼
        par plan : découpe ─ recadrage 9:16 ─ zoom ─ étalonnage ─ flash   (ffmpeg)
                                               ▼
        concat ─► habillage ASS (titres, étapes, cercles, filigrane, CTA) ─► mix musique ─► −14 LUFS ─► MP4
```

## Tests
```bash
python3 -m unittest discover tests
```

## Limites actuelles
- Détection des coups par squelette 2D : fiable sur un combattant bien visible ; sur une mêlée ou une vidéo déjà
  montée (avec ses propres titres), des coups peuvent être ratés ou mal nommés → `--ai claude`, ou rognez l'entrée.
- Les coups retournés ne sont nommés que par `--ai claude` (le squelette 2D les confond avec un circulaire).
- Pas encore de flèches animées ni de hook « réaction » en 2 vidéos superposées.
- Rendu ≈ 10 images/s sur un CPU de portable : ~1 à 2 min pour un short de 30 s en 1080p ; la 8K est beaucoup plus lente.
- Le BPM est estimé : sur une musique sans batterie nette, indique `bpm:` dans le brief.
- `main.jsx` / `src` : ancien prototype d'interface React, il n'est pas encore relié au moteur.
