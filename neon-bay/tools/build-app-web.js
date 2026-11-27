#!/usr/bin/env node
// Crée app-android/www/ : les fichiers du jeu embarqués dans l'application Android (Capacitor).
// Différences avec dist-web/ (le site) :
//  - 100 % hors ligne : polices copiées en local (pas de Google Fonts), pas de service worker ;
//  - seulement ce que le jeu charge : les .glb listés dans NB_DATA.MODELS (pas les copies .glb.js
//    ni les aperçus), le film d'intro paysage et la bande-annonce (pas la version verticale : l'app est en paysage) ;
//  - pas de Néon Studio ;
//  - ajoute js/native.js (bouton Retour, pause en arrière-plan).
// Usage : node tools/build-app-web.js   (appelé aussi par tools/build-android.sh)
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const root = path.join(__dirname, '..');
const app = path.join(root, 'app-android');
const out = path.join(app, 'www');
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });
const copy = (rel, dest = rel) => {
  const s = path.join(root, rel);
  if (!fs.existsSync(s)) throw new Error('Fichier manquant : ' + rel);
  fs.mkdirSync(path.dirname(path.join(out, dest)), { recursive: true });
  fs.cpSync(s, path.join(out, dest), { recursive: true });
};

// 1. scripts du jeu (dans l'ordre de index.html) + vendor utilisés
const JS = ['data.js', 'i18n-dict.js', 'i18n.js', 'audio.js', 'store.js', 'portal.js', 'engine.js', 'native.js'];
JS.forEach(f => copy('js/' + f));
const VENDOR = ['three.min.js', 'GLTFLoader.js', 'postfx.js', 'SkeletonUtils.js', 'RoomEnvironment.js'];
VENDOR.forEach(f => copy('vendor/' + f));
copy('icons/icon-192.png');
copy('privacy.html');

// 2. modèles : uniquement les .glb déclarés dans js/data.js (chargés par fetch depuis https://localhost)
const sandbox = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(root, 'js/data.js'), 'utf8'), sandbox);
const models = Object.values(sandbox.window.NB_DATA.MODELS || {});
models.forEach(u => copy(u));
copy('models/CREDITS.md');

// 3. médias : film d'intro (paysage) et bande-annonce
['media/intro.mp4', 'media/bande-annonce.mp4'].forEach(f => copy(f));
// fichiers audio facultatifs déclarés dans AUDIO_FILES
Object.values(sandbox.window.NB_DATA.AUDIO_FILES || {}).forEach(u => copy(u));

// 4. polices en local (paquets npm @fontsource, licence OFL)
const fontsDir = path.join(out, 'fonts');
fs.mkdirSync(fontsDir, { recursive: true });
let css = '';
for (const [pkg, weights] of [['bungee', [400]], ['chakra-petch', [400, 600, 700]]]) {
  const base = path.join(app, 'node_modules', '@fontsource', pkg);
  if (!fs.existsSync(base)) throw new Error('Polices absentes : lance « npm install » dans app-android/');
  for (const w of weights) {
    let c = fs.readFileSync(path.join(base, w + '.css'), 'utf8');
    c = c.replace(/,\s*url\(\.\/files\/[^)]+\.woff\) format\('woff'\)/g, ''); // woff2 suffit (WebView Chrome)
    c.replace(/url\(\.\/files\/([^)]+\.woff2)\)/g, (m, f) => { fs.copyFileSync(path.join(base, 'files', f), path.join(fontsDir, f)); return m; });
    css += c.replace(/url\(\.\/files\//g, 'url(./') + '\n';
  }
}
fs.writeFileSync(path.join(fontsDir, 'fonts.css'), css);

// 5. index.html : même tête que tools/build-web.js, sans manifeste ni service worker, polices locales
let html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
html = html.replace(/<link rel="preconnect"[^>]*>\n?/g, '')
  .replace(/<link rel="stylesheet" href="https:\/\/fonts\.googleapis\.com[^>]*>/, '<link rel="stylesheet" href="fonts/fonts.css">');
if (/fonts\.googleapis|https?:\/\/(?!www\.w3\.org)/.test(html.replace(/<style>[\s\S]*?<\/style>/g, ''))) console.warn('Attention : index.html contient encore une adresse externe');
html = html.replace('<script src="js/engine.js"></script>', '<script src="js/engine.js"></script>\n<script src="js/native.js"></script>');
const head = `<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">\n<meta name="theme-color" content="#0d0b1a">\n<link rel="icon" href="icons/icon-192.png">\n`;
html = head + html.replace(/<\/style>/, '</style>\n</head>\n<body>') + '\n</body>\n</html>\n';
fs.writeFileSync(path.join(out, 'index.html'), html);

// taille totale
const size = d => fs.readdirSync(d, { withFileTypes: true }).reduce((n, e) => n + (e.isDirectory() ? size(path.join(d, e.name)) : fs.statSync(path.join(d, e.name)).size), 0);
console.log('app-android/www/ prêt : ' + models.length + ' modèles, ' + (size(out) / 1048576).toFixed(1) + ' Mo');
