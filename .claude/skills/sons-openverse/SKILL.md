---
name: sons-openverse
description: Chercher et télécharger des sons libres (CC0 ou CC-BY) sur Openverse pour les vidéos et le jeu Néon Bay, avec la licence et l'attribution de chaque fichier. À utiliser quand il faut un vrai bruitage enregistré (moteur, sirène, foule, pluie, explosion, whoosh) plutôt qu'un son synthétisé.
---

# Sons libres via Openverse

Outil : `neon-bay/tools/sound/openverse.js` (Node, sans dépendance).

```bash
cd neon-bay
node tools/sound/openverse.js "police siren" --n 10                 # liste : durée, licence, titre, auteur, source
node tools/sound/openverse.js "whoosh" --license cc0 --max 2 --download marketing/sons/candidats/whoosh
```

- Licences par défaut `cc0,by` : usage commercial autorisé. **CC-BY impose de créditer l'auteur** : le fichier `CREDITS-SONS.md` du dossier est rempli automatiquement, à reprendre dans les crédits du jeu ou la description de la vidéo.
- Ne jamais utiliser `by-nc`, `by-nd`, `by-sa` ni `sampling+` pour un produit vendu.
- `--min` / `--max` filtrent la durée en secondes.

## Réseau
La recherche (`api.openverse.org`) passe. Les fichiers sont hébergés ailleurs : `cdn.freesound.org` (la plupart) et `upload.wikimedia.org`. Si le téléchargement est refusé (HTTP 403 ou 429), il faut autoriser ces domaines dans les réglages réseau de l'environnement ; en attendant, utiliser le skill `bruitages-video` (sons générés).

## Suite logique
1. Télécharger 5 à 10 candidats par type dans `marketing/sons/candidats/<type>/`.
2. Les faire « écouter » et classer par le skill `ecoute-sons`, qui garde le meilleur en `marketing/sons/<type>.wav`.
3. Rendre les vidéos avec `--sons marketing/sons` (skill `bruitages-video`).
