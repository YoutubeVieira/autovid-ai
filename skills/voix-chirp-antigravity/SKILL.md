---
name: "voix-chirp-antigravity"
description: "Produire des voix françaises naturelles (Google Chirp 3 HD, gratuit jusqu'à 1 million de caractères/mois) via un script lancé dans Antigravity sur le PC de l'utilisateur, puis les caler sur l'animation."
---

# Voix naturelles Chirp 3 HD via Antigravity

Les voix Piper (hors ligne) sonnent robotiques : pour les vidéos publiées, utiliser Chirp 3 HD.

## Règles
- Gratuit jusqu'à 1 million de caractères par mois (Chirp 3 HD), puis 30 $ par million : vérifier la page de prix Google avant d'en parler, et ne jamais dépasser (garde-fou dans le script). L'utilisateur refuse toute dépense hors crédits gratuits.
- Le script tourne sur le PC de l'utilisateur avec sa connexion Google (gcloud auth application-default login). Ne jamais demander ni lire de clé, mot de passe, fichier .env ou clé de compte de service.
- Script : voix_chirp.py (livré dans /mnt/user-data/outputs/voix-chirp). Commandes : `python voix_chirp.py essai` (une phrase avec chacune des 30 voix françaises, pour choisir à l'oreille) et `python voix_chirp.py episode episodes.json 1` (toutes les répliques d'un épisode, fichiers ep1/rawN.wav).
- Rôles par défaut : L/F héroïne Leda, M femme mûre Gacrux, P homme mûr Sadaltager, H homme grave Charon, N narratrice Aoede. Adapter après l'essai.
- Avec Chirp, écrire les noms normalement (« Rose-Marie ») : l'astuce « Rosemarie » ne sert qu'à Piper.

## Enchaînement
1. Claude écrit episodes.json (répliques, rôles, plans).
2. L'utilisateur lance le script dans Antigravity (ou Claude le lance directement si le PC est relié et qu'un terminal est disponible) et renvoie le dossier epN.
3. Claude vérifie chaque réplique avec Whisper, applique les traitements (écho léger pour le « futur »), puis timeline.py (bouche synchronisée + effets sonores) et le rendu.

## Vidéo « presque film »
Pour un rendu 3D réaliste, le code ne suffit pas : préparer des fiches personnages et des textes de plans pour Google Flow / Veo (inclus dans Google AI Pro, crédits mensuels) ; Claude monte ensuite les clips, sous-titres et sons.