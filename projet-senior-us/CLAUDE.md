@AGENTS.md

## Agents Claude Code de ce projet
| Besoin | Agent |
|--------|-------|
| écrire ou adapter une séance (JSON) en anglais américain | `redacteur-seance-us` |
| ranger vos voix off, clips du coach et musique ; ajuster les durées | `preparateur-medias` |
| rendre la vidéo, les images de contrôle, le dossier CapCut | `monteur-senior` |
| relire une séance ou une vidéo : sécurité, lisibilité, style | `controleur-senior` |

Ordre : `redacteur-seance-us` → `controleur-senior` (séance) → `preparateur-medias` (dès que des fichiers arrivent) → `monteur-senior` → `controleur-senior` (images de contrôle).

Séance d'exemple réutilisable : `sessions/exemple-50s.json` (50 s : intro, chronomètre avec flèche, compteur de répétitions, rappel de sécurité, fin).
