---
name: "sound-design-auto"
description: "Ajouter le sound design d'une vidéo (whoosh aux transitions, pops quand un élément apparaît, ticks, clics, respiration, pleurs, cris, rires, soupirs, cœur) à l'endroit exact où chaque son est utile, puis mixer avec la musique et la voix. Sons synthétisés ou vrais enregistrements CC0 de la bibliothèque, sans droits. À utiliser après le rendu d'une vidéo motion design ou d'un montage."
---

# Sound design automatique

Script : `scripts/sfx.py` (numpy + ffmpeg). Claude n'entend pas : il place les sons d'après la liste des moments où quelque chose se passe à l'image, puis vérifie avec les mesures.

## 1. Trouver les moments
- Vidéo codée (skill motion-design-video) : la page calcule elle-même `window.SFX` à partir de sa timeline, puis `node render.js page.html --events sons.json`. Les sons tombent donc à la milliseconde sur les animations.
- Montage de clips : un `whoosh` 0,25 s avant chaque changement de scène, un `pop` sur chaque titre ou carte, un `tick` sur chaque nouvelle ligne de texte.
- Format d'un son synthétisé : `{ "t": secondes, "type": "whoosh|pop|tick|click|breathIn|breathOut", "gain": 1 }`.
- Format d'un vrai son de la bibliothèque : `{ "t": secondes, "son": "vrai-pleurs-enfant-1", "gain": 0.8, "duree": 4 }`. `duree` (facultatif) coupe le son avec un petit fondu. On peut aussi donner un chemin : `"fichier": "C:/.../son.wav"`.

## Bibliothèque de sons (studio-bibliotheque)
- 106 sons, livrés dans `studio-bibliotheque.zip` (dossier Téléchargements de l'utilisateur). Dézipper, puis passer le dossier à `--bibliotheque`. Le script cherche dans tous les sous-dossiers le fichier dont le nom (sans extension) est celui du champ `son`.
- Le catalogue de la bibliothèque donne le nom exact et l'usage de chaque son : toujours le lire avant de choisir, ne pas deviner un nom. Si un nom est introuvable, le script s'arrête et le dit.
- Dossier `voix-emotions` : 25 vrais enregistrements (BigSoundBank, licence CC0, gratuits, libres de droits, coupés à 15 s au plus). Exemples de noms : `vrai-pleurs-enfant-1`, `vrai-femme-essoufflee`.
  - Pleurs : bébé, nouveau-né, enfant (deux versions).
  - Cris : fille, garçon, groupe d'enfants, « oh ! » de surprise, cri Wilhelm (gag de cinéma, à éviter dans une scène sérieuse).
  - Respiration : homme essoufflé, femme essoufflée, respiration d'homme, deux soupirs, bâillement.
  - Rires : rire, éclats de rire, rires d'enfants, fou rire.
  - Autres : deux vrais battements de cœur, deux reniflements, une ambiance de peur, cris de joie avec applaudissements.
- Il n'y a pas de pleurs d'adulte : BigSoundBank n'en propose pas. Ne pas faire passer des pleurs d'enfant pour un adulte ; le signaler à l'utilisateur.
- Les respirations, soupirs et cœurs fabriqués par synthèse restent dans la bibliothèque, et le script garde `breathIn` / `breathOut` : choisir le vrai son pour une émotion à l'écran, le son synthétisé pour un exercice de respiration guidée.

## 2. Règles de dosage
- Whoosh : changement de scène seulement, commencé 0,25 s avant la coupe.
- Pop : apparition d'un mot ou d'une carte ; gain qui monte légèrement quand plusieurs se suivent (0,8 / 0,9 / 1).
- Tick : nouvelle consigne ou nouvelle ligne, discret (gain 0,5 à 1).
- Click : bouton (S'abonner, lien).
- Respiration : seulement pendant un exercice de respiration guidée, calée sur l'animation (inspire 4 s, expire 5 s).
- Voix et émotions (pleurs, cris, rires, soupirs, cœur) : seulement quand l'émotion est montrée à l'image, et jamais par-dessus une phrase de la voix off. Gain 0,5 à 0,8, coupé avec `duree` pour ne pas déborder sur la scène suivante.
- Pas plus d'un son par demi-seconde, sauf une série de pops voulue. Jamais de son sur une phrase importante de la voix off.

## 3. Fabriquer et mixer
`python sfx.py sons.json --music musique.wav --bibliotheque studio-bibliotheque --out mix.wav --video video-muette.mp4 --final video.mp4`
- Options : `--music-gain` (0,75), `--sfx-gain` (0,8).
- Avec une voix off : mixer d'abord voix + musique (musique baissée sous la voix), puis passer ce mélange en `--music` avec `--music-gain 1`.
- Son final normalisé à -14 LUFS, crête à -1,5 dB.

## 4. Vérifier sans écouter
- Mesurer le niveau : `ffmpeg -i video.mp4 -af ebur128 -f null -` (viser -14 LUFS intégrés).
- Dessiner la forme d'onde d'un extrait (`showwavespic`) et vérifier que les pics tombent aux temps prévus.
- Dire clairement à l'utilisateur que Claude n'a pas écouté le résultat et qu'il doit l'écouter avant publication.
