# Les 15 voix de la série (gratuites, hors-ligne)

Définies dans `packs/voices/cast.json`, utilisables avec `python3 packs/voices/tts.py script.txt --out voix/ --cast <n>`. Échantillons : `packs/voices/samples/voix_NN_*.mp3` (même phrase pour toutes). La colonne « Whisper » indique si un contrôle de reconnaissance vocale (Whisper small) retrouve le texte : c'est un test d'**intelligibilité**, pas de beauté — à écouter pour juger.

| N° | Groupe | Voix | Source | Licence | Whisper |
|---|---|---|---|---|---|
| 1 | Homme | Narrateur grave (défaut) | Supertonic 3, voix 9 | code MIT, modèle OpenRAIL-M¹ | comprise |
| 2 | Homme | Homme posé | Supertonic 3, voix 8 | idem¹ | comprise |
| 3 | Homme | Jeune homme | Supertonic 3, voix 6 | idem¹ | comprise |
| 4 | Homme | Voix chaude | Piper « tom » | AGPLv3 ⚠ à vérifier avant monétisation | comprise |
| 5 | Femme | Narratrice douce | Supertonic 3, voix 0 | idem¹ | comprise |
| 6 | Femme | Femme dynamique | Supertonic 3, voix 2 | idem¹ | comprise |
| 7 | Femme | Voix claire | Kokoro `ff_siwis` | CC BY 4.0 (mention : SIWIS, Univ. d'Édimbourg) | comprise |
| 8 | Femme | Mamie (grave, lente, tremblante) | Supertonic voix 4 + effets | idem¹ | comprise |
| 9 | Enfant | Petit garçon | Supertonic voix 5, hauteur +5, timbre rapproché | idem¹ | comprise |
| 10 | Enfant | Petite fille | Supertonic voix 1, hauteur +3 | idem¹ | à réécouter |
| 11 | Bébé | Bébé | Supertonic voix 1, hauteur +9, lent | idem¹ | comprise |
| 12 | Animal | Chat | Supertonic voix 3, hauteur +7, vibrato | idem¹ | comprise |
| 13 | Animal | Chien (rauque) | Supertonic voix 7, saturation | idem¹ | comprise |
| 14 | Animal | Oiseau (aigu, rapide) | Supertonic voix 2, hauteur +10 | idem¹ | partiellement |
| 15 | Animal | Ours / dinosaure | Supertonic voix 9, hauteur −6 | idem¹ | comprise |

¹ Licence du modèle Supertonic notée d'après les notes de l'utilisateur (usage commercial permis) : à reverifier sur la fiche officielle.

## Limites honnêtes
- Il n'existe pas de modèle libre français de vraies voix d'enfant, de bébé ou d'animaux : les n° 9 à 15 sont des voix d'adultes **transformées** (hauteur, timbre, effets). Elles sonnent « dessin animé ». Pour de vrais rires, pleurs et cris, voir `packs/sfx` (rires, pleurs de bébé, cris de peur, rugissements, synthétisés).
- Prononciation : Supertonic lit les lettres. À vitesse naturelle (1,0–1,05) « habitant » est bien compris ; au-delà de 1,2 la diction se dégrade (mesuré avec Whisper). Corrections : `packs/voices/prononciation.json` + `tts.py --verify --asr-model <whisper>` (essaie plusieurs écritures et garde la mieux comprise).
- Voix Microsoft (Vivienne…) et VoiceStudio : non disponibles dans cet environnement (voir `packs/voices/edge_local.py` pour un usage sur ton ordinateur).
