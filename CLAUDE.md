# AutoVid AI

Monteur vidéo automatique en Python + ffmpeg (paquet `autovid/`). Commandes : `python -m autovid -h`.

- Vidéos de combat → skill `montage-combat` (`python -m autovid combat`).
- Clip d'humour / animaux / généré par IA → `python -m autovid fun` (pas d'anatomie). Le mode combat refuse
  l'analyse si aucune vraie personne n'est reconnue (`--force` pour passer outre).
- Vidéo parlée → skill `couper-les-blancs` (`python -m autovid talk`).
- « Fais comme cette vidéo » → skill `copier-style`.
- Retours sur un rendu → skill `feedback-montage` ; publication → skill `publier`.
- Skills tiers (Melvynx/video-agent-skills, installés par `scripts/install.sh`) : `outliers` / `studio-script viral`
  (ce qui marche dans la niche), `studio-script` (scripts + accroches notées, `humanize`), `short-editing`
  (prise face caméra → short), `clips` (vidéo longue → shorts), `editing` (aiguillage).
- Toujours **regarder** le rendu (planche contact via ffmpeg + Read) avant de dire qu'il est bon.
- Tests : `python3 -m unittest discover tests` (rapides, rushs synthétiques).
- Ne jamais committer de vidéos (`*.mp4` est ignoré) ni de clés API.
