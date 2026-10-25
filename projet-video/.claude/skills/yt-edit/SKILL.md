---
name: yt-edit
description: Prépare le montage — marque les coupes d'une prise brute et génère le fichier video.json (scènes, visuels, sous-titres) que le gabarit Remotion de ce projet rend en vidéo verticale. Utiliser pour « monte la vidéo », « coupes », « sous-titres », « edit ».
---

# /yt-edit — des coupes au fichier de montage

## 1. Coupes (prise brute)
Si une vidéo brute est fournie :
1. Détecte les silences : `ffmpeg -i brut.mp4 -af silencedetect=n=-35dB:d=0.4 -f null -`.
2. Transcris (Whisper si disponible) ; sinon demande le script `/yt-script` et aligne à la main.
3. Coupe : silences > 0,4 s, doublons de phrase (garde la dernière prise), « euh ».
4. Écris `montage/coupes.txt` (liste `debut-fin` à garder) et la commande ffmpeg de concaténation.

## 2. video.json pour Remotion
Format (voir `remotion/src/types.ts`) :
```json
{
  "title": "…", "theme": "light", "facecam": "facecam.mp4",
  "scenes":   [{ "from": 0, "to": 3, "layout": "split", "visual": { "type": "headline", "text": "*YouTube*" } }],
  "captions": [{ "from": 0, "to": 1.5, "text": "Claude vient de *tuer*" }]
}
```
Règles de montage tirées des vidéos de référence :
- **Un visuel toutes les 2 à 4 s** en haut (`layout: "split"`) ; jamais plus de 4 s sans changement.
- Plein écran facecam (`"facecam"`) seulement pour le moment émotionnel ou le payoff, 2 s max.
- Plein écran graphique (`"graphic"`) pour les gros chiffres et la « révélation ».
- Sous-titres : 2 à 6 mots par segment, 1 mot `*rouge*` max (le mot qui porte le sens).
- Chaque `visual` reprend le nom de la skill / l'objet dont on parle (libellé `label`).

Écris `remotion/data/<slug>.json`, copie la facecam dans `remotion/public/`, puis :
```
cd remotion && npx remotion render AutoVidShort out/<slug>.mp4 --props=./data/<slug>.json
```
