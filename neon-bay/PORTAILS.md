# Néon Bay sur les portails de jeux (Poki, CrazyGames)

## Le principe
Sur les portails, le jeu est **entièrement gratuit** (les 30 niveaux). Tu gagnes de l'argent grâce aux **publicités** que le portail affiche :
- une pub entre deux niveaux (le portail décide s'il en montre une) ;
- une pub **récompensée** facultative à la fin d'un niveau : « Doubler le bonus (vidéo) ».
Le bouton « Jeu complet » et les codes Systeme.io sont masqués dans ces versions (les portails n'acceptent pas les paiements externes).

## Fabriquer les versions
```
node tools/build-portal.js
```
Cela crée :
- `dist-portal/poki/` et `dist-portal/neon-bay-poki.zip`
- `dist-portal/crazygames/` et `dist-portal/neon-bay-crazygames.zip`

## Soumettre
- **CrazyGames** : developer.crazygames.com → créer un jeu → envoyer le `.zip` (type HTML5). Leur équipe teste le jeu avant publication.
- **Poki** : poki.com/fr/developers → remplir le formulaire de candidature. Poki sélectionne les jeux et fournit son outil d'envoi après acceptation.

## À vérifier avant d'envoyer
- Les appels aux SDK (`js/portal.js`) suivent les API publiques connues (Poki SDK v2, CrazyGames SDK v3). **Vérifie-les dans la documentation actuelle de chaque portail** et teste avec leurs outils (CrazyGames a un mode « QA tool », Poki un « Inspector »).
- Les portails demandent souvent un jeu en **anglais** par défaut : le jeu choisit la langue du navigateur (français, anglais, espagnol, portugais).
- Contenu : certains portails refusent la violence réaliste ; le style du jeu est cartoon, mais signale le thème (crime, armes) lors de la soumission.
- Poids : environ 1 Mo sans compter la bibliothèque 3D (600 Ko).

## Bande-annonce
`marketing/bande-annonce-verticale.mp4` : 16 secondes, 1080x1920, musique et bruitages du jeu. Prête pour TikTok, YouTube Shorts et Reels. Ajoute ta voix ou un texte d'accroche dans CapCut si tu veux.
