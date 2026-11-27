# Analyse des 2 videos de reference

Mesures faites avec ffprobe/ffmpeg (scene detection, silencedetect, ebur128) + planches de vignettes.
**Limite** : aucune transcription n'a ete possible dans l'environnement (pas de modele de reconnaissance vocale), l'analyse porte donc sur la structure, le rythme, l'image et le son, pas sur les mots dits.

| | Video A (making-of Blender) | Video B (monteur dans Claude) |
|---|---|---|
| Duree | 13,8 s | 39,9 s |
| Format | 1080x1920, 30 fps, AV1 | 1440x2560, 30 fps, AV1 |
| Audio | AAC stereo 48 kHz | AAC stereo 44,1 kHz |
| Loudness integree | **-14,1 LUFS** (LRA 1,5, crete -4,4 dBFS) | **-14,1 LUFS** (LRA 1,6, crete -1,5 dBFS) |
| Silences > 0,3 s | aucun | 1 seul de 0,44 s (a 16 s) : les pauses sont coupees |
| Plans (seuil 0,08) | ~27 changements, dont une rafale de 5 en 0,4 s a 12,4-12,8 s | peu de coupes franches (1,5 / 2,6 / 3,5 / 29,6 / 32,5 s), le rythme vient des animations internes |

## Structure narrative

**A - revelation « derriere l'image »** : hook face camera (0-2,2 s) -> alternance face cam / captures ecran Blender (maillage, rig en T-pose, animation) / rendu final -> rafale de coupes rapides en fin -> le rendu final sert de recompense. Mise en page en split-screen (face cam en haut, ecran en bas, separateur orange) puis plein cadre sur le rendu.

**B - tutoriel en etapes** : hook face cam avec bandeau de titre (0-3,5 s) -> sequence de maquettes d'interface animees, **une etape toutes les ~3,3 s**, chacune avec un sous-titre en 2 niveaux (ligne en gras + ligne en italique serif) -> retour face cam avec sous-titres mot par mot, mot cle en jaune -> **CTA** avec bouton « Saiba Mais » et curseur qui clique.

## Recette extraite (encodee dans `editor/presets/shortform_9x16.json`)

1. Vertical 9:16, 30 fps, sortie 1080x1920.
2. Hook dans les 3 premieres secondes (texte en bandeau + visuel de promesse).
3. Zero temps mort : silences > 0,35 s coupes, on garde 0,08 s de respiration.
4. Un plan ne depasse pas ~3,5 s : sinon jump-cut avec punch-in (cycle de zoom 1.0 / 1.12 / 1.0 / 1.22).
5. Sous-titres gros, 1 a 3 mots, mot cle en couleur, zone basse-centrale.
6. Mastering **-14 LUFS**, crete <= -1,5 dBTP, dynamique serree (LRA ~1,5 a 11).
7. Structure : hook -> etapes/preuves -> payoff -> CTA.

## Ce que le monteur autonome fait deja / ne fait pas encore

Fait (teste sur ces 2 videos) : analyse, coupe des silences, jump-cuts + zoom, sous-titres ASS depuis un SRT, bandeau d'accroche, musique avec ducking, normalisation -14 LUFS, controle qualite automatique.
Pas encore : transcription integree (necessite `pip install faster-whisper`, sinon fournir un `.srt`), choix de b-roll, effets sonores, detection automatique du mot cle par IA (aujourd'hui : mot le plus long du groupe).

---

# Video C - « Caragua Pixel » (@caraguapixel)

Mesures: 35,3 s, 720x1280, 30 fps, H.264, AAC 44,1 kHz. Loudness **-14,1 LUFS** (LRA 1,4, crete -1,6 dBFS), un seul silence: la **queue de 1,8 s** a 33,5-35,3 s. Pas de transcription possible (voix non analysee), analyse sur l'image, le texte a l'ecran et les mesures.

**Concept**: jeu de gestion pixel-art vu de dessus - « chaque abonne = un habitant » d'une ville vide (Dia 1 - A cidade vazia, 0/100 moradores). Video d'ouverture d'une serie qui transforme la croissance de la chaine en jeu.

**Structure (horodatages approximatifs)**
- 0-5 s: hook + regle du jeu (« essa cidade tem... aqui, cada seguidor = um morador », badges `+1 MORADOR`, `+1 EMPREGO`)
- 5-12 s: mecanique (`SEGUIU = MORADOR ✓`, champ de commentaire « ANA, PROFESSORA » -> le personnage « VOCE » arrive avec un metier)
- 12-19 s: postes a pourvoir (professeur, medecin, sauveteur, pecheur) avec etiquettes `VAGA: ...` sur la carte
- 19-24 s: la Chambre: `15` cadeiras vazias -> les 15 premiers = vereadores
- 25-28 s: prefeitura `TRANCADA` (cadenas) -> 28-32 s: objectif `0/100` moradores pour l'election du maire
- 32-35 s: carton-titre « CARAGUA PIXEL - A cidade dos seguidores - Dia 1 » + queue silencieuse

**Montage**
- Image: un seul « monde » (carte pixel-art) filme par des mouvements de camera lents; peu de coupes franches (9 changements de plan > 0,1, soit ~2,5 par 10 s), mais un **changement de texte toutes les ~0,5 s** dans la zone sous-titre: le rythme vient du texte, pas des coupes.
- **Synchro mot/visuel**: chaque mot ou groupe de 1-3 mots appelle un element a l'ecran au meme instant (« MEDICA » -> hopital, « SALVA-VIDAS » -> plage, « TRANCADA » -> cadenas).
- **HUD permanent** en haut (jour, compteur 0/100, habitants/emplois) qui donne l'impression de jeu; badges colores (jaune = +1 habitant, vert = +1 emploi, rouge = bloque).
- **Sous-titres**: police pixel majuscules, blanc a contour noir epais, mot cle en **jaune**, 1-3 mots, tiers bas de l'ecran; le titre-chiffre (« 15 », « 0 / 100 ») est un gros bloc jaune.
- Transitions courtes (fondu enchaine d'environ 0,2-0,3 s visible entre deux legendes), zooms sur le personnage et sur les lieux.
- Son: -14,1 LUFS comme les videos A et B, voix serree, queue silencieuse de 1,8 s en fin de video (pas de musique mesurable en pause).

**Ce qui est reutilisable dans `autoeditor`**
1. Les 3 videos de reference sont a -14,1 LUFS avec une dynamique serree: la cible -14 LUFS du preset est confirmee.
2. Rythme de texte ~1 groupe de 1-3 mots toutes les 0,5-1 s (le preset actuel `max_words: 3` convient; ajouter une option de police pixel et une couleur de mot cle par mot pre-defini).
3. HUD / badges / chiffres en gros bloc: **pas encore gere** par le monteur (necessite des calques graphiques, ex. Remotion/HyperFrames, ou des overlays ASS/PNG).
4. Queue silencieuse finale de ~1,8 s + carton-titre de fin: a ajouter comme option `outro`.


---

# Compte de reference TikTok « Dans cette ville... » (captures d'ecran)

Source: 7 captures de la grille du profil (miniatures de 20 K a 1,9 M de vues). Palette mesuree par k-means sur 84 miniatures (`docs/palette_analysis.py`), reprise telle quelle dans `blender/blocky/palette_ref.json` (couleurs par defaut de la ville et des personnages).

## Couleurs (mesurees)
| Role | Couleur | Part des pixels |
|---|---|---|
| Rouge | `#CC130E` | 3,0 % |
| Bleu ciel | `#198AE6` | 5,1 % |
| Bleu profond | `#1B478C` | 2,8 % |
| Or / jaune | `#E59C18` | 1,9 % |
| Vert | `#267722` | 3,3 % |
| Pierre creme / gris chaud / blanc casse | `#DEC5A1` `#9F978C` `#F6F5F5` | 7,8 % / 7,9 % / 8,0 % |
| Ocre, brun, brun fonce (bois, brique, peaux) | `#C18552` `#895818` `#582811` | 4,9 % / 6,0 % / 6,9 % |
| Route, pave, quasi noir | `#4E4D55` `#73716E` `#120E10` | 9,5 % / 9,7 % / 9,3 % |
| Bleu nuit | `#1E2841` | 8,0 % |

Saturation moyenne 0,48; luminosite moyenne 0,44; **seules 5 % des miniatures sont sombres** (la serie est surtout diurne, ciel bleu franc), 45 % sont claires. Regle: cinq teintes pleines (rouge, bleu, or, vert, brun) sur un decor de pierre creme et de gris chaud; pas de pastel.

## Style d'image
- Figurines en blocs (corps cubique, tete cubique, joues roses, yeux noirs allonges) rendues en 3D avec matieres plastique/metal, ombres douces et **profondeur de champ faible** (fond flou, effet maquette).
- Decor de petite ville francaise: facades en pierre creme, volets verts/bleus/rouges, mairie avec drapeaux, guirlandes de fanions, lampadaires, places pavees; variantes thematiques (temple grec, montagne, desert, ferme, nuit de fete sous la pluie).
- Texte integre au decor (panneaux « INTERDIT DE SE BATTRE », affiches « DISPARU », « EN DIRECT », compteurs lumineux), pastille doree « EPISODE 2 », sous-titres mot par mot (une seule parole a l'ecran) en blanc gras a contour noir vers 65 % de la hauteur.

## Plans (types releves)
1. **Gros plan visage** (yeux, joues, sourire) qui remplit le cadre; 2. **objet heros** plein cadre (piece d'or avec tete de mort, panneau « NON », couronne flottante, jauge de vitesse); 3. **rue en perspective centrale** symetrique, lampadaires qui guident l'oeil vers le batiment; 4. **contre-plongee** sur un personnage ou une foule en fete; 5. **plan d'ensemble de place** avec foule ou alignement de personnages; 6. **coupe en section** (maison posee sur un puits/sous-sol); 7. plans de reaction rapproches (visages inquiets, bouches ouvertes); 8. gros plan sur panneau/affiche pour lire l'information.
Rythme: une idee par plan, 1 a 2 s, alternance gros plan / plan large, coupes sur les mots forts.

## Applique dans le depot
- Couleurs par defaut: `blender/blocky/palette_ref.json` (ville, vetements, peaux, volets, drapeaux).
- Style: profondeur de champ (f/3,2), piece d'or heros « 100 », contre-plongees, gros plans, rase-sol, vue du ciel, travelling rapide (15 plans pour 20 s dans `episode01.py`).
- Montage rapide (`pixel_game` -> `fx`): zoom « punch » a chaque coupe, secousse, flou de balayage, flash sur les paliers.
