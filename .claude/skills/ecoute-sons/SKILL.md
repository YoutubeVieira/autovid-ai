---
name: ecoute-sons
description: Écouter et classer des fichiers son (via ffmpeg) pour choisir le meilleur bruitage pour un usage donné (whoosh, impact, sirène, moteur, montée, pluie, grondement, pop, signature), puis le couper et le normaliser. À utiliser quand plusieurs sons candidats existent et qu'il faut choisir celui qui colle vraiment, au lieu de prendre le premier au hasard.
---

# Écoute et choix des sons

Outil : `neon-bay/tools/sound/ecoute.js`. Un agent ne peut pas entendre : cet outil mesure ce qu'une oreille jugerait.

```bash
cd neon-bay
node tools/sound/ecoute.js marketing/sons/candidats/whoosh --pour whoosh
node tools/sound/ecoute.js marketing/sons/candidats/whoosh --pour whoosh --garder marketing/sons/whoosh.wav
```

Mesures par fichier :
- durée utile, sans les silences de début et de fin ;
- attaque : temps pour atteindre le maximum ;
- brillance : centroïde spectral **pondéré par le volume** ;
- régularité : variation du volume ;
- volume intégré (LUFS).

Un score sur 100 compare ces mesures au profil attendu de l'usage (`--pour`).

`--garder` copie le meilleur son, coupé de ses silences et normalisé à −14 LUFS (WAV 44,1 kHz stéréo), là où le rendu vidéo l'attend.

## Fiabilité (testé sur les bruitages générés)
- **Bien reconnus :** whoosh, impact, sirène, pluie, montée, pop.
- **Moins fiables :** moteur, grondement et signature finale, qui se confondent avec une sirène aux sons proches.
- Pour ces trois-là, comparer des candidats d'un même type, par exemple tous les résultats d'une recherche « car engine ».
- Regarder aussi les mesures, pas seulement le score.
