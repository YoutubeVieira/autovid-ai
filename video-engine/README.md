# Video engine : vidéos verticales « carte animée »

Moteur de vidéos 9:16 (1080×1920, 30 i/s) de géopolitique et d'histoire sur carte, dans le style des shorts « carte + voix off + sous-titres jaunes ».
Tout est piloté par un fichier JSON de scènes : on change le sujet sans toucher au code.

Construit avec [Remotion](https://www.remotion.dev) (React → MP4). Voir la [licence de Remotion](https://www.remotion.dev/docs/license) avant un usage commercial en entreprise.

## Chaîne de fabrication

```
projects/<sujet>.json ──► tools/tts.mjs ──► voix par scène + durées réelles
                     └──► tools/build-props.mjs ──► .cache/<sujet>.props.json (durée de scène = durée de voix)
                                              └──► tools/render.mjs ──► out/<sujet>.mp4
```

```bash
cd video-engine
npm install
npm run assets                      # une fois : contours des pays (déjà fournis dans public/geo)
node tools/make.mjs franca-reino-unido     # voix + durées + rendu
npm run studio                      # aperçu interactif dans le navigateur
node tools/render.mjs <sujet> --frame 120  # une image de contrôle (out/<sujet>-f120.png)
npm test
```

## Voix off

Les voix sont déclarées dans `voices.json` ; un projet en choisit une avec `"voice": "<id>"` (ou `VOICE=<id>` en ligne de commande).
Pour l'instant : **`test`** (voix locale espeak, robotique, pour essayer le montage). Pour en ajouter une, ajoutez une entrée, par exemple une voix Gemini (même principe que `second-souffle-pwa/tools/generate-audio.js`) :

```json
"sulafat": { "label": "Sulafat (Gemini)", "provider": "gemini", "voiceName": "Sulafat", "model": "gemini-3.8-flash-tts" }
```

Les voix Gemini demandent `GEMINI_API_KEY` (jamais dans le code). Les fichiers audio sont conservés par empreinte (texte + voix) : relancer ne régénère que les scènes modifiées.

## Écrire un projet (`projects/<sujet>.json`)

Une scène = une phrase de voix off + un état de carte :

```json
{
  "id": "s03",
  "text": "Paris cai em junho, e o governo francês foge para o sul.",
  "camera": { "lon": 1.5, "lat": 47.2, "zoom": 3.0 },
  "fills": { "FRA": "split" },
  "items": [
    { "kind": "tag", "text": "PARIS", "at": [2.35, 48.86], "delay": 0.3 },
    { "kind": "bubble", "text": "NÃO VAMOS RESISTIR!", "at": [-0.58, 44.84], "dy": -110, "delay": 2.2 }
  ]
}
```

- `camera` : centre (lon/lat) et zoom, interpolés d'une scène à l'autre.
- `fills` : code pays (ADM0_A3 : `FRA`, `GBR`, `DEU`…) → `flag`, `land`, `gray`, `red`, `yellow`, `split` (France 1940 : zone occupée rouge, zone libre jaune). L'état est **cumulatif** d'une scène à l'autre, avec fondu.
- `items` : `icon` (hexagone + emoji), `flagBadge` (hexagone drapeau gbr/fra/deu), `person` (médaillon + nom), `bubble` (texte ou emoji), `tag`, `title`. Placés par `at: [lon, lat]` (suivent la carte) ou `screen: [x, y]`, avec `dx`/`dy` en pixels, `delay`/`until` en secondes.
- Sous-titres : générés depuis `text`, par groupes de 3 mots (`subtitleWords`), répartis au prorata des lettres sur la durée de la voix.

Ajouter un drapeau : `src/flags.tsx`. Ajouter un portrait : déposer l'image dans `public/portraits/` et mettre `"img": "portraits/churchill.jpg"` (sans image, une silhouette est dessinée).

## Limites actuelles

- **Fond de carte stylisé** (terres vert sombre sur océan dégradé), pas une vraie photo satellite. Les sources d'imagerie haute résolution ne sont pas accessibles depuis l'environnement de développement ; une image reprojetée peut s'ajouter dans `Ocean`/`MapLayer`.
- **Portraits** : silhouettes par défaut. Les photos d'archives sont à fournir (vérifier les droits).
- **Sous-titres** : répartition approximative, pas un alignement mot à mot. Un alignement réel (Whisper ou équivalent) peut remplacer `chunkTimings`.
- **Zone libre de la France de 1940** : tracée à la main, approximative.
- **Fond sonore** et **écran de fin** (logo de chaîne) non inclus.
- La voix `espeak` ne sert qu'aux essais.
