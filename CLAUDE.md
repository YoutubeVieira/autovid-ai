# AutoVid AI

Monteur vidéo automatique en Python + ffmpeg (paquet `autovid/`). Commandes : `python -m autovid -h`.

- Vidéos de combat → skill `montage-combat` (`python -m autovid combat`).
- Vidéo parlée → skill `couper-les-blancs` (`python -m autovid talk`).
- « Fais comme cette vidéo » → skill `copier-style`.
- Retours sur un rendu → skill `feedback-montage` ; publication → skill `publier`.
- Toujours **regarder** le rendu (planche contact via ffmpeg + Read) avant de dire qu'il est bon.
- Tests : `python3 -m unittest discover tests` (rapides, rushs synthétiques).
- Ne jamais committer de vidéos (`*.mp4` est ignoré) ni de clés API.
