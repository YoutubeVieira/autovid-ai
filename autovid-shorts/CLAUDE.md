# Projet vidéo — AutoVid

Production de vidéos YouTube et de Shorts au format décrit dans `docs/ANALYSE.md`.

## Quel agent pour quoi
| Besoin | Agent |
|--------|-------|
| semaine de contenu : 7 vidéos, approbation, 1 publication/jour, analyse | `chef-machine` |
| programmer / publier sur Instagram, TikTok, YouTube (vidéos approuvées seulement) | `publicateur` |
| statistiques réelles, classement, variantes à produire | `analyste-performance` |
| décortiquer une vidéo (la sienne ou une virale) : hook, rythme, texte, son, CTA, score | `analyste-video` |
| vidéo dans un style précis (claymation, explainer, chanté, pub, 3D, cartoon, motion) | `directeur-creatif` |
| quoi publier, quand, audit, SEO, viral, commentaires | `stratege-youtube` |
| script, hook, titre, miniature | `scenariste` |
| montage d'une prise brute → MP4 | `monteur-video` |
| Shorts à partir d'une vidéo longue | `decoupeur-shorts` |
| nouveau visuel / animation / style du gabarit Remotion | `motion-designer` |
| effets sonores (whoosh, pop, impact…), sons Openverse | `sound-designer` |

## Fichiers de l'utilisateur
Prises brutes et voix off : `entrees/<slug>/` (voir `entrees/LISEZMOI.md`). Ne jamais les committer.

## Chaîne de production
`stratege-youtube` (sujet) → `scenariste` (`scripts/<slug>.md`) → tournage → `monteur-video` (`remotion/data/<slug>.json`) → `sound-designer` (si les sons automatiques ne suffisent pas) → rendu `remotion/out/<slug>.mp4` → `decoupeur-shorts`.
Les agents se passent le travail par fichiers : chacun lit ce que le précédent a écrit.

## Machine à Reels
Boucle hebdomadaire créer → approuver → programmer → publier → analyser : `machine/LISEZMOI.md`, outil `outils/machine.py`. L'utilisateur seul approuve ; rien n'est programmé ni publié sans son approbation.

## Styles de création (7)
Catalogue, outils, clés et coûts : `styles/STYLES.md`. Installation sur le PC : `bash outils/installer-styles.sh` (ou `.ps1`). Les outils tiers vont dans `externes/` et `.claude/skills/<style>`, jamais dans git ; les clés dans `.env`, jamais dans le chat.

## Commandes
- Vérifier le gabarit : `cd remotion && npx tsc --noEmit`
- Image de contrôle : `npx remotion still AutoVidShort out/check.png --props=./data/<slug>.json --frame=<n>`
- Rendu : `npx remotion render AutoVidShort out/<slug>.mp4 --props=./data/<slug>.json`
- Analyser une vidéo : `python3 outils/analyser-video.py video.mp4 [--transcrire]` → `analyses/<nom>/rapport.md`
- Super-analyse sans images (seconde par seconde, moments forts, mots qui accrochent, SEO, prompts, améliorations) : `python3 outils/superanalyse.py video.mp4 [--srt s.srt] [--retention r.csv]` → `analyses/<nom>/super.md`
- Couper les silences : `python3 outils/couper-silences.py brut.mp4 remotion/public/facecam.mp4`

## Règles
- Ne jamais inventer de chiffres ni de citations dans un script : `[À VÉRIFIER]`.
- Un mot rouge max par sous-titre ; un visuel toutes les 2 à 4 s.
- Ne rien publier sur YouTube ni répondre à des commentaires sans l'accord de l'utilisateur.
