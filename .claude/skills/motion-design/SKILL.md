---
name: motion-design
description: Génère par le code les éléments de motion design d'un montage — intro 3D HyperFrames (HTML/CSS/GSAP → MP4) et carte de fin Remotion (React → MP4) — paramétrés avec la technique, la discipline, le @ et la couleur, puis les insère dans le montage combat (accroche → intro → analyses → carte de fin).
---

# Motion design (HyperFrames + Remotion)

Installation une fois : `cd motion && npm install && npx hyperframes browser ensure`
(skills officiels : `npx hyperframes skills update motion-graphics`, `npx remotion skills add`).

## Automatique
`python -m autovid combat …` utilise les deux si `motion/node_modules` existe (`--no-motion` pour s'en passer) :
- **Intro HyperFrames** `motion/hyperframes/intro/index.html` (2,4 s) : sol néon en perspective, titre qui se
  retourne en 3D, flash d'impact. Placée **après l'accroche** (ne jamais retarder l'accroche).
- **Carte de fin Remotion** `motion/remotion/Outro.jsx` (3 s) : ABONNE-TOI, curseur qui clique « S'abonner »,
  cloche, teaser de la partie 2, « enregistre et essaie ».
- Les sons (montée, impact, déclics) sont calés sur leurs animations dans `combat.build_audio`.

## À la main
```bash
cd motion/hyperframes/intro && npx hyperframes render --quality delivery \
   --variables '{"title":"MEIA-LUA","tag":"CAPOEIRA • ANATOMIE","handle":"@moi"}' --output ../../../sorties/motion/intro.mp4
cd motion && npx remotion render remotion/index.jsx Outro ../sorties/motion/outro.mp4 \
   --props='{"handle":"@moi","teaser":"PRÓXIMO : A ESQUIVA"}' --browser-executable="$(npx hyperframes browser path)"
```

## Modifier le design
- Intro : suivre les skills `hyperframes` / `hyperframes-core` (une timeline GSAP en pause, `npx hyperframes lint`
  puis `check` avant le rendu), et regarder des images du rendu avant de valider.
- Carte de fin : skill `remotion-best-practices` ; aperçu interactif avec `npx remotion studio remotion/index.jsx`.
- Garder 1080×1920, 30 i/s, et les durées `motion.INTRO_DUR` / `motion.OUTRO_DUR` alignées sur les compositions.
