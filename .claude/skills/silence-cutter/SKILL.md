---
name: silence-cutter
description: Regle la coupe des silences et le rythme (jump-cuts, punch-in) d'une video parlee.
---
# silence-cutter

Reglages dans `editor/presets/<preset>.json`:
- `silence.noise_db` (-35): seuil de silence; monter vers -30 si le bruit de fond est fort.
- `silence.min_silence` (0,35 s): en dessous, la pause est gardee (respiration naturelle).
- `silence.keep_pad` (0,08 s): marge conservee de chaque cote d'une coupe.
- `pacing.max_shot` (3,5 s): au-dela, jump-cut avec zoom (le son reste continu).
- `pacing.zoom_cycle`: cycle des zooms [1.0, 1.12, 1.0, 1.22].
Verifier `plan.json` (`removed`, `shots`) apres changement. Trop de coupes qui mangent la fin des mots: augmenter `keep_pad` a 0,12.
