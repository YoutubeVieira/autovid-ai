---
description: Ranger les voix off, clips du coach et musique fournis par l'utilisateur et ajuster la séance
---

1. Identifie la séance concernée (`sessions/<slug>.json`).
2. Lance `python3 autovideo.py check sessions/<slug>.json` pour voir le numéro de chaque segment.
3. Copie les fichiers dans `entrees/<slug>/` en suivant `entrees/LISEZMOI.md` (`coach/NN.*`, `voix/NN.*` ou `voix/complete.*`, `musique.*`). Demande confirmation si un fichier ne peut pas être associé à un segment avec certitude.
4. Vérifie chaque fichier avec `ffprobe` (lisible, durée, audio présent).
5. Relance `check` ; pour chaque voix trop longue, propose une nouvelle durée de segment qui garde la durée totale, et applique-la après accord.
6. Mets à jour le texte `say` si la voix enregistrée dit autre chose (sous-titres justes).
7. Donne le tableau des médias et ce qui manque encore.
