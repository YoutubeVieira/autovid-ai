---
name: couper-les-blancs
description: Nettoie une vidéo face caméra — coupe les silences, les « euh », les bégaiements et les faux départs (garde la dernière reformulation), recadre en 9:16 et ajoute des sous-titres dynamiques mot par mot. À utiliser pour une vidéo parlée, un tutoriel, une explication ou un vlog.
---

# Couper les blancs

```bash
export ELEVENLABS_API_KEY=...   # transcription mot à mot (modèle scribe_v2 par défaut, ELEVENLABS_STT_MODEL pour changer)
python -m autovid talk "<video>" -o "sorties/<nom>_talk.mp4" --language fra --workdir "travail/<nom>"
```
- Sans clé : seuls les silences sont coupés, pas de sous-titres.
- Réglages : `--noise-db -35` (plus haut = coupe plus), `--min-silence 0.4` (s).
- Après le rendu, lis `travail/<nom>/mots.json` et vérifie qu'aucune phrase utile n'a été coupée par la détection des faux départs (même début de phrase répété dans les 8 s → la première version est retirée).
- Regard caméra (lecture de téléprompteur) : pas faisable ici ; c'est la fonction « Eye Contact » de Descript, à appliquer avant.
