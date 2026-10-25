# Projet vidéo — AutoVid YouTube Agent

Inspiré de la vidéo 1 (voir [`../ANALYSE.md`](../ANALYSE.md)). Deux parties :

1. **11 skills Claude Code** (`.claude/skills/`) qui font le travail d'une chaîne YouTube.
2. **Un gabarit Remotion** (`remotion/`) qui rend des Shorts/Reels au format des vidéos analysées : visuels en haut, facecam en bas, sous-titres mot à mot avec mot-clé rouge.

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
