# AutoVid AI — 3 projets indépendants

Chaque projet est autonome : son dossier contient ses agents, ses règles (`CLAUDE.md`), sa documentation et ses outils. Ouvrez Claude Code (ou Antigravity) **dans le dossier du projet** pour que ses agents soient chargés :
```bash
cd projet-senior-us && claude      # ou projet-video, projet-app
```

| | Projet | Pour quoi | Agents |
|---|---|---|---|
| 1 | [`projet-senior-us/`](projet-senior-us/) | **Auto Video Senior (US)** — séances de gym douce YouTube 16:9 pour seniors américains, montage automatique Python + FFmpeg, export YouTube et CapCut. Claude Code **et** Antigravity. | `redacteur-seance-us`, `preparateur-medias`, `monteur-senior`, `controleur-senior` |
| 2 | [`projet-video/`](projet-video/) | **Shorts/Reels verticaux** au style des deux vidéos analysées (facecam + motion design + sous-titres mot à mot), gabarit Remotion, 11 skills `/yt-*` | `stratege-youtube`, `scenariste`, `monteur-video`, `decoupeur-shorts`, `motion-designer` |
| 3 | [`projet-app/`](projet-app/) | **Applications web et mobiles** (méthode Replica : analyser, reconstruire, tester, lancer), 11 skills `/replica-*` | `chercheur-produit`, `architecte-app`, `designer-ui`, `dev-web`, `dev-mobile`, `testeur-qa`, `lanceur` |

Analyse des deux vidéos d'origine : [`ANALYSE.md`](ANALYSE.md). Anciens fichiers de démarrage : [`archive/`](archive/).

## Où déposer vos voix off et vos vidéos
Chaque projet vidéo a un dossier d'entrée, lu automatiquement :

| Projet | Dossier | Mode d'emploi |
|--------|---------|---------------|
| Senior US | `projet-senior-us/entrees/<séance>/coach/NN.mp4`, `voix/NN.mp3` | [`entrees/LISEZMOI.md`](projet-senior-us/entrees/LISEZMOI.md) |
| Shorts | `projet-video/entrees/<vidéo>/brut.mp4`, `voix.mp3` | [`entrees/LISEZMOI.md`](projet-video/entrees/LISEZMOI.md) |

Ces médias ne sont pas versionnés dans git (trop lourds). Deux façons de les transmettre :
1. **Les joindre dans la conversation** (application Claude) : l'agent les range dans le bon dossier d'entrée.
2. **Travailler directement dans un dossier de votre PC** : sur le PC, ouvrez un terminal dans votre copie du dépôt et lancez `claude remote-control` (ou utilisez l'application Claude Desktop) ; la session apparaît dans l'application Claude Code et lit vos fichiers sur place, sans téléversement. Une session dans le cloud comme celle-ci ne peut pas accéder à votre PC.
