# Dossier d'entrée — vos prises et voix off

Un dossier par vidéo (`<slug>` = nom court, ex. `replica-fr`) :
```
entrees/<slug>/
├── brut.mp4        ← prise facecam brute (verticale de préférence)
├── voix.mp3        ← voix off séparée (facultatif ; sinon le son de brut.mp4)
└── script.md       ← texte prononcé (facultatif ; sinon l'agent scenariste l'écrit)
```
L'agent `monteur-video` part de ce dossier : coupe des silences (`outils/couper-silences.py`), sous-titres, `remotion/data/<slug>.json`, rendu dans `remotion/out/`.
Ces fichiers ne sont pas versionnés dans git.
