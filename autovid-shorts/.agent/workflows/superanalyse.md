---
description: "Super-analyse sans images : seconde par seconde, moments forts, mots qui accrochent, SEO, prompts, améliorations"
---

1. Demande la vidéo, et si possible les sous-titres `.srt` et l'export de rétention de YouTube Studio.
2. Lance `python outils/superanalyse.py <video> [--srt <fichier.srt>] [--retention <retention.csv>]`.
3. Lis `analyses/<nom>/super.md`, `secondes.md` et `prompts.md`.
4. Si l'utilisateur veut des prompts complets : décris chaque plan dans `super.json` → `descriptions`, puis `python outils/superanalyse.py prompts analyses/<nom>/super.json`.
5. Résume : 3 moments les plus forts (préciser « estimé » sans courbe de rétention), mots qui accrochent et pourquoi, mot-clé SEO principal, 3 améliorations.
