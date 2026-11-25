# AutoVid AI — 3 projets indépendants

Chaque projet est autonome : son dossier contient ses agents, ses règles (`CLAUDE.md`), sa documentation et ses outils. Ouvrez Claude Code (ou Antigravity) **dans le dossier du projet** pour que ses agents soient chargés :
```bash
cd autovid-senior && claude      # ou autovid-shorts, autovid-apps
```

| | Projet | Pour quoi | Agents |
|---|---|---|---|
| 1 | [`autovid-senior/`](autovid-senior/) | **Auto Video Senior (US)** — séances de gym douce YouTube 16:9 pour seniors américains, montage automatique Python + FFmpeg, export YouTube et CapCut. Claude Code **et** Antigravity. | `redacteur-seance-us`, `preparateur-medias`, `designer-sonore`, `monteur-senior`, `controleur-senior` |
| 2 | [`autovid-shorts/`](autovid-shorts/) | **Shorts/Reels verticaux** au style des vidéos analysées (facecam + motion design + sous-titres mot à mot), gabarit Remotion, 11 skills `/yt-*`, effets sonores (earshot), **machine à Reels** (7 vidéos par semaine, approbation, 1 publication par jour, analyse des vraies statistiques) et **7 styles de création MP4** (motion, claymation, explainer, chanté, pub, 3D, cartoon — [`styles/STYLES.md`](autovid-shorts/styles/STYLES.md)) | `chef-machine`, `publicateur`, `analyste-performance`, `directeur-creatif`, `stratege-youtube`, `scenariste`, `monteur-video`, `sound-designer`, `decoupeur-shorts`, `motion-designer` |
| 3 | [`autovid-apps/`](autovid-apps/) | **Applications web et mobiles** (méthode Replica : analyser, reconstruire, tester, lancer), 11 skills `/replica-*` | `chercheur-produit`, `architecte-app`, `designer-ui`, `dev-web`, `dev-mobile`, `testeur-qa`, `lanceur` |

Analyse des deux vidéos d'origine : [`ANALYSE.md`](ANALYSE.md). Anciens fichiers de démarrage : [`archive/`](archive/).

## Où déposer vos voix off et vos vidéos
Chaque projet vidéo a un dossier d'entrée, lu automatiquement :

| Projet | Dossier | Mode d'emploi |
|--------|---------|---------------|
| Senior US | `autovid-senior/entrees/<séance>/coach/NN.mp4`, `voix/NN.mp3` | [`entrees/LISEZMOI.md`](autovid-senior/entrees/LISEZMOI.md) |
| Shorts | `autovid-shorts/entrees/<vidéo>/brut.mp4`, `voix.mp3` | [`entrees/LISEZMOI.md`](autovid-shorts/entrees/LISEZMOI.md) |

Ces médias ne sont pas versionnés dans git (trop lourds). Deux façons de les transmettre :
1. **Les joindre dans la conversation** (application Claude) : l'agent les range dans le bon dossier d'entrée.
2. **Travailler directement dans un dossier de votre PC** : sur le PC, ouvrez un terminal dans votre copie du dépôt et lancez `claude remote-control` (ou utilisez l'application Claude Desktop) ; la session apparaît dans l'application Claude Code et lit vos fichiers sur place, sans téléversement. Une session dans le cloud comme celle-ci ne peut pas accéder à votre PC.

## Antigravity
Toutes les demandes sont aussi disponibles dans **Google Antigravity** (règles + workflows `/…`) :
- **Dossier `autovid-ai` entier ouvert** : règle `.agent/rules/autovid.md` et 18 workflows dans `.agent/workflows/` —
  `/video-analyser-video`, `/video-superanalyse`, `/video-creer-short`, `/video-creer-style`, `/video-machine-semaine`, `/video-publier`, `/video-statistiques`, `/video-effets-sonores`, `/video-decouper-shorts`, `/video-installer`,
  `/senior-nouvelle-seance`, `/senior-importer-medias`, `/senior-monter-video`, `/senior-ajouter-sons`, `/senior-exporter-capcut`,
  `/app-cloner-app`, `/app-tester-app`, `/installer-pc`.
- **Un seul projet ouvert** : les mêmes workflows sans préfixe, dans `<projet>/.agent/workflows/`.

Chaque workflow renvoie à l'agent Claude Code correspondant (`.claude/agents/<nom>.md`) : les règles (validation avant publication ou dépense, clés jamais dans la conversation) sont les mêmes dans les deux outils. Les guides publics divergent sur le nom du dossier (`.agent/` ou `.agents/`) : si les workflows n'apparaissent pas, renommez-le `.agents/`.
