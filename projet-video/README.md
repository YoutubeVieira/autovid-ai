# Projet vidéo — AutoVid YouTube Agent

Inspiré de la vidéo 1 (voir [`../ANALYSE.md`](../ANALYSE.md)). Trois parties :

1. **5 agents** (`.claude/agents/`) qui se répartissent la production — voir ci-dessous.
2. **11 skills Claude Code** (`.claude/skills/`) qui font le travail d'une chaîne YouTube.
3. **Un gabarit Remotion** (`remotion/`) qui rend des Shorts/Reels au format des vidéos analysées : visuels en haut, facecam en bas, sous-titres mot à mot avec mot-clé rouge.

## Les 11 agents

| Agent | Rôle |
|-------|------|
| `chef-machine` | pilote la semaine : 7 vidéos, file d'approbation, 1 publication par jour, analyse |
| `publicateur` | programme et publie sur Instagram, TikTok, YouTube les vidéos approuvées (connecteurs ou programmation native) |
| `analyste-video` | décortique une vidéo étape par étape (hook, rythme, texte, son, appel à l'action) avec un score /100, et en tire une recette |
| `analyste-performance` | importe vos vraies statistiques, classe les vidéos, propose les variantes |
| `directeur-creatif` | vidéo dans l'un des 7 styles (motion, claymation, explainer, chanté, pub, 3D, cartoon) : choisit l'outil, estime le coût, fait valider, pilote |
| `stratege-youtube` | planning, audit, vidéos virales, SEO, rétention, commentaires |
| `scenariste` | script dans ta voix, hook, titre + miniature |
| `monteur-video` | prise brute → coupes → sous-titres → `video.json` → MP4 |
| `decoupeur-shorts` | vidéo longue → Shorts verticaux |
| `motion-designer` | nouveaux visuels et animations du gabarit Remotion |
| `sound-designer` | effets sonores placés automatiquement sur chaque apparition, sons libres Openverse |

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

## Analyser une vidéo « blow-up »
```bash
python3 outils/analyser-video.py ma_video.mp4 virale.mp4 --transcrire
```
9 étapes : fiche technique, découpage (coupes franches et changements visuels), hook des 3 premières secondes, son (volume, silences), planche d'images, texte à l'écran, transcription, fin et appel à l'action, puis score mesurable /100. Résultat dans `analyses/<nom>/rapport.md` (+ images ; `comparatif.md` pour plusieurs vidéos). L'agent `analyste-video` lit les images et complète le jugement (formule du hook, structure, pourquoi ça marche, recette à reprendre).

### Super-analyse (sans images)
```bash
python3 outils/superanalyse.py video.mp4 [--srt sous-titres.srt] [--retention retention.csv]
```
- **Seconde par seconde** (`secondes.md`) : ce qui est dit, énergie de la voix, changement d'image, mots forts, potentiel d'engagement.
- **Moments les plus puissants** : estimés à partir de ces signaux, ou **réels** avec l'export de rétention de YouTube Studio.
- **Mots et formulations** qui accrochent (curiosité, chiffre, gratuit, urgence, adresse directe, choc, contraste, question, appel à l'action) et **pourquoi** ils marchent.
- **SEO** : mot-clé principal, mots-clés, hashtags, tags YouTube.
- **Prompts plan par plan** (`prompts.md`, FR + EN) pour recréer la vidéo avec un générateur (Seedance, Kling…), et **améliorations** classées.

## Machine à Reels (créer, publier, analyser)
Vous ne faites que relire et approuver : voir [`machine/LISEZMOI.md`](machine/LISEZMOI.md). Demandez « lance la machine pour la semaine prochaine » (agent `chef-machine`).

## Les 7 styles de création MP4
Motion, Claymation, Explainer, Singing, Commercial, Animation 3D, Cartoon : voir [`styles/STYLES.md`](styles/STYLES.md) (outil public le plus proche, clés, coût, licence). Installation sur votre PC :
```bash
bash outils/installer-styles.sh        # Windows : powershell -ExecutionPolicy Bypass -File outils\installer-styles.ps1
```
Puis demandez par exemple « une pub claymation de 20 s pour mon livre » : l'agent `directeur-creatif` s'occupe du reste.

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
- **Effets sonores** automatiques : whoosh à chaque nouveau visuel, impact sur les gros chiffres, pop sur les listes, clics sur les lignes de terminal (`src/sfx.ts`, sons dans `public/sfx/`). `"sfx": "off"` les coupe, `"sfxExtra"` en ajoute. Pour de vrais enregistrements libres : `python3 outils/chercher-sons.py` (Openverse, à lancer sur votre PC).
- **Earshot** (outils 2 et 3 de la vidéo SFX) : `bash outils/installer-earshot.sh` sur votre PC (Windows : `outils\installer-earshot.ps1`) installe l'outil et déclare son serveur MCP à Claude Code ; les skills `earshot` (fabriquer / écouter un son) et `real-sound` (bande-son complète depuis de vrais enregistrements, compatible Remotion) sont dans `.claude/skills/`. Les sons par défaut en viennent (`remotion/public/sfx/SOURCES.md`).
