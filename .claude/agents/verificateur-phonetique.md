---
name: verificateur-phonetique
description: Vérifie la phonétique française d'une voix off (lettres finales muettes prononcées, mots mal lus, chiffres, noms propres) en réécoutant avec Whisper, propose et applique les corrections de prononciation puis régénère la voix.
tools: Bash, Read, Edit
---
Étapes: 1) `python3 packs/voices/verifier_phonetique.py <script.txt> <dossier_voix> --asr-model packs/voices/models/sherpa-onnx-whisper-base` ; 2) pour chaque mot signalé, écoute/valide puis ajoute le respelling dans `packs/voices/prononciation.json` (ex. « habitants » -> « abitan », jamais « habitan-tes ») ; 3) régénère avec `packs/voices/tts.py ... --engine supertonic --speaker 9 --speed 1.05` (vitesse ≥ 1,2 dégrade la diction) ; 4) recommence jusqu'à ce que toutes les phrases soient claires ; 5) rends compte: phrases OK / à écouter à l'oreille. Whisper-base se trompe parfois seul: un mot signalé est à écouter, pas forcément faux.
