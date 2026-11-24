#!/usr/bin/env node
// Prépare une copie figée du studio pour le rendu TikTok : marketing/tiktok/.web/
// (studio.html + js/studio.js + vendor + models, et une page index.html qui ne charge que la musique).
// On ne touche pas à dist-web/, qui suit le jeu en cours d'édition.
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..', '..', '..'), out = path.join(root, 'marketing', 'tiktok', '.web');
fs.rmSync(out, { recursive: true, force: true }); fs.mkdirSync(path.join(out, 'js'), { recursive: true });
for (const d of ['vendor', 'models']) fs.cpSync(path.join(root, d), path.join(out, d), { recursive: true });
for (const f of ['studio.js', 'audio.js', 'data.js']) fs.copyFileSync(path.join(root, 'js', f), path.join(out, 'js', f));
const st = fs.readFileSync(path.join(root, 'studio.html'), 'utf8');
fs.writeFileSync(path.join(out, 'studio.html'), '<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n' + st.replace(/<\/style>/, '</style>\n</head>\n<body>') + '\n</body>\n</html>\n');
fs.writeFileSync(path.join(out, 'index.html'), '<!doctype html>\n<html lang="fr"><head><meta charset="utf-8"></head><body>\n<script src="js/data.js"></script>\n<script src="js/audio.js"></script>\n</body></html>\n');
console.log('Copie de rendu prête : ' + out);
