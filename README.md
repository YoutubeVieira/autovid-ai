# AutoVid AI — monteur vidéo automatique

Tu lui donnes des rushs et une musique, il sort un short 9:16 prêt à poster : coupes calées sur le tempo,
meilleur moment de chaque plan trouvé tout seul, recadrage vertical, titres animés, annotations, filigrane,
CTA et son normalisé à −14 LUFS. Les deux styles fournis sont reconstitués à partir de deux vidéos
virales de sports de combat (voir [docs/analyse-videos.md](docs/analyse-videos.md)).

Tout tourne en local avec **ffmpeg + Python** (numpy, PyYAML, requests). Pas d'After Effects, pas de Premiere.

## Installation
```bash
sudo apt install ffmpeg          # ou brew install ffmpeg (il faut libass, inclus d'habitude)
pip install numpy pyyaml requests
```

## Les 4 commandes

### 1. `analyze` — extraire l'« ADN » d'une vidéo qui marche
```bash
python -m autovid analyze reference.mp4 -o analyse/
```
Sortie : format, codecs, chaque coupe, durée des plans, BPM, part des coupes sur le temps, loudness,
mise en page seconde par seconde (`adn.json`, `resume.md`) + une planche contact (`planche.jpg`).

### 2. `auto` — montage autonome d'un dossier de rushs
```bash
python -m autovid auto rushs/ -o out/short.mp4 --music musique.mp3 \
    --style bincombat --reference reference.mp4 --watermark "MonCompte" --cta "SAVE AND TRY" \
    --save-brief out/brief.json
```
- Les titres viennent des noms de fichiers : `01_mma__smart-back-kick.mp4` → surtitre **MMA**, titre **SMART BACK KICK**.
- `--reference` : copie le rythme (temps par plan) et la mise en page d'une vidéo existante.
- `--save-brief` : écrit le brief généré pour le retoucher et le relancer avec `render`.

### 3. `render` — montage piloté par un brief (contrôle total)
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

### 4. `talk` — vidéo face caméra (façon Video-Use)
```bash
export ELEVENLABS_API_KEY=...      # facultatif : sans clé, pas de sous-titres
python -m autovid talk face_cam.mp4 -o out/talk.mp4 --language fra
```
Coupe des silences → recadrage 9:16 → transcription mot à mot ElevenLabs Speech-to-Text →
sous-titres dynamiques (mot prononcé en jaune avec un pop) → −14 LUFS.

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
- Pas encore de masque coloré qui suit un membre (il faut un modèle de segmentation type SAM 2 / MediaPipe).
- Pas encore de flèches animées ni de hook « réaction » en 2 vidéos superposées.
- Le BPM est estimé : sur une musique sans batterie nette, indique `bpm:` dans le brief.
- `main.jsx` / `src` : ancien prototype d'interface React, il n'est pas encore relié au moteur.
