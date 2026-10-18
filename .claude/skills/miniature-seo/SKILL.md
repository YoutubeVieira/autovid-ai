---
name: miniature-seo
description: Extrait l'ADN des miniatures et des titres d'une chaîne de référence (couleurs, lumière, place du sujet, texte, structure des titres) et l'applique aux miniatures, titres, descriptions, tags et hashtags de nos vidéos, en français, portugais du Brésil et anglais.
---

# Miniatures + SEO

1. **Récupérer les références.** Si YouTube est accessible : `yt-dlp --flat-playlist -J "https://www.youtube.com/@CHAINE/videos"`
   (titres, vues, durées) et `yt-dlp --skip-download --write-thumbnail` sur les 10 plus vues. Sinon, demande à
   l'utilisateur 8 à 15 captures de miniatures dans un dossier.
2. **ADN visuel** : `python -m autovid thumbs dossier_miniatures/ -o analyse/miniatures.json`
   (luminosité, contraste, saturation, chaleur, palette, centre du sujet, texte probable), puis **regarde** 3–4
   miniatures avec Read pour ce que les chiffres ne disent pas (émotion, objet star, composition).
3. **ADN des titres** : relève la structure (majuscules, émoji, crochets, longueur, mots-promesse). Référence
   FISH13 : « SUJET EN MAJUSCULES + émoji + promesse + [ mots-clés ] ». Adapte `autovid/seo.py` (dictionnaire `T`).
4. **Générer** : `python -m autovid combat …` écrit déjà `<sortie>_youtube.jpg` (1280×720), `<sortie>_cover.jpg`
   (1080×1920), `<sortie>.seo.txt` et `.seo.json` (3 titres, description avec horodatages, tags, hashtags × 3 langues).
   Ajuste l'étalonnage de `thumbs._grade` pour coller à l'ADN mesuré (sombre/froid ↔ lumineux/chaud).
5. Propose 3 titres et 2 miniatures pour un test A/B (YouTube Studio → « Tester et comparer »).
