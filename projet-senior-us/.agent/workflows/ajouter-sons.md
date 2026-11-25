---
description: Régler les effets sonores doux d'une séance (transition, cloche de repos, cloche de fin)
---

1. Lance `python3 autovideo.py check sessions/<slug>.json` et lis la ligne « effets sonores ».
2. Pour changer un son pour cette séance seulement, place le fichier dans `entrees/<slug>/sons/<événement>.mp3` (`exercise_start`, `rest_start` ou `outro`). Pour toutes les séances, remplace le fichier dans `sons/`.
3. Pour chercher un vrai son libre (sur le PC) : `python3 outils/chercher-sons.py "<mots-clés en anglais>" --liste`, puis `--choix N --nom <événement> --dossier entrees/<slug>/sons`.
4. Rends un aperçu (`render … --preview`) et mesure le volume autour de chaque son : il doit rester nettement sous la voix.
5. Vérifie que les crédits éventuels apparaissent dans `out/<slug>/youtube/description.txt`.
