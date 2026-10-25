# Dossier d'entrée — vos vidéos et voix off

Déposez vos fichiers ici, un dossier par séance (même nom que le `slug` du fichier `sessions/<slug>.json`).
Le générateur les trouve tout seul : aucun chemin à écrire dans la séance.

```
entrees/<slug>/
├── coach/
│   ├── defaut.mp4      ← clip utilisé pour tous les segments sans clip propre (facultatif)
│   ├── 02.mp4          ← clip du segment 02 (01 = intro)
│   └── 03.mov
├── voix/
│   ├── 01.mp3          ← voix off du segment 01…
│   ├── 02.wav
│   └── complete.mp3    ← OU une seule piste pour toute la séance (commence à 0:00)
└── musique.mp3         ← musique de fond (facultatif, mise sous la voix)
```

- **Numéros** : `python3 autovideo.py check sessions/<slug>.json` affiche le numéro de chaque segment et les fichiers trouvés (ou `—`).
- **Formats** : vidéo `.mp4 .mov .m4v .webm .mkv`, image `.png .jpg .webp`, audio `.mp3 .wav .m4a .aac .ogg .flac`. Toute taille ou orientation : la vidéo est recadrée en 16:9 sans déformation, et bouclée si elle est plus courte que le segment.
- **Voix trop longue** : `check` le signale ; allongez le segment (`duration`) ou raccourcissez l'enregistrement.
- Un chemin écrit dans la séance (`"coach"`, `"voice"`) reste prioritaire sur ce dossier.

Ces fichiers ne sont pas versionnés dans git (trop lourds) : seuls ce mode d'emploi et les dossiers vides le sont.
