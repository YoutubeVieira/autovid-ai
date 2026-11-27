#!/usr/bin/env node
// Crée dist-web/ : la version à mettre en ligne (site + application Android).
// Usage : node tools/build-web.js
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..'), out = path.join(root, 'dist-web');
fs.rmSync(out, { recursive: true, force: true });
const copy = (rel) => { const s = path.join(root, rel); if (!fs.existsSync(s)) return; fs.cpSync(s, path.join(out, rel), { recursive: true }); };
['js', 'vendor', 'icons', 'audio', 'models', 'media', 'manifest.webmanifest', 'privacy.html'].forEach(copy);
const stamp = Date.now().toString(36);
fs.writeFileSync(path.join(out, 'sw.js'), fs.readFileSync(path.join(root, 'sw.js'), 'utf8').replace('__BUILD__', stamp));
let html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const head = `<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<meta name="theme-color" content="#0d0b1a">\n<link rel="manifest" href="manifest.webmanifest">\n<link rel="icon" href="icons/icon-192.png">\n<link rel="apple-touch-icon" href="icons/icon-192.png">\n`;
html = head + html.replace(/<\/style>/, '</style>\n</head>\n<body>') +
  `\n<script>if ('serviceWorker' in navigator) addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));</script>\n</body>\n</html>\n`;
fs.writeFileSync(path.join(out, 'index.html'), html);
// Néon Studio : éditeur d'animations et de cinématiques
{ const st = fs.readFileSync(path.join(root, 'studio.html'), 'utf8');
  fs.writeFileSync(path.join(out, 'studio.html'), `<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n` + st.replace(/<\/style>/, '</style>\n</head>\n<body>') + '\n</body>\n</html>\n'); }
// lien de vérification Android (à remplir avec l'empreinte donnée par la Play Console)
const al = path.join(root, 'android', 'assetlinks.json');
if (fs.existsSync(al)) { fs.mkdirSync(path.join(out, '.well-known'), { recursive: true }); fs.copyFileSync(al, path.join(out, '.well-known', 'assetlinks.json')); }
console.log('dist-web/ prêt (' + stamp + ')');
