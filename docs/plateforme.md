# Plateforme AutoVid : ce qui est branché, ce qu'il faut installer

Vérifié en octobre 2026. ⚠️ = non confirmé dans une doc officielle, à revérifier.

## Ce qui tourne tout seul (aucun compte nécessaire)
| Brique | Rôle | Outil |
|---|---|---|
| Analyse du mouvement | squelette 33 points, 2 personnes, masque de silhouette | MediaPipe Pose Landmarker (local, gratuit) |
| Détection des coups | pic de vitesse poignet / cheville / genou, nommage (direct, crochet, uppercut, high/middle/low kick, genou) | `autovid/combat.py`, `autovid/anatomy.py` |
| Effets | ralenti fondu, flash blanc, arrêt sur image, zoom, tremblement, aberration RVB, silhouette en avant, chaîne cinétique colorée, cercles sur les articulations, angles, traînée, étiquettes d'anatomie, barre de progression, grain, vignette | OpenCV + Pillow + ffmpeg |
| Son | beat drill/trap généré (libre de droits), whoosh, impact, montée (riser), déclic, ticks, ducking, −14 LUFS | `autovid/sfx.py` |
| Téléphone ↔ PC | page web locale + QR code ; dossier surveillé | `python -m autovid serve` / `watch` |

## Connecteurs et outils externes
| Outil | Ce qui existe vraiment | Utilisation dans AutoVid |
|---|---|---|
| **Claude (API Anthropic)** | vision + sortie JSON structurée | `--ai claude` : Claude regarde 3 images par coup et écrit nom, accroche, muscles, astuce |
| **ElevenLabs** | Speech-to-Text `scribe_v2` avec temps par mot ; Sound Effects (`/v1/sound-generation`) ; Music (`/v1/music`) | mode `talk` : sous-titres + suppression des « euh » et faux départs. SFX/musique ElevenLabs : possibles en remplacement des sons générés (pas encore branchés) |
| **Canva** | serveur MCP officiel `https://mcp.canva.com/mcp` (OAuth ; offre Pro/Teams requise ⚠️) : créer des designs, exporter en image/PDF | `.mcp.json` du dépôt → Claude Code propose de l'activer ; sert aux **miniatures / couvertures** (skill `publier`), pas au montage vidéo |
| **CapCut** | **pas d'API ni de MCP officiels**. Outils non officiels (pyJianYingDraft, CapCutAPI, capcut-mate) qui écrivent des brouillons et cassent à chaque mise à jour | non branché. Pour retoucher : importer le MP4 dans CapCut |
| **Google Gemini** | API de compréhension vidéo (upload d'un MP4, réponses horodatées ; 1 image/s par défaut, trop peu pour des coups rapides ⚠️) | pas encore branché ; candidat pour un 2e avis sur les techniques |
| **Google Flow / Veo** | Flow = appli sans API. Veo 3.1 via l'API Gemini (`veo-3.1-generate-preview` ⚠️, clips de 8 s en 9:16) | pas branché ; utile pour générer des plans d'intro / B-roll |
| **Google Antigravity** | IDE à agents ; lit le format Agent Skills `SKILL.md` (dossier `.agent/skills/` ⚠️) | `scripts/install.sh` copie les skills dans `.agent/skills/` |
| **HyperFrames (HeyGen)** | rendu HTML/CSS/GSAP → MP4, plugin Claude Code | optionnel : motion design avancé (intros, titres 3D). Commande dans `scripts/install.sh` |
| **Video-Use (browser-use)** | skill Claude Code de montage par transcription (ElevenLabs) | optionnel, même rôle que notre mode `talk` |
| **Descript** | « Eye Contact » (regard caméra), sans API | à faire avant AutoVid si tu lis un téléprompteur |

## 8K : à savoir avant de l'utiliser
- TikTok et Instagram recompressent en **1080p** ; YouTube Shorts accepte jusqu'à la **4K** (2160×3840).
- Une vidéo filmée en 1080p ou 4K passée en 8K est **agrandie**, pas plus détaillée.
- Donc : `--resolution 1080` pour TikTok/Reels, `--resolution 4k` pour un master YouTube. `8k` existe (4320×7680) mais ne sert qu'à l'archive et prend beaucoup plus de temps.

## Lier le téléphone et le PC
1. **Wi-Fi local (le plus simple)** : sur le PC `python -m autovid serve`, ouvre la page, scanne le QR code avec le téléphone. Tu filmes ou choisis la vidéo, tu lances, tu récupères le MP4 (bouton Partager → TikTok / Instagram directement depuis le téléphone).
2. **Dossier synchronisé (automatique)** : Google Drive, OneDrive, iCloud ou Syncthing sur le téléphone et le PC, puis
   `python -m autovid watch ~/Drive/AutoVid/entree ~/Drive/AutoVid/sorties --handle @toncompte`.
   Chaque vidéo déposée depuis le téléphone ressort montée dans `sorties`, visible sur le téléphone.
3. **Hors de chez toi** : Tailscale (VPN gratuit) sur les deux appareils, puis l'adresse Tailscale du PC à la place de l'IP Wi-Fi. N'ouvre pas le port sur Internet.

## Monétisation : les règles qui comptent
- Monte **tes** vidéos (ou celles dont tu as les droits) : un réupload de combats d'autrui expose au Content ID et à la démonétisation, même avec une analyse par-dessus.
- La musique générée est libre de droits ; une musique du commerce peut bloquer la monétisation.
- Format produit par défaut (reprend les codes des deux vidéos de référence) : accroche dès la 1re seconde, une analyse toutes les ~5 s, 25–40 s au total, CTA « abonne-toi / enregistre ». Pense aux séries « PARTIE 1/2/3 ».
