---
name: short-carte-finance
description: Écrire un short finance/géopolitique de 60-90 s pour la chaîne et le produire avec le moteur video-engine (carte animée, chiffres qui défilent, voix, sous-titres, bruitages). À utiliser une fois la fiche d'impact validée.
---

# Short « carte animée » finance

Entrée : fiche `veille/fiches/<slug>.md`. Sortie : `video-engine/projects/<slug>.json` + vidéo `out/<slug>.mp4`.

## Structure du script (60-90 s, 8 à 14 scènes)
1. **Accroche (0-3 s)** : une question concrète pour un foyer. Pas de présentation.
2. **Contexte** (1-2 scènes) : l'événement mondial sur carte.
3. **Chaîne cause→effet** (4-6 scènes) : un maillon par scène, une idée par phrase (≤ 18 mots), un visuel par maillon (flèche de flux, pays coloré, chiffre).
4. **Effet France** : carte de France + chiffre qui défile + exemple de foyer.
5. **Incertitude** : ce qu'on ne sait pas.
6. **Chute** : une idée à retenir + « Contenu éducatif, pas un conseil en investissement. »
Phrases courtes, tutoiement ou vouvoiement selon la chaîne (`narrateur-finance-famille-antihype` fixe le ton s'il est disponible). Texte original : jamais repris d'une vidéo source.

## JSON du moteur
```json
{
  "title": "…", "theme": "finance", "lang": "fr-FR", "voice": "test",
  "faits": [ { "id": "f1", "claim": "…", "value": "…", "source": "Banque de France, …", "url": "https://…", "date": "2026-10" } ],
  "scenes": [ {
    "id": "s01", "text": "…", "faits": ["f1"],
    "camera": { "lon": 2.5, "lat": 47, "zoom": 2.6 }, "move": "zoomin",
    "fills": { "FRA": "flag", "DEU": "red" },
    "items": [
      { "kind": "stat", "value": 3.2, "decimals": 1, "suffix": " %", "label": "inflation, 2026", "screen": [540, 640], "delay": 0.6 },
      { "kind": "arrow", "from": [lon, lat], "to": [lon, lat], "delay": 1.0 }
    ] } ]
}
```
- **Tout chiffre** dans `text` ou dans un item `stat` exige `"faits": [...]` sur la scène ; `npm test` refuse sinon.
- Cartes : `camera` + `fills` (codes pays ADM0_A3 : FRA, DEU, USA, CHN, RUS…) ; flux : `arrow` ; lieux : `ping` ; événements : `burst`, `impacts` (secousse), `flash`.
- Géographie hors Europe : le fond actuel couvre -25°→45° E, 27°→72° N. Pour le Moyen-Orient, la Chine, les USA, il faut étendre `make-basemap.py` et `fetch-assets.mjs` (voir README) : le signaler et le faire avant d'écrire la scène.
- Ne jamais mettre de portrait ou image dont les droits ne sont pas établis.

## Fabrication
```bash
cd video-engine && npm test                      # JSON, faits, voix, fichiers
node tools/make.mjs <slug>                        # voix → durées → rendu (long : lancer en arrière-plan)
node tools/render.mjs <slug> --frame 120          # image de contrôle ; LA REGARDER avant le rendu complet
```
Contrôles avant livraison : relire la voix, vérifier chaque chiffre à l'écran contre `faits`, volume (pas de saturation), lisibilité des sous-titres, mention AMF en fin.
