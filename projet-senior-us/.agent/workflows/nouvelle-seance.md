---
description: Créer une nouvelle séance de gym douce (anglais américain) et la valider
---

1. Demande la durée (10, 20 ou 30 min) et l'objectif (balance, strength ou mobility) si l'utilisateur ne les a pas donnés.
2. Lance `python3 autovideo.py plan --minutes <durée> --focus <objectif>`.
3. Ouvre le JSON créé dans `sessions/` et adapte titres, consignes (≤ 48 caractères), voix off (`say`) et encouragements selon `AGENTS.md`.
4. Lance `python3 autovideo.py check sessions/<slug>.json` et corrige chaque avertissement.
5. Montre à l'utilisateur la liste des exercices et la durée totale ; attends sa validation avant le montage.
