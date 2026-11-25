# Analyse des deux vidéos de référence

Deux Reels/Shorts verticaux (1080×1920, 60 i/s, en portugais du Brésil), même créateur, même recette. Chacun fait la promo d'un **pack gratuit de 11 skills Claude Code**.

| | Vidéo 1 | Vidéo 2 |
|---|---|---|
| Durée | 46 s | 43 s |
| Sujet | **YouTube Agent** : 11 skills `/yt-*` qui font tourner une chaîne YouTube | **Replica** : 11 skills `/replica-*` qui clonent n'importe quelle app |
| Hook (0–3 s) | « O Claude acabou de *matar* o YouTube » | « Agora é só você *clonar* qualquer app usando o Claude » |
| Formule de hook | Annonce de mort (« X vient de tuer Y ») | Promesse impossible |
| Preuve | page GitHub du pack, « totalmente de graça » | page GitHub « The Replica skill », « de graça » |
| Corps | une skill = un visuel = 2–4 s : script (21 formules de hook), package (titre + miniature notés /100), edit (coupes), comment, plan (semaine), viral (démonte et recrée) | recon (démonte), build (reconstruit), test (cherche les erreurs), diff (ce qui manque), puis « l'entrepreneur » : lit 140 avis et résout les problèmes, paiement PIX « PAGO » |
| Virage | « Você já recebe um vídeo viral, escrito na sua voz » | « um clone de qualquer app » → l'entrepreneur va plus loin |
| CTA | « abre o Claude Code e cola esse link » | « comenta CLONE que eu te envio na DM » (lead magnet) |
| Fond graphique | beige clair `#EDEBE7`, mascotte pixel rouge | gris anthracite `#1C1C1C`, personnages en papier découpé |

## Grammaire visuelle commune
- **Split-screen** : motion design sur ~52 % du haut, facecam sur le bas. Ponctuellement plein écran facecam (émotion) ou plein écran graphique (gros chiffre « 11 », « 140 »).
- **Sous-titres mot à mot** dans une pastille noire posée sur la ligne de coupe ; **un seul mot en rouge** `#E8392B` par segment (le mot qui porte le sens : *matar*, *11*, *Replica*, *CLONE*).
- **Un changement visuel toutes les 2 à 4 s**, jamais de plan fixe plus long.
- Objets récurrents : fenêtres de terminal « Claude Code », compteurs animés, grilles d'icônes (une par skill), barres, classements, cartes notées.
- Petits libellés gris en capitales au-dessus des visuels (« ELA TE AJUDA A DECIDIR », « COLA NO CLAUDE CODE »).

## Structure (gabarit réutilisable)
```
0–3 s    HOOK      promesse choc, 1 mot rouge
3–8 s    PREUVE    nom du produit + « gratuit »
8–11 s   COMPTE    « ce n'est pas 1 skill, c'est 11 »
11–38 s  CORPS     1 skill / 2–4 s, chacune avec son visuel
38–42 s  PAYOFF    le résultat final pour le spectateur
42–46 s  CTA       une seule action (coller un lien / commenter un mot)
```

## Ce que ce dépôt en tire
- [`projet-video/`](projet-video/) — 5 agents (stratège, scénariste, monteur, découpeur de Shorts, motion designer), le pack **AutoVid YouTube Agent** (11 skills `/yt-*` en français) + un gabarit **Remotion** qui rend des vidéos dans ce format exact à partir d'un JSON.
- [`projet-app/`](projet-app/) — 7 agents (chercheur produit, architecte, designer, dev web, dev mobile, QA, lanceur) et le pack **Replica** (11 skills `/replica-*` en français) pour concevoir, construire, tester, monétiser et lancer une application.

---

# Vidéo 3 — « Claude est nul en montage vidéo, sauf si… » (effets sonores)

TikTok vertical de 52 s (576×1024, en français, @henriexploria). Facecam plein écran, sous-titres mot à mot blancs sans pastille, quelques encarts (logos d'outils, bulles « Claude ne peut pas entendre », « Comment Claude sait-il où le placer ? »).

**Script reconstitué** (d'après les sous-titres incrustés) : Claude est nul en montage vidéo sauf avec trois outils ; le visuel est devenu bon, mais les effets sonores « sonnent comme du contenu IA bâclé ».
1. **Openverse** : accès à des millions de sons libres que l'agent cherche et télécharge seul.
2. **Earshot** : « Claude ne peut pas entendre » → l'outil écoute les sons, choisit celui qui marche, en génère un sinon.
3. **Real SFX** : regarde le montage, repère chaque moment qui demande un son (« un whoosh quand un élément apparaît ») et le place au bon endroit.
CTA : « commente SFX sous ma vidéo sur Instagram ».

**Vérification des outils** : Openverse existe (API publique `api.openverse.org/v1/audio/`, sons sous licences Creative Commons). Earshot existe : [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot), licence MIT — catalogue de 922 sons rendus par code, écoute par modèles, serveur MCP (20 outils), et deux skills dont **`real-sound`** (bande-son à partir de vrais enregistrements placés sur les instants calculés depuis le code de l'animation). Aucun outil public ne s'appelle « Real SFX » : `real-sound` correspond à ce que la vidéo décrit, sans certitude que ce soit le même.

## Ce que le dépôt en tire
- **Placement des sons sans « voir » la vidéo** : nos deux générateurs connaissent déjà l'instant exact de chaque apparition (scènes Remotion, segments de séance). Les sons sont donc placés de façon déterministe — c'est le rôle annoncé de « Real SFX », sans outil supplémentaire.
  - `projet-video` : whoosh à chaque nouveau visuel, impact sur les gros chiffres, pop sur les listes, clics sur les lignes de terminal (`remotion/src/sfx.ts`) ; agent `sound-designer`.
  - `projet-senior-us` : profil doux et rare — souffle au début des exercices, cloche de repos, cloche de fin (`sfx_plan` dans `autovideo.py`) ; agent `designer-sonore`.
- **Openverse** : `outils/chercher-sons.py` (dans les deux projets) cherche et télécharge un son, refuse les licences non commerciales, écrit le crédit à côté du fichier ; le projet senior le reprend dans la description YouTube. À lancer sur le PC (API non joignable depuis une session cloud).
- **Sons par défaut** synthétisés et versionnés (`projet-video/remotion/public/sfx/`, `projet-senior-us/sons/`) pour que tout fonctionne sans téléchargement.
- **Earshot** est intégré aux deux projets vidéo : skills `earshot` et `real-sound` copiées (commit 7a7f7c5, MIT), script `outils/installer-earshot.sh` / `.ps1` qui l'installe sur le PC et déclare son serveur MCP. Testé ici : installation, génération de sons, serveur MCP (20 outils, appel `make`). Les modèles d'écoute (≈ 1,1 Go) n'ont pas pu être téléchargés depuis la session cloud. Les sons par défaut des deux projets sont désormais générés par earshot.

---

# Vidéo 4 — « Ce skill Claude crée… » (7 styles de création MP4)

TikTok vertical de 43 s (576×1024, @henriexploria, même créateur que la vidéo 3). Facecam, sous-titres mot à mot, et pour chaque style une carte `Skill.md` (nom du style) avec un exemple de vidéo générée tenu devant la caméra.

**Script reconstitué** : sept skills Claude, chacun présenté par « ce skill Claude crée… »
| Carte | Promesse |
|-------|----------|
| Motion | des animations en motion design haut de gamme, comme un designer professionnel |
| Claymation | des publicités en pâte à modeler, comme une vraie agence de pub |
| Explainer | des vidéos explicatives complètes, comme un documentaire Netflix |
| Singing | des histoires chantées, comme une comédie musicale Disney |
| Commercial | des pubs IA à fort taux de conversion, cinématographiques, comme une vraie équipe de tournage |
| Animation | des films d'animation en 3D, comme un vrai studio hollywoodien |
| Cartoon | des épisodes complets de dessins animés pour enfants, comme une série |
CTA : « commente Compétences sous ma vidéo sur Instagram et je te les envoie avec le guide complet en message privé ».

**Constat** : ces sept skills ne sont pas publiés (aimant à prospects). Les exemples montrés (personnages en pâte à modeler, brocoli qui chante, prisonnier, chat cartoon) sont des vidéos générées par des modèles payants (type Seedance / Kling / ElevenLabs), que Claude orchestre sans les produire lui-même.

## Ce que le dépôt en tire
`projet-video/styles/STYLES.md` associe à chaque style l'équivalent public le plus proche, vérifié (dépôt cloné et lu, commit épinglé) : skills `claymation-ads` et `seedance` (fal.ai, payants, sans licence publiée → téléchargés sur le PC, jamais copiés ici), `talking-explainer` (MIT, présentateur cartoon avec lip-sync), et OpenMontage (AGPL-3.0, 13 pipelines dont `animated-explainer`, `animation`, `cinematic`, `character-animation`, `documentary-montage`). Le style **Singing** n'a pas d'équivalent public : il est assemblé à partir des outils d'OpenMontage (musique avec voix + lip-sync). Installation par `outils/installer-styles.sh` / `.ps1` ; agent `directeur-creatif` pour choisir l'outil, estimer le coût et faire valider avant toute génération payante.
