# Où télécharger (légal, usage commercial) – à faire sur ton PC
Règle : noter pour chaque fichier **l'URL + la licence** (voir `packs/animals/importer_sons.py`, colonne licences.csv). Refuser tout « NC » (non commercial), « ND » ou licence inconnue.

## Sons, bruitages, ambiances
| Site | Licence | Notes |
|---|---|---|
| freesound.org | Filtre **« Creative Commons 0 »** | le plus grand ; animaux, foule, pas, portes. Compte gratuit. CC-BY = crédit à écrire |
| pixabay.com/sound-effects | Licence Pixabay (commerciale, sans crédit) | rapide, propre |
| mixkit.co/free-sound-effects | Licence Mixkit (commerciale) | bonne qualité |
| kenney.nl/assets (catégorie Audio) | CC0 | sons de jeu/UI, parfait pour le style jeu |
| sonniss.com (GDC Game Audio Bundle) | royalty-free commercial | énormes packs pro |
| commons.wikimedia.org (catégorie « Sounds of animals ») | domaine public / CC (lire chaque fiche) | vrais animaux |
| À ÉVITER | BBC Sound Effects (non commercial), xeno-canto (surtout NC), ESC-50 (NC) | |

## Musiques
- pixabay.com/music (licence Pixabay), incompetech.com (Kevin MacLeod, CC BY : crédit obligatoire), freemusicarchive.org (filtrer licences commerciales), YouTube Audio Library (YouTube Studio) – vérifier l'usage hors YouTube.
- **TikTok** : la bibliothèque de sons dans l'appli est la plus sûre pour un compte TikTok ; ajouter la musique à la publication.

## Polices (toutes à licence OFL = commercial OK)
fonts.google.com : **Bangers**, **Lilita One**, **Luckiest Guy**, **Titan One**, **Fredoka**, **Baloo 2**, **Bungee**, **Press Start 2P** (déjà dans `packs/fonts`). Autres : fontshare.com, fontsquirrel.com (filtre « commercial use »). DaFont : seulement les polices marquées « 100 % gratuit ».

## Images, textures, 3D, animations
polyhaven.com (CC0 : HDRI ciels, textures, modèles), ambientcg.com (CC0 textures), kenney.nl (CC0 modèles 3D, icônes), quaternius.com (CC0 personnages/props), mixamo.com (animations gratuites, compte Adobe gratuit), pexels.com / pixabay.com (vidéos et images libres).

## Emojis / icônes
Twemoji (CC BY 4.0), OpenMoji (CC BY-SA : crédit + partage identique), lucide.dev (ISC), Kenney icons (CC0).

## Comment me les donner
1. Mets les fichiers dans un dossier `a_importer/` + un `licences.csv` (`fichier;espece;licence;auteur;source`).
2. Envoie-les sur la branche (GitHub > Add file > Upload files, dossier `packs/a_importer/`) ; je les nettoie (mono, silences, volume), les range, génère les crédits et les branche dans les épisodes.
3. Polices : copie les `.ttf` dans `packs/fonts/` (avec le fichier OFL.txt).
