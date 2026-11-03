# Voix locale avec Chatterbox (sans API, sans quota)

Objectif : produire la voix off sur votre machine, avec une voix proche de « Fenrir » (extrait de référence), sans dépense.

## Avant de commencer
- **Droits** : l'extrait fourni (`voix/fenrir-reference.wav`) vient de l'API Gemini. Les conditions d'utilisation de Google peuvent limiter la réutilisation des sorties de l'API (par exemple pour entraîner ou imiter un service concurrent) : à lire avant d'aller plus loin ; je n'ai pas pu les relire. La solution la plus sûre : enregistrer **votre propre voix** (10 à 40 s, sans bruit ni musique) et l'utiliser comme référence.
- Ne jamais cloner la voix d'une autre personne sans son accord écrit. Chatterbox ajoute un filigrane inaudible « généré par IA » ; YouTube demande d'indiquer les contenus de synthèse réalistes.

## Installation
```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r video-engine/tools/chatterbox/requirements.txt
```
La première exécution télécharge les poids du modèle (Hugging Face).

## Utilisation
```bash
cd video-engine
python3 tools/chatterbox/generate.py spread-france-allemagne-60s --ref voix/fenrir-reference.wav   # écrit public/projects/<projet>/voix-externe/<scène>.wav
VOICE=fenrir-chatterbox node tools/tts.mjs spread-france-allemagne-60s                             # intègre les fichiers au montage
node tools/build-props.mjs spread-france-allemagne-60s && node tools/render.mjs spread-france-allemagne-60s
```
Avec carte graphique, la génération est plus rapide que l'audio ; sur processeur seul, elle peut prendre plusieurs fois la durée de l'audio.
Réglages : `--exagg` (expressivité) et `--cfg` (rythme) ; commencer à 0,5 puis ajuster à l'oreille sur une scène (`--only s01`).

## Limites
- Script **non testé** avec le vrai modèle (poids inaccessibles depuis la session). La partie « fichier » du moteur est testée avec des audios factices.
- Qualité en français et ressemblance avec Fenrir : à écouter ; un clonage « zéro coup » ne reproduit pas toujours le ton énergique.
