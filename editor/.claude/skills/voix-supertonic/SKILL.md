---
name: voix-supertonic
description: Voix françaises hors-ligne Supertonic 3 (10 voix, 5-9 = hommes, 9 par défaut) via sherpa-onnx, calées sur un script minute. Rapide (~1 s par phrase sur CPU).
---
# voix-supertonic
```bash
pip install -U "sherpa-onnx>=2.0"
curl -sL https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11.tar.bz2 | tar xj -C packs/voices/models
python3 packs/voices/tts.py script.txt --out voix/ --engine supertonic --st-model packs/voices/models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11 --speaker 9 --speed 1.35
```
Script: `<debut_s | +pause> | <sous-titre> || <texte dit>` (la partie après `||` est l'orthographe phonétique envoyée à la voix, ex. `Caragoua`; le sous-titre reste correct). `+0.15` enchaîne la phrase 0,15 s après la précédente: les scènes se calent ensuite sur `voice.json`. Le français est ~25 % plus long que le portugais: resserrer le texte plutôt que d'accélérer au-delà de 1,4.
Pièges à surveiller (notes de l'utilisateur): « plus » négatif, « il » + verbe voyelle, « soir »; reformuler plutôt que relancer. Vérification de prononciation par Whisper non disponible dans cet environnement: écouter avant publication.
