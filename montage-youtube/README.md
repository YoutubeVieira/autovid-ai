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
- Le service de voix n'a pas été testé depuis cette session (pas de clé ici) ; le montage, lui, a été vérifié en mode `--demo`.
