# Projet vidéo — AutoVid YouTube Agent

Inspiré de la vidéo 1 (voir [`../ANALYSE.md`](../ANALYSE.md)). Trois parties :

1. **5 agents** (`.claude/agents/`) qui se répartissent la production — voir ci-dessous.
2. **11 skills Claude Code** (`.claude/skills/`) qui font le travail d'une chaîne YouTube.
3. **Un gabarit Remotion** (`remotion/`) qui rend des Shorts/Reels au format des vidéos analysées : visuels en haut, facecam en bas, sous-titres mot à mot avec mot-clé rouge.

## Les 5 agents

| Agent | Rôle |
|-------|------|
| `stratege-youtube` | planning, audit, vidéos virales, SEO, rétention, commentaires |
| `scenariste` | script dans ta voix, hook, titre + miniature |
| `monteur-video` | prise brute → coupes → sous-titres → `video.json` → MP4 |
| `decoupeur-shorts` | vidéo longue → Shorts verticaux |
| `motion-designer` | nouveaux visuels et animations du gabarit Remotion |

Ils s'appellent automatiquement selon la demande (« monte cette vidéo », « écris le script de… »), ou explicitement : « utilise l'agent monteur-video sur brut.mp4 ». Le rôle de chacun est résumé dans [`CLAUDE.md`](CLAUDE.md).

L'outil `outils/couper-silences.py brut.mp4 sortie.mp4` (ffmpeg) coupe les silences d'une prise brute ; c'est la première étape du `monteur-video`.

## Les 11 skills

| Commande | Rôle |
|----------|------|
| `/yt-plan` | planifie la semaine : quoi, quand, quel format |
| `/yt-script` | écrit le script dans ta voix, à partir de [21 formules de hook](.claude/skills/yt-script/formules.md) |
| `/yt-package` | titre + miniature notés sur 100, avec variantes |
| `/yt-edit` | coupes de la prise brute + fichier `video.json` pour Remotion |
| `/yt-retention` | où les spectateurs décrochent et quoi réécrire |
| `/yt-chapters` | chapitres horodatés |
| `/yt-comment` | trie et répond aux commentaires, alimente le backlog |
| `/yt-viral` | trouve les vidéos virales de ta niche, les démonte et les recrée |
| `/yt-seo` | mot-clé, description, tags |
| `/yt-shorts` | extrait des Shorts d'une vidéo longue |
| `/yt-audit` | audit complet de la chaîne et plan d'action |

## Démarrer
```bash
cd projet-video
claude            # les skills de .claude/skills sont chargées automatiquement
```
Remplis d'abord `profil/voice.md` et `profil/chaine.md` (ou laisse `/yt-script` et `/yt-plan` te poser les questions).

Enchaînement typique : `/yt-plan` → `/yt-script` → `/yt-package` → tournage → `/yt-edit` → rendu → `/yt-shorts` → `/yt-comment`.

## Rendu vidéo (Remotion)
```bash
cd remotion
npm install
npm run studio            # aperçu interactif
npm run render            # exemple « YouTube Agent » → out/youtube-agent.mp4
npm run render:replica    # exemple « Replica » (thème sombre) → out/replica.mp4
```
- Mets ta prise facecam dans `remotion/public/facecam.mp4` et ajoute `"facecam": "facecam.mp4"` au JSON ; sans facecam, un emplacement factice est affiché.
- Format du JSON : [`remotion/src/types.ts`](remotion/src/types.ts). Mises en page : `split`, `facecam`, `graphic`. Visuels : `headline`, `bigNumber`, `terminal`, `iconGrid`, `bars`, `ranking`, `checklist`, `score`. Les mots entre `*astérisques*` sont en rouge.
- Les deux exemples (`remotion/data/`) sont les adaptations françaises des deux vidéos analysées.
