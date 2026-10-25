# Auto Video Senior (US) — Gentle Senior Fitness

Générateur automatique de séances de **gym douce pour seniors américains** (YouTube, 16:9), dans le style du kit *Gym Douce Senior* : coach en plein écran, quelques textes discrets posés sur la vidéo, aucun cadre.

```
séance (JSON) ──► autovideo.py (Python + FFmpeg) ──► MP4 1080p + YouTube (titre, description, chapitres, SRT)
                                                  └─► dossier CapCut (vidéo sans texte, calque transparent, SRT, timeline)
```

## Ce qui est généré automatiquement
| Élément | Détail |
|---------|--------|
| Plan de séance | 10, 20 ou 30 min, objectif équilibre / force / mobilité, à partir de `config/exercises.json` (15 exercices avec variante chaise) |
| Habillage | nom de la chaîne, `02 / 08`, nom de l'exercice, chronomètre `00:28`, barre fine, consigne, encouragement, flèche de mouvement, « Next: … » pendant le repos, rappel de sécurité |
| Animations | fondus 0,35–0,5 s, flèche ~1 s, aucun flash ni zoom |
| Chronomètre | calculé depuis le début et la fin de chaque segment (jamais un minuteur indépendant), ou compteur de répétitions `08 / 12` |
| Lisibilité | chaque texte passe en blanc avec halo sombre si le décor derrière lui est sombre (sinon olive avec halo beige) |
| Audio | voix off par segment (fichiers ou synthèse vocale), musique sous la voix, AAC 48 kHz |
| YouTube | `title.txt`, `description.txt` (chapitres + avertissement médical US + hashtags), `captions.en.srt` |
| CapCut | voir plus bas |

## Installation
```bash
cd projet-senior-us
pip install -r requirements.txt     # numpy, Pillow ; FFmpeg doit être installé
```
Les polices (Montserrat, Inter, Roboto Mono, licence OFL) sont dans `fonts/`.

## Utilisation
```bash
python3 autovideo.py plan --minutes 10 --focus balance        # → sessions/balance-10min.json
python3 autovideo.py check sessions/balance-10min.json        # timeline + avertissements
python3 autovideo.py still sessions/balance-10min.json --at 9 # image de contrôle
python3 autovideo.py render sessions/balance-10min.json       # vidéo finale
python3 autovideo.py render sessions/balance-10min.json --preview --until 60   # aperçu rapide
python3 autovideo.py render sessions/balance-10min.json --alpha              # + calque transparent pour CapCut
```

### Brancher vos médias
- **Coach** : `"coach_default": "assets/coach/coach.mp4"` dans la séance, ou `"coach"` par segment (vidéo ou image ; recadrage 16:9 automatique). Sans coach, une silhouette sert d'emplacement.
- **Voix off** : `"voice": "assets/voice/03.mp3"` par segment, ou une commande de synthèse vocale dans `config/brand.json`, par exemple :
  ```json
  "tts": { "command": "edge-tts --voice en-US-AriaNeural --text {text} --write-media {out}" }
  ```
  (n'importe quel outil qui écrit un fichier audio fonctionne ; `{text}` et `{out}` sont remplacés.)
- **Musique** : `"music": { "file": "assets/music.mp3", "volume": 0.10 }` dans `config/brand.json`.
- **Texte à gauche** si le coach est à droite : `"text_side": "left"` sur le segment. Forcer le ton : `"text_tone": "light"` (blanc) ou `"dark"` (olive).

## Dépôt sur CapCut
CapCut n'a **pas d'API de dépôt** : le générateur prépare `out/<slug>/capcut/`, à glisser dans CapCut (bureau ou web) ou dans CapCut Cloud.

| Fichier | Usage |
|---------|-------|
| `<slug>_final.mp4` | vidéo terminée, prête pour YouTube |
| `<slug>_clean.mp4` | coach + voix + musique **sans texte** : piste principale pour retoucher |
| `<slug>_overlay_alpha.mov` | (avec `--alpha`) tout l'habillage sur fond transparent, à poser au-dessus |
| `captions.en.srt` | *Captions → Import* (UTF-8) ; on peut aussi y appliquer la synthèse vocale de CapCut |
| `stills/*.png` | habillage de chaque segment en PNG transparent |
| `timeline.csv` | début et fin de chaque segment |

Le calque transparent est en QuickTime Animation (≈ 2 Mo/s ; `--alpha prores` pour ProRes 4444, ≈ 13 Mo/s). La documentation de CapCut ne précise pas s'il conserve la transparence de ces formats : **testez sur quelques secondes** ; si le fond devient noir, utilisez `<slug>_final.mp4`.

## Montage avec Claude Code et Antigravity
Les deux assistants partagent les mêmes règles : **`AGENTS.md`** (langue, style, sécurité, procédure de contrôle).

| | Claude Code | Google Antigravity |
|---|---|---|
| Règles | `CLAUDE.md` (importe `AGENTS.md`) | `AGENTS.md` + `.agent/rules/gym-douce-senior.md` |
| Créer une séance | agent `redacteur-seance-us` | workflow `/nouvelle-seance` |
| Monter la vidéo | agent `monteur-senior` | workflow `/monter-video` |
| Préparer CapCut | agent `monteur-senior` | workflow `/exporter-capcut` |
| Contrôle qualité | agent `controleur-senior` | (étapes de contrôle dans `/monter-video`) |

Ouvrir le dossier `projet-senior-us/` comme espace de travail (Antigravity) ou y lancer `claude`.
Antigravity : les guides publics divergent sur le nom du dossier (`.agent/` ou `.agents/`) ; `.agent/` est lu par toutes les versions documentées. Si vos règles n'apparaissent pas, renommez-le `.agents/`.

## Charte
Kit d'origine (français) : `docs/kit-gym-douce-senior.md` et `docs/kit-config-fr.json`. Version US : `config/brand.json` — couleurs, polices, positions, durées d'animation et tous les textes à l'écran (« REST », « Great job! », rappel de sécurité…) se changent là, sans toucher au code.
