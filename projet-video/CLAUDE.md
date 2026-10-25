# Projet vidéo — AutoVid

Production de vidéos YouTube et de Shorts au format décrit dans `../ANALYSE.md`.

## Quel agent pour quoi
| Besoin | Agent |
|--------|-------|
| quoi publier, quand, audit, SEO, viral, commentaires | `stratege-youtube` |
| script, hook, titre, miniature | `scenariste` |
| montage d'une prise brute → MP4 | `monteur-video` |
| Shorts à partir d'une vidéo longue | `decoupeur-shorts` |
| nouveau visuel / animation / style du gabarit Remotion | `motion-designer` |

## Chaîne de production
`stratege-youtube` (sujet) → `scenariste` (`scripts/<slug>.md`) → tournage → `monteur-video` (`remotion/data/<slug>.json` → `remotion/out/<slug>.mp4`) → `decoupeur-shorts`.
Les agents se passent le travail par fichiers : chacun lit ce que le précédent a écrit.

## Commandes
- Vérifier le gabarit : `cd remotion && npx tsc --noEmit`
- Image de contrôle : `npx remotion still AutoVidShort out/check.png --props=./data/<slug>.json --frame=<n>`
- Rendu : `npx remotion render AutoVidShort out/<slug>.mp4 --props=./data/<slug>.json`
- Couper les silences : `python3 outils/couper-silences.py brut.mp4 remotion/public/facecam.mp4`

## Règles
- Ne jamais inventer de chiffres ni de citations dans un script : `[À VÉRIFIER]`.
- Un mot rouge max par sous-titre ; un visuel toutes les 2 à 4 s.
- Ne rien publier sur YouTube ni répondre à des commentaires sans l'accord de l'utilisateur.
