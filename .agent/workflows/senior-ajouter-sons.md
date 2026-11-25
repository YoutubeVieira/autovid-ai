---
description: "Régler les effets sonores doux d'une séance"
---

Travaille dans le dossier `projet-senior-us/` : toutes les commandes et chemins ci-dessous s'entendent depuis ce dossier.

1. Lance `python3 autovideo.py check sessions/<slug>.json` et lis la ligne « effets sonores ».
2. Pour changer un son pour cette séance seulement, place le fichier dans `entrees/<slug>/sons/<événement>.mp3` (`exercise_start`, `rest_start` ou `outro`). Pour toutes les séances, remplace le fichier dans `sons/`.
3. Pour fabriquer un son doux (sur le PC, après `bash outils/installer-earshot.sh`) : `.venv-earshot/bin/earshot make --sound heal/chime -o entrees/<slug>/sons/rest_start.mp3` (familles douces : `whoosh/soft`, `notify/pair`, `heal/chime`, `logo/bloom`).
   Pour chercher un vrai son libre (sur le PC) : `python3 outils/chercher-sons.py "<mots-clés en anglais>" --liste`, puis `--choix N --nom <événement> --dossier entrees/<slug>/sons`.
4. Rends un aperçu (`render … --preview`) et mesure le volume autour de chaque son : il doit rester nettement sous la voix.
5. Vérifie que les crédits éventuels apparaissent dans `out/<slug>/youtube/description.txt`.
