# Analyse des deux vidéos de référence (« ADN » de montage)

Mesures obtenues avec `python -m autovid analyze` (données brutes : `docs/references/*.json`)
puis vérifiées image par image.

## Format commun aux deux vidéos

| | Vidéo 1 — « Most peak knockouts » (BinCombat) | Vidéo 2 — « Adrian Broner pull counter » (Killa x Pablo) |
|---|---|---|
| Résolution | 1080 × 1920, vertical 9:16 | 1080 × 1920, vertical 9:16 |
| Cadence | 30 i/s | 30 i/s |
| Durée | 15,98 s | 10,87 s |
| Codec (fichier reçu) | AV1 ~3,5 Mb/s + AAC HE stéréo 44,1 kHz | AV1 ~3,3 Mb/s + AAC HE stéréo 44,1 kHz |
| Loudness | −14,3 LUFS (LRA 2,4) | −14,1 LUFS (LRA 3,2) |
| Son | musique seule, pas de voix, aucun silence | musique seule, pas de voix, aucun silence |
| Coupes | 14 coupes, ≈ 53 / min | 9 coupes, ≈ 50 / min |

AV1 / AAC HE : c'est le ré-encodage de la plateforme (Facebook / Instagram). À l'export on vise
H.264 High, 1080×1920, 30 i/s, AAC 192 kb/s, −14 LUFS : c'est ce que produit `autovid`.

## Vidéo 1 — compilation « technique → mise en situation »

**Structure (7 techniques en 16 s)** : chaque technique dure ≈ 2,3 s = 2 plans.
1. démonstration solo à la salle (plein cadre, filmé au téléphone, grand angle) ;
2. la même technique en vrai combat (extrait paysage posé dans le 9:16).

| t (s) | titre (petite ligne jaune / grande ligne blanche) |
|---|---|
| 0 – 2,6 | MMA / SMART BACK KICK |
| 2,6 – 5,1 | KARATE SOLO MUAYTHAI / KNOCKOUT COMBO |
| 5,1 – 7,2 | MMA KNOCKOUT / DESTROY + KNOCKOUT |
| 7,2 – 9,6 | MUAY TIPS KICK |
| 9,6 – 11,6 | MMA / SPIN HOOK KICK |
| 11,6 – 13,7 | MUAYTHAI / SET UP HEAD KICK |
| 13,7 – 16 | QUESTION MARK KICK |

**Rythme** : coupes quasi métronomiques toutes les 1,07 – 1,27 s (médiane 1,08 s). La musique est à
≈ 99 BPM → 1 temps = 0,60 s : **un plan ≈ 2 temps**. Les coupes ne tombent pas sur les attaques
de la musique (7 %) : la grille est régulière, le monteur a coupé au temps, pas au son.
Pas de transition : uniquement des cuts secs.

**Habillage**
- Titre en 2 lignes centré en haut (zone 7 – 15 % de la hauteur) : surtitre catégorie **jaune**
  (≈ 60 px), titre **blanc** (≈ 90 px), police manuscrite type marqueur/pinceau, contour noir fin +
  ombre portée. Le titre change **sec** au changement de technique, sans animation.
- Filigrane « BinCombat » gris semi-transparent, centré en bas (≈ 89 % de la hauteur), permanent.
- Extraits de combat paysage : image réduite à la largeur, descendue sous le titre, haut assombri
  en dégradé noir, bas en fond flouté (ou bandes noires sur certains plans).

**Étalonnage** : léger contraste/saturation, image nette ; pas de zoom, pas de vitesse modifiée.

## Vidéo 2 — tutoriel « step-by-step » avec hook

**Structure (10,9 s)**
1. **Hook 0 – 3,33 s** : extrait viral (Adrian Broner qui montre la technique) en haut, désaturé et
   très contrasté, et en bas le créateur qui regarde son téléphone (format « réaction », incrustation
   sur fond flouté). Rien n'est encore expliqué : on crée la curiosité.
2. **Flash blanc à 3,33 s** (2 images surexposées) → titre **PULL COUNTER / STEP-BY-STEP**.
3. **Étapes numérotées**, un plan chacune (≈ 0,7 – 1,3 s) : `1. WIDE STANCE`, `2. REAR FOOT`,
   `3. LEAN BACK`, `4. CROSS`, intercalées avec des preuves en combat / sparring.
4. **CTA final** « SAVE AND TRY » sur le coup dans le sac, puis retour au plan du hook (boucle).

**Rythme** : plans plus courts (médiane 0,78 s), 67 % des coupes sur une attaque audio : ici la coupe
suit la musique.

**Motion design / annotations**
- **Masque coloré qui suit le corps** (rotoscopie) : la jambe arrière passe orange puis vert fluo, et
  sur « 4. CROSS » la couleur verte remonte la chaîne pied → hanche → buste → bras (on montre le
  transfert de force). C'est de la segmentation (type SAM / MediaPipe), pas un simple calque.
- **Cercle jaune en perspective** au sol autour du pied (`2. REAR FOOT`).
- **Flèche verte en pointillés** qui indique le recul (`3. LEAN BACK`).
- **Cercle vert néon** sur le point d'impact du sac (CTA).
- Bâton/guide orange au sol pour l'écartement des pieds (`1. WIDE STANCE`).

**Typographie** : sans-serif condensée très grasse blanche (famille Impact / Anton / Bebas), ombre
noire épaisse ; sous-titre en manuscrit. Les titres d'étape apparaissent instantanément en haut.

**Étalonnage** : contraste et saturation forts, **sur-accentuation (sharpen) très marquée**, look
« HDR ».

## Ce que les deux vidéos ont en commun (la recette)
1. 9:16, 30 i/s, −14 LUFS, musique seule, ≤ 16 s.
2. Une coupe toutes les ~1 s (≈ 50 coupes/min), calée sur 2 temps musicaux.
3. Le texte vit dans le **tiers haut**, le filigrane dans le bas : le centre reste libre pour l'action.
4. Chaque idée = démonstration propre + preuve réelle.
5. Les extraits horizontaux sont réutilisés dans le 9:16 avec fond flouté ou bandes.

## Ce que `autovid` reproduit / ne reproduit pas (encore)
| Élément | Statut |
|---|---|
| Format, cadence, export, loudness −14 LUFS | ✅ |
| Coupe calée sur le tempo (détection BPM) | ✅ |
| Choix automatique du moment d'action dans chaque rush | ✅ (pic de mouvement) |
| Plein cadre / fond flouté / bandes noires automatiques | ✅ |
| Titres 2 lignes, étapes numérotées, filigrane, CTA, pop | ✅ (ASS / libass) |
| Flash blanc, zoom « punch », poussée, ralenti | ✅ |
| Cercles / ellipses d'annotation qui pulsent | ✅ (position donnée dans le brief) |
| Flèches animées | ❌ à ajouter |
| Masque coloré qui suit un membre | ❌ demande un modèle de segmentation (SAM 2, MediaPipe) |
| Hook « réaction » (2 vidéos superposées) | ❌ à ajouter |
