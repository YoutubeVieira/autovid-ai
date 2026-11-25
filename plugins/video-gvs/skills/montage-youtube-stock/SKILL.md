---
name: "montage-youtube-stock"
description: "Monter une vidéo YouTube horizontale 16:9 avec voix off (Gemini), clips gratuits Pexels et Pixabay choisis par mots-clés, sous-titres, chapitres et musique baissée sous la voix. À utiliser pour toute vidéo YouTube faite de clips d'illustration et d'une voix off."
---

# Montage YouTube avec clips Pexels / Pixabay

Script prêt : `scripts/montage.py` (Python 3.9+ et ffmpeg, aucune bibliothèque). Exemple complet : `scripts/exemple-gym-over-60.json`. Lanceur Windows : `scripts/Faire-la-video.bat` (demande les clés en saisie masquée).

## Enchaînement
1. Écrire le fichier JSON de la vidéo : `title`, `slug`, `description` (avec la source de chaque chiffre cité), `tags`, `fallback_queries`, puis `scenes` : `chapter`, `text` (ce que dit la voix), `queries` (2 ou 3 recherches de clips en anglais, de la plus précise à la plus large).
2. Essai sans clé : `python montage.py video.json --demo` (faux clips, voix muette) pour vérifier les durées, le découpage et les sous-titres.
3. Vraie vidéo : `python montage.py video.json --music musique.mp3`. Clés dans les variables d'environnement `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `GEMINI_API_KEY`.
4. Livrer `build/<slug>/<slug>.mp4`, le `.srt` (à importer aussi dans YouTube) et `description.txt` (chapitres avec les minutes, crédits des clips, tags).

## Règles de montage
- 1920×1080, 30 i/s ; un plan toutes les 3 à 5 s ; jamais deux fois le même clip dans la vidéo si on peut l'éviter.
- 0,4 s de silence avant la première phrase, 0,45 s après chaque scène.
- Sous-titres de 42 caractères par ligne au plus, 2 lignes, coupés sur la ponctuation ; grands et contrastés pour un public senior.
- Son final à -14 LUFS (niveau YouTube) ; la musique baisse automatiquement sous la voix.
- Chapitres YouTube : le premier à 0:00, au moins 3, chacun d'au moins 10 s.
- Voix Gemini par défaut : Sulafat (femme, chaleureuse). Une requête toutes les 6 s ; en cas de quota, attendre et reprendre, jamais forcer.

## Écriture du script
- Appliquer la skill auto-humaniser à la voix off.
- Pour l'oral : nombres en toutes lettres, pas de parenthèses, phrases courtes et longues en alternance.
- Santé ou exercice : rappeler de consulter son médecin, ne citer que des chiffres sourcés (lien dans la description), faire relire par un professionnel avant publication.

## Sécurité
- Ne jamais demander, lire ni écrire une clé d'API dans la conversation ou un fichier.
- Licences : Pexels et Pixabay permettent l'usage commercial sans attribution ; les crédits sont quand même mis dans la description.

## Corriger
- Clip mal choisi : le retirer de `clips/choix.json`, supprimer `shots/`, relancer.
- Scène entière : changer ses `queries`, supprimer `clips/choix.json` et `shots/`, relancer.
- Phrase de voix : supprimer `voice/scene-NN.wav`, relancer. Sa propre voix : déposer `voice/scene-01.wav`... avant de lancer.
