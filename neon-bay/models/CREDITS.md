# Modèles 3D
- `robot.glb` : RobotExpressive, par Tomás Laulhé (Quaternius), modifié par Don McCurdy. Licence CC0 1.0 (domaine public).
  Source : dépôt three.js, examples/models/gltf/RobotExpressive.

## Ajouter tes propres personnages
Tout fichier `.glb` animé (exporté de Blender, ou packs CC0 Quaternius / Kenney / KayKit) peut être déclaré dans `js/data.js` (`MODELS`). Le jeu cherche tout seul les animations dont le nom contient idle, walk, run, punch et death.
