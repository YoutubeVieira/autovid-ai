---
name: controle-qualite-video
description: Porte de contrôle avant le montage final et la publication : mesures automatiques (durée, audio, silences, images noires, mentions), relecture des faits, regard sur les images, écoute, licences des médias. À utiliser après un rendu et avant toute livraison, pour une longue comme pour un short.
---

# Contrôle qualité avant montage final

Rien n'est « prêt » sans cette porte. Un seul ÉCHEC ou un seul fait « non confirmé » bloque.

## 1. Mesures automatiques
`cd video-engine && node tools/qa.mjs out/<slug>-final.mp4 --projet <slug> --cible <secondes>`
Contrôle : durée, résolution, présence et niveau de l'audio (pic > −1 dB = saturation possible), silences > 2,5 s, images noires, poids ; puis `npm test`, mentions légales (finance), faits « à confirmer », médias avec source.
Verdicts : `PRÊT POUR LE MONTAGE FINAL`, `À RELIRE`, `BLOQUÉ`. L'outil ne juge ni le fond, ni le style, ni l'écoute.

## 2. Faits (agent `verificateur-faits`)
Chaque chiffre à l'écran et dit à la voix = une ligne du registre `faits` ; sources rouvertes quand les domaines sont autorisés ; les faits « a_confirmer » sont soit confirmés, soit retirés, soit dits « à confirmer » dans la vidéo.

## 3. Regard sur les images
Rendre 8 à 12 images de contrôle réparties (`node tools/render.mjs <slug> --frame N`) et les regarder : texte lisible et non masqué, chiffres justes, bandeaux sans chevauchement avec les sous-titres, mention de source visible sur chaque média, aucune image « simulée » présentée comme réelle.

## 4. Voix et son
Écouter ou faire écouter : prononciation des chiffres et sigles, changement de voix entre scènes si deux modèles ont été mélangés, volume des bruitages par rapport à la voix. Si l'écoute est impossible (session de développement), **le dire** : « mesuré, non écouté ».

## 5. Licences et droits
Chaque média déposé a une source, une licence et une mention (affichée + description). Voix et musique : pas de musique protégée. Aucune copie d'une autre chaîne.

## 6. Compte rendu
Tableau : contrôle | résultat | preuve (fichier, image, mesure). Distinguer ce qui est **vérifié**, **mesuré**, **non vérifié**. Mettre à jour `serie/serie.json` seulement si la porte est passée.
