---
name: voix-off
description: Crée la voix off explicative d'une vidéo de combat ou de capoeira avec la voix clonée de l'utilisateur (ElevenLabs) — technique, placement, anatomie, risques de blessure — en français avec les termes brésiliens prononcés en portugais, et les sous-titres français, portugais du Brésil et anglais.
---

# Voix off + sous-titres multilingues

## Une seule fois : cloner la voix (uniquement la voix de l'utilisateur, ou avec un accord écrit)
1. Demande 1 à 3 minutes d'enregistrement propre (micro proche, pièce calme, sans musique), en français, avec
   quelques mots brésiliens dits naturellement (ginga, rasteira, aú, meia-lua de compasso).
2. ```bash
   export ELEVENLABS_API_KEY=...
   python -m autovid voice-clone voix1.m4a voix2.m4a --name "Ma voix" --i-own-this-voice
   ```
   L'identifiant est gardé dans `~/.config/autovid/voix.json` (ou `ELEVENLABS_VOICE_ID`).

## À chaque vidéo
```bash
python -m autovid combat video.mp4 -o sorties/x.mp4 --discipline capoeira --ai claude --subs fr,pt,en --burn fr
```
- `--ai claude` écrit la voix off (placement, muscles, risque) à partir des images ; sinon un texte modèle est utilisé.
- Les arrêts sur image s'allongent pour laisser la voix finir. Musique et son d'origine baissent sous la voix.
- Sorties : `x.mp4` (FR incrustés + pistes FR/PT/EN activables), `x.fr.srt`, `x.pt.srt`, `x.en.srt` (à envoyer sur
  YouTube), `x.voix.txt` (le script, à relire).
- Relis `x.voix.txt` : corrige tout terme anatomique douteux et relance. Les termes [pt] sont prononcés en portugais.
- Modèle de voix : `ELEVENLABS_TTS_MODEL` (par défaut `eleven_multilingual_v2`).
