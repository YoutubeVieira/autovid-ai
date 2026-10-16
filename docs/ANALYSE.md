# Analyse des 2 videos de reference

Mesures faites avec ffprobe/ffmpeg (scene detection, silencedetect, ebur128) + planches de vignettes.
**Limite** : aucune transcription n'a ete possible dans l'environnement (pas de modele de reconnaissance vocale), l'analyse porte donc sur la structure, le rythme, l'image et le son, pas sur les mots dits.

| | Video A (making-of Blender) | Video B (monteur dans Claude) |
|---|---|---|
| Duree | 13,8 s | 39,9 s |
| Format | 1080x1920, 30 fps, AV1 | 1440x2560, 30 fps, AV1 |
| Audio | AAC stereo 48 kHz | AAC stereo 44,1 kHz |
| Loudness integree | **-14,1 LUFS** (LRA 1,5, crete -4,4 dBFS) | **-14,1 LUFS** (LRA 1,6, crete -1,5 dBFS) |
| Silences > 0,3 s | aucun | 1 seul de 0,44 s (a 16 s) : les pauses sont coupees |
| Plans (seuil 0,08) | ~27 changements, dont une rafale de 5 en 0,4 s a 12,4-12,8 s | peu de coupes franches (1,5 / 2,6 / 3,5 / 29,6 / 32,5 s), le rythme vient des animations internes |

## Structure narrative

**A - revelation « derriere l'image »** : hook face camera (0-2,2 s) -> alternance face cam / captures ecran Blender (maillage, rig en T-pose, animation) / rendu final -> rafale de coupes rapides en fin -> le rendu final sert de recompense. Mise en page en split-screen (face cam en haut, ecran en bas, separateur orange) puis plein cadre sur le rendu.

**B - tutoriel en etapes** : hook face cam avec bandeau de titre (0-3,5 s) -> sequence de maquettes d'interface animees, **une etape toutes les ~3,3 s**, chacune avec un sous-titre en 2 niveaux (ligne en gras + ligne en italique serif) -> retour face cam avec sous-titres mot par mot, mot cle en jaune -> **CTA** avec bouton « Saiba Mais » et curseur qui clique.

## Recette extraite (encodee dans `editor/presets/shortform_9x16.json`)

1. Vertical 9:16, 30 fps, sortie 1080x1920.
2. Hook dans les 3 premieres secondes (texte en bandeau + visuel de promesse).
3. Zero temps mort : silences > 0,35 s coupes, on garde 0,08 s de respiration.
4. Un plan ne depasse pas ~3,5 s : sinon jump-cut avec punch-in (cycle de zoom 1.0 / 1.12 / 1.0 / 1.22).
5. Sous-titres gros, 1 a 3 mots, mot cle en couleur, zone basse-centrale.
6. Mastering **-14 LUFS**, crete <= -1,5 dBTP, dynamique serree (LRA ~1,5 a 11).
7. Structure : hook -> etapes/preuves -> payoff -> CTA.

## Ce que le monteur autonome fait deja / ne fait pas encore

Fait (teste sur ces 2 videos) : analyse, coupe des silences, jump-cuts + zoom, sous-titres ASS depuis un SRT, bandeau d'accroche, musique avec ducking, normalisation -14 LUFS, controle qualite automatique.
Pas encore : transcription integree (necessite `pip install faster-whisper`, sinon fournir un `.srt`), choix de b-roll, effets sonores, detection automatique du mot cle par IA (aujourd'hui : mot le plus long du groupe).
