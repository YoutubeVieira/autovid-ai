# Néon Bay : sons et musique

## Ce qui est déjà dans le jeu
Tous les sons sont **générés par le jeu** (fichier `js/audio.js`, Web Audio). Ils sont 100 % originaux : aucun droit d'auteur, aucun fichier à télécharger.

- **Tirs** : un son différent par arme (pistolet, mitraillette, fusil à pompe, fusil d'assaut, précision, roquette, minigun) et pour les ennemis. Le son se place à gauche ou à droite et baisse avec la distance.
- **Explosions**, **chocs de voiture**, **impacts**, **douleur**, **K.O.**
- **Moteur** dont le régime suit la vitesse, **crissement de pneus** au frein à main, **sirène de police** qui monte quand la police approche
- **Argent ramassé**, **valise**, **étape réussie**, **niveau gagné**, **échec**, **achat**, **portière**, **tunnel**, **clics du menu**
- **Musique** générée en continu, différente pour chaque pays :
  - Menu : nappes calmes
  - Néon Bay (USA) : synthwave 100 BPM
  - Porto Lumi (Italie) : mandoline mineure 92 BPM
  - Sierra Verde (Colombie) : rythme cumbia et marimba 96 BPM
  - Morro Azul (Brésil) : funk 128 BPM
  - La batterie s'intensifie quand la police te recherche.
- Boutons **Musique oui/non** et **Bruitages oui/non** dans le menu et dans la pause.

## Ajouter tes propres fichiers
1. Mets le fichier (MP3 ou OGG) dans le dossier `audio/`.
2. Dans `js/data.js`, remplis `AUDIO_FILES`, par exemple :
   ```js
   const AUDIO_FILES = {
     music_usa: 'audio/music-usa.mp3',
     explosion: 'audio/explosion.ogg',
     shot_rifle: 'audio/rifle.ogg',
   };
   ```
3. Relance `node tools/build-standalone.js`. Attention : la version autonome `dist/index.html` ne contient pas les fichiers audio, il faut mettre le dossier `audio/` à côté d'elle en ligne.

Si un fichier manque ou ne se charge pas, le jeu reprend automatiquement le son généré.

## Bibliothèques gratuites
Vérifie toujours la licence de **chaque** fichier avant de l'utiliser dans un jeu vendu.

| Bibliothèque | Contenu | Licence | Pour un jeu vendu |
|---|---|---|---|
| Kenney.nl (kenney.nl/assets, catégorie Audio) | Packs de bruitages de jeu, interface, impacts, armes cartoon | CC0 (domaine public) | Oui, sans mention obligatoire |
| OpenGameArt.org | Bruitages et musiques de jeu | Mélange : CC0, CC-BY, CC-BY-SA, GPL | Préfère CC0 ou CC-BY (créditer l'auteur). Évite CC-BY-SA et GPL dans un jeu fermé |
| Freesound.org | Énorme base de bruitages réels (armes, voitures, sirènes, foule) | CC0, CC-BY, CC-BY-NC | Filtre sur CC0 ou CC-BY. **Jamais** NC (non commercial) |
| Pixabay Sound Effects et Music | Bruitages et musiques | Licence Pixabay (usage commercial autorisé, pas de revente du son seul) | Oui, relis les conditions |
| Sonniss « GDC Game Audio Bundle » (sonniss.com/gameaudiogdc) | Plusieurs Go de bruitages professionnels offerts chaque année | Libre de droits, usage commercial autorisé | Oui |
| Incompetech (Kevin MacLeod) | Musiques de tous styles | CC-BY 4.0 | Oui, avec crédit « Kevin MacLeod (incompetech.com) » |
| Free Music Archive | Musiques | Variable selon le morceau | Seulement CC0 ou CC-BY |
| Bibliothèque audio YouTube (YouTube Studio) | Musiques et bruitages | Pour les vidéos YouTube | **Pour tes vidéos YouTube**, pas pour le jeu |
| ZzFX / jsfxr | Générateurs de bruitages rétro en code | MIT | Oui |

## Bon à savoir
- Ne prends jamais un son extrait d'un jeu, d'un film ou d'une chanson connue : même court, c'est interdit sans autorisation.
- Garde une liste des sons utilisés avec leur source et leur licence (fichier `audio/CREDITS.txt`) : les stores et les acheteurs peuvent la demander.
- Sur téléphone, le son ne démarre qu'après un premier toucher de l'écran : c'est une règle des navigateurs.
