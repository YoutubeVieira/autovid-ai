---
name: "sound-design-auto"
description: "Ajouter le sound design d'une vidéo (whoosh aux transitions, pops quand un élément apparaît, ticks, clics, respiration) à l'endroit exact où chaque son est utile, puis mixer avec la musique et la voix. Sons synthétisés, sans droits. À utiliser après le rendu d'une vidéo motion design ou d'un montage."
---

# Sound design automatique

Script : `scripts/sfx.py` (numpy + ffmpeg). Claude n'entend pas : il place les sons d'après la liste des moments où quelque chose se passe à l'image, puis vérifie avec les mesures.

## 1. Trouver les moments
- Vidéo codée (skill motion-design-video) : la page calcule elle-même `window.SFX` à partir de sa timeline, puis `node render.js page.html --events sons.json`. Les sons tombent donc à la milliseconde sur les animations.
- Montage de clips : un `whoosh` 0,25 s avant chaque changement de scène, un `pop` sur chaque titre ou carte, un `tick` sur chaque nouvelle ligne de texte.
- Format de chaque moment : `{ "t": secondes, "type": "whoosh|pop|tick|click|breathIn|breathOut", "gain": 1 }`.

## 2. Règles de dosage
- Whoosh : changement de scène seulement, commencé 0,25 s avant la coupe.
- Pop : apparition d'un mot ou d'une carte ; gain qui monte légèrement quand plusieurs se suivent (0,8 / 0,9 / 1).
- Tick : nouvelle consigne ou nouvelle ligne, discret (gain 0,5 à 1).
- Click : bouton (S'abonner, lien).
- Respiration : seulement pendant un exercice de respiration guidée, calée sur l'animation (inspire 4 s, expire 5 s).
- Pas plus d'un son par demi-seconde, sauf une série de pops voulue. Jamais de son sur une phrase importante de la voix off.

## 3. Fabriquer et mixer
`python sfx.py sons.json --music musique.wav --out mix.wav --video video-muette.mp4 --final video.mp4`
- Options : `--music-gain` (0,75), `--sfx-gain` (0,8).
- Avec une voix off : mixer d'abord voix + musique (musique baissée sous la voix), puis passer ce mélange en `--music` avec `--music-gain 1`.
- Son final normalisé à -14 LUFS, crête à -1,5 dB.

## 4. Vérifier sans écouter
- Mesurer le niveau : `ffmpeg -i video.mp4 -af ebur128 -f null -` (viser -14 LUFS intégrés).
- Dessiner la forme d'onde d'un extrait (`showwavespic`) et vérifier que les pics tombent aux temps prévus.
- Dire clairement à l'utilisateur que Claude n'a pas écouté le résultat et qu'il doit l'écouter avant publication.
