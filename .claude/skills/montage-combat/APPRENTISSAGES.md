# Apprentissages (mis à jour par le skill feedback-montage)

## 2026-10-19 — retours sur le test roda (capoeira filmée de haut)
- **Pas de pauses longues** : style par défaut `--style fluide` (ralenti autour du geste + micro-arrêt de 0,25 s,
  la vidéo continue pendant les explications). L'ancien mode à arrêts sur image reste en `--style analyse`.
- **Sons comme la vidéo réaction** (pull counter) : kit `--kit reaction` = phonk/drill 808, cowbell, impacts sub-boom,
  souffles graves ; profil réglé sur la mesure de la référence (~72 % sub, 19 % basses, 8 % médiums).
- **Explications visuelles = couleurs et traits** (comme les références) : traits lumineux sur les membres
  (vert = membre qui travaille, orange = appui), ellipse jaune sous l'appui, trajectoire en arc, flèche courbe pour
  les déplacements, étoile d'impact. Pas de grandes étiquettes : titre 2 lignes + 1 ligne risque + 1 ligne muscles.
- **Zoom précis sur un membre** : cadrer extrémité + articulation intermédiaire (pied+genou, main+coude).
- Modèle « Gemini » (martelo / meia-lua) : titres courts 2 lignes, écran partagé « application réelle » à ajouter.
- Toujours vérifier la planche contact ET quelques images en grand avant d'envoyer.

## 2026-10-19 — 2e retour
- **Traits et flèches sur une seule partie précise** : uniquement le membre qui travaille (jambe qui frappe,
  ou bras qui protège / qui porte l'aú) + ses articulations + UNE flèche qui suit son extrémité.
  Plus de trait sur la jambe d'appui ni de flèche sur le bassin. Ellipse seulement sous la main de l'aú.

## 2026-10-19 — skills Melvynx installés
- Avant de rendre, passer accroches, voix off, titres et description au filtre `studio-script humanize`
  (pas de « secret », pas de question-révélation, une seule demande en fin de vidéo, 5 hashtags max).
  `tests/test_humanize.py` le vérifie sur nos modèles de texte.
- Pas de lignes ni de squelette : seulement la COULEUR sur le membre qui travaille (silhouette coloriée, sinon
  bande douce). Pas de ronds un peu partout : UN seul rond, sur l'articulation clé, pendant la pause du contact.
  Petite flèche de trajectoire de temps en temps, c'est tout (comme la vidéo modèle n° 2).
- Bruits selon le coup (comme la vidéo n° 1) : contact sur le corps = coup sourd + claque, sac / pao = « boum »
  lourd + cuir + chaîne, dans le vide = swish ; rotation (meia-lua, armada, aú) = souffle qui tourne.

## 2026-10-19 — sujet qui n'est pas humain
- Une créature d'IA (dinde-dinosaure) a reçu un faux « UPPERCUT / attention au poignet » : le squelette se pose
  sur tout ce qui a deux pattes. Le mode combat vérifie maintenant avec un détecteur d'objets (COCO « person »)
  et refuse sous 50 %. Ces clips passent par `python -m autovid fun` (accroche, ralenti, bruitages, mention IA).
