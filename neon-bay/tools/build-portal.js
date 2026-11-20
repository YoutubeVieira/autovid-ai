#!/usr/bin/env node
// Crée les versions portails : dist-portal/poki/ et dist-portal/crazygames/ (+ un .zip de chaque)
// Usage : node tools/build-portal.js
const fs = require('fs'), path = require('path'), { execSync } = require('child_process');
const root = path.join(__dirname, '..');
const SDK = { poki: 'https://game-cdn.poki.com/scripts/v2/poki-sdk.js', crazygames: 'https://sdk.crazygames.com/crazygames-sdk-v3.js' };
for (const kind of Object.keys(SDK)) {
  const out = path.join(root, 'dist-portal', kind);
  fs.rmSync(out, { recursive: true, force: true }); fs.mkdirSync(out, { recursive: true });
  for (const rel of ['js', 'vendor', 'icons', 'audio']) { const s = path.join(root, rel); if (fs.existsSync(s)) fs.cpSync(s, path.join(out, rel), { recursive: true }); }
  let html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  html = html.replace('<script src="vendor/three.min.js"></script>', `<script src="${SDK[kind]}"></script>\n<script>window.NB_PORTAL = '${kind}';</script>\n<script src="vendor/three.min.js"></script>`);
  html = `<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n` + html.replace(/<\/style>/, '</style>\n</head>\n<body>') + '\n</body>\n</html>\n';
  fs.writeFileSync(path.join(out, 'index.html'), html);
  try { execSync(`cd "${out}" && python3 -c "import shutil; shutil.make_archive('../neon-bay-${kind}', 'zip', '.')"`); } catch (e) { console.log('zip impossible :', e.message); }
  console.log('dist-portal/' + kind + ' prêt');
}
