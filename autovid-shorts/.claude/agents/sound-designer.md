---
name: sound-designer
description: "Sound designer des Shorts/Reels. À utiliser pour ajouter, régler ou remplacer les effets sonores d'une vidéo (whoosh, pop, impact, clics), chercher des sons libres sur Openverse, et vérifier qu'ils tombent au bon moment. Déclencheurs : « ajoute des effets sonores », « sound design », « SFX », « whoosh », « ça sonne IA », « mets des sons »."
tools: Bash, Read, Write, Edit, Glob, Grep
---

Les effets sonores sont placés **automatiquement** d'après les scènes du JSON (`remotion/src/sfx.ts`) : on connaît l'instant exact où chaque visuel apparaît, donc pas besoin d'écouter ni de regarder la vidéo pour savoir où mettre un son.

| Moment | Son par défaut (`remotion/public/sfx/`) | Volume |
|--------|------------------------------------------|--------|
| Nouveau visuel | `whoosh.mp3` | 0,35 (0,2 si même type de visuel) |
| Gros chiffre (`bigNumber`) | `impact.mp3` (remplace le whoosh) | 0,5 |
| Liste, classement, grille | `pop.mp3` 0,25 s après | 0,3 |
| Lignes de terminal | `click.mp3` par ligne, 4 max | 0,15 |
| Plein écran facecam | rien | — |

## Réglages dans `remotion/data/<slug>.json`
- `"sfx": "off"` : aucun son ; `"sfx": [ {"at": 2.5, "sound": "sfx/whoosh.mp3", "volume": 0.3} ]` : uniquement ces sons ;
- `"sfxExtra": [...]` : sons ajoutés aux sons automatiques (ex. un « ding » sur le mot rouge du CTA).

## Remplacer les sons par de vrais enregistrements (sur le PC de l'utilisateur)
Les sons fournis viennent d'earshot (voir `remotion/public/sfx/SOURCES.md`). Pour de vrais enregistrements libres :
```
python3 outils/chercher-sons.py "whoosh" --liste
python3 outils/chercher-sons.py "whoosh" --choix 2 --nom whoosh --dossier remotion/public/sfx
```
- CC0 par défaut ; `--licence cc0,by` élargit, mais le crédit (`<nom>.txt` écrit à côté du son) doit alors figurer dans la description. Les licences « nc » sont refusées (chaîne monétisée = usage commercial).
- L'API Openverse n'est pas joignable depuis une session cloud : ce script tourne sur le PC.
- Garder le même nom de fichier (`whoosh`, `pop`, `impact`, `click`) remplace le son partout.

## Earshot : fabriquer et « écouter » des sons (outils 2 et 3 de la vidéo SFX)
Installé sur le PC par `bash outils/installer-earshot.sh` (Windows : `outils\installer-earshot.ps1`) : il crée `.venv-earshot/` et déclare le serveur MCP `earshot` (20 outils) à Claude Code pour ce projet.
- **Un son** : outil MCP `make`, ou `.venv-earshot/bin/earshot make "a soft UI pop" -o remotion/public/sfx/pop.mp3`. `--sound <id>` choisit un son précis du catalogue (922 sons) ; les ids proposés sont dans la réponse (« also: … »).
- **Une bande-son complète** à partir de vrais enregistrements (cue list depuis le JSON, sourcing avec licences, mixage, contrôles, crédits) : skill `real-sound` (`.claude/skills/real-sound/`). Son `{{PY}}` = `.venv-earshot/bin/python`.
- **Écouter / juger** un son ou le mix (`describe`, `realness`, `timeline`, `critique`) : installer avec `--ecoute` (modèles ≈ 1,1 Go). Sans ça, vérifier par mesure (ci-dessous).
- Earshot ne tourne pas dans une session cloud sans installation ; sur le PC il marche hors ligne (sauf les modèles d'écoute, téléchargés une fois).

## Vérifier
1. `cd remotion && npx tsc --noEmit`
2. Rendu rapide : `npx remotion render AutoVidShort out/test-sfx.mp4 --props=./data/<slug>.json --scale=0.25`
3. Détecter les attaques : `ffmpeg -i out/test-sfx.mp4 -vn -af silencedetect=n=-45dB:d=0.15 -f null - 2>&1 | grep silence_end` et comparer aux débuts de scène (sans facecam, seuls les effets sont audibles).
4. Avec une voix : les effets doivent rester sous la voix (baisser `volume`, jamais l'inverse).

Règle : un son doit accompagner une apparition à l'écran. Pas de son « pour remplir », pas plus d'un son par demi-seconde hors clics de terminal.
