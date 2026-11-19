#!/usr/bin/env node
// Crée dist/index.html : un seul fichier autonome, prêt à envoyer sur itch.io, ton site, etc.
// Usage : node tools/build-standalone.js
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
let html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
for (const f of ['js/data.js', 'js/audio.js', 'js/engine.js']) {
  const js = fs.readFileSync(path.join(root, f), 'utf8').replace(/<\/script/g, '<\\/script');
  html = html.replace(`<script src="${f}"></script>`, () => `<script>\n${js}\n</script>`);
}
const out = `<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n` +
  html.replace(/<\/style>/, '</style>\n</head>\n<body>') + '\n</body>\n</html>\n';
fs.mkdirSync(path.join(root, 'dist'), { recursive: true });
fs.writeFileSync(path.join(root, 'dist', 'index.html'), out);
console.log('dist/index.html', (out.length / 1024).toFixed(0) + ' Ko');
