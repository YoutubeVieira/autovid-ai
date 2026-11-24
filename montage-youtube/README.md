# Montage YouTube automatique

Fabrique une vidéo YouTube horizontale (1920×1080) à partir d'un script : voix off de femme (Gemini), clips gratuits Pexels et Pixabay choisis par mots-clés, un plan toutes les 3 à 5 secondes, sous-titres incrustés, musique baissée sous la voix, son au niveau YouTube (-14 LUFS).

Première vidéo prête à monter : **`videos/gym-over-60.json`**, « Over 60 and New to the Gym? Start With These 5 Gentle Moves », en anglais pour les Américaines de plus de 60 ans, environ 4 minutes, 12 chapitres.

## Sous Windows

1. Installer une fois : `winget install Python.Python.3.12` et `winget install Gyan.FFmpeg`.
2. Créer les clés gratuites : [Pexels](https://www.pexels.com/api/), [Pixabay](https://pixabay.com/api/docs/), [Google AI Studio](https://aistudio.google.com/apikey) pour la voix.
3. Double-cliquer sur `Faire-la-video.bat`. Choisir la vidéo, coller les clés (rien ne s'affiche), glisser une musique si vous en avez une.

Résultat dans `build/gym-over-60/` :

- `gym-over-60.mp4` : la vidéo ;
- `gym-over-60.srt` : les sous-titres à envoyer aussi à YouTube (Sous-titres > Importer un fichier) ;
- `description.txt` : titre, description, chapitres avec les minutes, crédits des clips, tags.

En cas d'arrêt (quota, réseau), relancez : ce qui est déjà fait est gardé.

## En ligne de commande

```bash
python montage.py videos/gym-over-60.json --demo                  # essai sans clé : faux clips, voix muette
python montage.py videos/gym-over-60.json --music musique.mp3     # vraie vidéo
```

Options : `--no-burn` (pas de sous-titres dans l'image), `--music-volume 0.18`, `--out dossier`.
Réglages de voix : `VOICE` (Sulafat par défaut), `TTS_MODEL` (gemini-3.8-flash-tts), `TTS_STYLE` (consigne de ton, par exemple « Say this in a warm, friendly, unhurried tone: »).

## Corriger le résultat

- **Un clip ne convient pas** : ouvrir `build/<vidéo>/clips/choix.json`, supprimer le clip dans la liste de sa scène, supprimer le dossier `shots`, relancer.
- **Mauvais clips pour toute une scène** : changer les `queries` de la scène dans le JSON, supprimer `clips/choix.json` et `shots`, relancer.
- **Refaire une phrase de voix** : supprimer `voice/scene-05.wav` (par exemple) et relancer.
- **Votre propre voix** : déposer vos enregistrements `voice/scene-01.wav`, `scene-02.mp3`... avant de lancer.

## Nouvelle vidéo

Copier `videos/gym-over-60.json` et changer : `title`, `slug`, `description`, `tags`, puis une entrée par scène dans `scenes` (`chapter`, `text` = ce que dit la voix, `queries` = 2 ou 3 recherches de clips en anglais, de la plus précise à la plus large).

## À savoir

- Licences : Pexels et Pixabay autorisent l'usage commercial sans attribution. Les crédits sont quand même ajoutés à la description. Vérifiez les clips où une personne est reconnaissable dans un contexte sensible (santé, douleur).
- La vidéo donne des conseils d'exercice : faites relire le script par un professionnel de l'activité physique adaptée avant publication. La description rappelle de consulter son médecin.
- Le chiffre cité (CDC : 2 jours de renforcement et 150 minutes d'activité modérée par semaine pour les 65 ans et plus) vient de la page source mise dans la description.
- Le service de voix n'a pas été testé depuis cette session (pas de clé ici) ; l'essai `--demo` du montage avec clips a été arrêté avant la fin (trop lent ici) : faites un premier essai avec `--demo` chez vous.

## Vidéo en motion design (sans clips ni voix)

`motion/wellness-60.html` : « Gentle Wellness After 60 », 3 min 35, en anglais. Une femme senior dessinée fait les 8 exercices sur une chaise (respiration, nuque, épaules, marche assise, étirement, assis-debout, montées sur pointes, équilibre sur une jambe). Les consignes s'affichent une à une, avec le nombre de répétitions et la progression de la séance.

- Aperçu : ouvrir `motion/wellness-60.html` dans Chrome (ajouter `?t=130` à l'adresse pour aller à 130 s).
- Rendu (il faut Node et Playwright) :

```bash
cd motion
node render.js wellness-60.html --out ../build/wellness-60/video-muette.mp4
python music.py --duration 214.8 --chimes 30.2,50.8,71.4,92,112.6,133.2,153.8,174.4 --out ../build/wellness-60/musique.wav
ffmpeg -i ../build/wellness-60/video-muette.mp4 -i ../build/wellness-60/musique.wav -c:v copy -c:a aac -b:a 192k -af loudnorm=I=-16:TP=-1.5 -shortest ../build/wellness-60/wellness-60.mp4
```

La musique est synthétisée par `music.py` (aucun morceau extérieur, donc pas de problème de droits). Les textes et l'animation se modifient dans le fichier HTML (tableau `MOVES`).
