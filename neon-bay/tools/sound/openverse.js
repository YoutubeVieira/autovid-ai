#!/usr/bin/env node
// Recherche (et téléchargement) de sons libres sur Openverse, avec la licence et l'attribution de chaque son.
// node tools/sound/openverse.js "whoosh" [--license cc0,by] [--n 10] [--min 0.2] [--max 4] [--download marketing/sons/candidats/whoosh]
// Sans --download : affiche les résultats (titre, durée, licence, auteur, lien). Avec : télécharge et écrit CREDITS-SONS.md.
// Licences acceptées par défaut : cc0 et by (usage commercial autorisé ; « by » impose de créditer l'auteur).
const fs = require('fs'), path = require('path'), https = require('https');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const q = process.argv[2] && !process.argv[2].startsWith('--') ? process.argv[2] : null;
if (!q) { console.error('Usage : node tools/sound/openverse.js "mot-clé" [--license cc0,by] [--n 10] [--download dossier]'); process.exit(1); }
const lic = arg('license', 'cc0,by'), n = +arg('n', 10), dmin = +arg('min', 0), dmax = +arg('max', 30), dl = arg('download', null);
const UA = 'NeonBayStudio/1.0 (outil de sound design)';
const get = (url, bin) => new Promise((res, rej) => {
  https.get(url, { headers: { 'User-Agent': UA } }, r => {
    if (r.statusCode >= 300 && r.statusCode < 400 && r.headers.location) return get(r.headers.location, bin).then(res, rej);
    if (r.statusCode !== 200) { r.resume(); return rej(new Error('HTTP ' + r.statusCode + ' pour ' + new URL(url).host)); }
    const ch = []; r.on('data', c => ch.push(c)); r.on('end', () => res(bin ? Buffer.concat(ch) : JSON.parse(Buffer.concat(ch).toString())));
  }).on('error', rej);
});
(async () => {
  const url = `https://api.openverse.org/v1/audio/?q=${encodeURIComponent(q)}&license=${lic}&page_size=${Math.min(50, n * 3)}&mature=false`;
  const d = await get(url);
  const list = d.results.filter(r => { const s = (r.duration || 0) / 1000; return s >= dmin && s <= dmax; }).slice(0, n);
  for (const r of list) console.log(`${((r.duration || 0) / 1000).toFixed(1).padStart(5)} s  ${(r.license + ' ' + (r.license_version || '')).padEnd(8)} ${r.title.slice(0, 50).padEnd(50)}  ${r.creator || '?'}  (${r.source})`);
  if (!dl) { console.log(`\n${d.result_count} résultats au total. Ajoute --download <dossier> pour télécharger.`); return; }
  fs.mkdirSync(dl, { recursive: true }); const credits = path.join(dl, 'CREDITS-SONS.md');
  if (!fs.existsSync(credits)) fs.writeFileSync(credits, '# Sons téléchargés depuis Openverse\n\n| Fichier | Titre | Auteur | Licence | Source |\n|---|---|---|---|---|\n');
  let ok = 0;
  for (const r of list) {
    const ext = (r.filetype || path.extname(new URL(r.url).pathname).slice(1) || 'mp3').replace(/[^a-z0-9]/gi, ''), file = path.join(dl, `${r.id.slice(0, 8)}.${ext}`);
    try { fs.writeFileSync(file, await get(r.url, true)); ok++;
      fs.appendFileSync(credits, `| ${path.basename(file)} | ${r.title.replace(/\|/g, '/')} | ${r.creator || '?'} | ${r.license.toUpperCase()} ${r.license_version || ''} | ${r.foreign_landing_url} |\n`);
    } catch (e) { console.error('Téléchargement refusé : ' + e.message + ' (autoriser ce domaine dans les réglages réseau de la session)'); }
  }
  console.log(`\n${ok}/${list.length} fichiers téléchargés dans ${dl} · crédits : ${credits}`);
})().catch(e => { console.error('Erreur : ' + e.message); process.exit(1); });
