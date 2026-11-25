# Les 7 styles de création MP4

D'après la vidéo « Ce skill Claude crée… » (@henriexploria) : 7 skills (`Skill.md`) — Motion, Claymation, Explainer, Singing, Commercial, Animation, Cartoon. Ces skills ne sont pas publiés (ils s'obtiennent en commentant « Compétences » sur Instagram). Ce catalogue donne, pour chaque style, l'équivalent **public** le plus proche, installé par `outils/installer-styles.sh` (Windows : `.ps1`).

| Style | Promesse de la vidéo | Outil installé | Clés / coût | Licence |
|-------|----------------------|----------------|-------------|---------|
| **Motion** | motion design haut de gamme | gabarit Remotion de ce projet (gratuit) ; `seedance` pour un rendu « verre liquide » 3D | aucune ; Seedance : `FAL_KEY` (payant) | ce dépôt ; seedance : non précisée |
| **Claymation** | pubs en pâte à modeler | skill `claymation-ads` : image produit + angle → pub verticale (personnages, images clés, voix, animation, montage ffmpeg), 5 validations avant de dépenser | `FAL_KEY` + `ELEVENLABS_API_KEY` (payant) | non précisée |
| **Explainer** | vidéo explicative « documentaire » | skill `talking-explainer` (présentateur cartoon qui parle, vrai lip-sync, 1920×1080 60 i/s) ; pipeline OpenMontage `animated-explainer` ; `documentary-montage` (images d'archives libres) | talking-explainer : aucune (votre voix) ; OpenMontage : selon fournisseurs, voie gratuite possible | MIT ; AGPL-3.0 |
| **Singing** | histoire chantée « comédie musicale » | **aucun skill public** : chaîne OpenMontage `music_gen` avec voix (`force_instrumental=false`, ElevenLabs Music) → personnage → `lip_sync` / `kling_lip_sync` | `FAL_KEY` ou ElevenLabs, `KLING_API_KEY` (payant) | AGPL-3.0 |
| **Commercial** | pub IA cinématographique | skill `seedance` (Seedance 2.0 : texte/image/référence → vidéo) ; pipeline OpenMontage `cinematic` | `FAL_KEY` (payant) | non précisée ; AGPL-3.0 |
| **Animation** | film d'animation 3D « studio » | pipelines OpenMontage `animation` (Three.js, motion graphics) et `cinematic` (mondes 3D) | voie gratuite possible ; vidéo IA en option | AGPL-3.0 |
| **Cartoon** | épisodes de dessin animé pour enfants | pipeline OpenMontage `character-animation` (personnages réutilisables, rigs, poses, rendu SVG/Canvas/Remotion) ; `talking-explainer` | voie gratuite possible | AGPL-3.0 ; MIT |

## Ce qu'il faut savoir avant de lancer un style payant
- Claude ne fabrique pas l'image animée lui-même : les styles Claymation, Commercial, Singing (et la vidéo IA d'OpenMontage) appellent des modèles de génération (Seedance, Kling, ElevenLabs) **facturés à l'usage** sur votre compte fal.ai / Kling / ElevenLabs. Les skills demandent une validation avant les étapes coûteuses ; OpenMontage plafonne le budget (10 $ par défaut, confirmation au-delà de 0,50 $ par opération).
- Les clés vont dans `.env` (créé depuis `outils/env.exemple`, ignoré par git). Ne jamais les écrire dans le chat ni dans un fichier versionné.
- Licences : `claymation-ads` et `seedance` n'ont pas de licence publiée (usage personnel toléré, pas de redistribution) : ils sont téléchargés sur votre PC et **jamais** copiés dans ce dépôt. OpenMontage est AGPL-3.0 : utilisable librement, mais un logiciel qui le modifie et est distribué ou servi en ligne doit publier ses sources.
- Pour une chaîne monétisée, vérifier les conditions commerciales de chaque modèle utilisé (fal.ai, Kling, ElevenLabs) — elles changent souvent.

## Installation
```bash
bash outils/installer-styles.sh            # skills + OpenMontage téléchargé
bash outils/installer-styles.sh --setup    # + dépendances d'OpenMontage (Python, Node, TTS gratuite Piper)
```
Tout atterrit dans `externes/` et `.claude/skills/<style>` (ignorés par git), aux versions testées. Relancer Claude Code dans `autovid-shorts/` ensuite, puis : « fais une pub claymation pour … » → l'agent `directeur-creatif` choisit l'outil.

Les skills **animation-studio** (dessin animé, explainer, lyric video, avec musique synthétisée par code, sans clé) et **codesign** (animer un visuel, vidéo de lancement) sont aussi disponibles dans votre compte Claude : l'agent les propose quand aucun service payant n'est voulu.
