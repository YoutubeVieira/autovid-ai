#!/usr/bin/env node
// Extrait les textes français visibles (données + interface) vers i18n/strings-fr.json
const fs = require('fs'), path = require('path'), vm = require('vm');
const root = path.join(__dirname, '..');
const out = new Set();
const add = s => { if (typeof s !== 'string') return; s = s.replace(/\s+/g, ' ').trim(); if (s.length < 2 || !/[A-Za-zÀ-ÿ]{2}/.test(s)) return; if (/^(#|https?:|Key|Digit|Arrow|js\/|audio\/|icons\/|[a-z_]+$)/.test(s)) return; if (/[{};]|=>|px|rgba|var\(|\.js|\.png/.test(s)) return; out.add(s); };
// données
const win = {}; vm.runInNewContext(fs.readFileSync(path.join(root, 'js/data.js'), 'utf8'), { window: win });
const D = win.NB_DATA;
for (const r of D.REGIONS) { add(r.name); add(r.country); add(r.tagline); add(r.vip); add(r.vip.split(',')[0]); r.places.forEach(add); r.factions.forEach(f => add(f.name)); }
for (const l of D.LEVELS) { add(l.t); add(l.s); }
Object.values(D.STEP_LABEL).forEach(add);
for (const w of D.WEAPONS.concat(D.GEAR)) { add(w.name); add(w.desc); }
for (const c of Object.values(D.OUTFITS)) { add(c.label); c.items.forEach(i => add(i[1])); }
// interface : chaînes entre guillemets et textes des gabarits HTML
const src = fs.readFileSync(path.join(root, 'js/engine.js'), 'utf8') + '\n' + fs.readFileSync(path.join(root, 'index.html'), 'utf8');
for (const m of src.matchAll(/'((?:[^'\\\n]|\\.){2,200})'/g)) { const s = m[1].replace(/\\u2019/g, '’').replace(/\\'/g, "'"); if (/[ éèàêçôîûÉÈÀ]/.test(s)) add(s); }
for (const m of src.matchAll(/`([^`]{2,2000})`/g)) {
  const parts = m[1].replace(/\$\{[^}]*\}/g, '\u0000').split(/<[^>]+>|\u0000/);
  for (const p of parts) add(p.replace(/&nbsp;/g, ' '));
}
for (const m of src.matchAll(/>([^<>{}`$]{2,200})</g)) add(m[1]);
const code = /&&|\|\||Math\.|\.[a-zA-Z]+\(|\b[a-zA-Z0-9]{1,4}\.[a-z]|\?\s|\+\s*$|^\s*[+,)]|\(\s*$|\bdt\b|===|!==|\bconst\b|\breturn\b/;
const list = [...out].filter(s => /[a-zà-ÿ]/i.test(s) && !/^[\d\s.,:/·$+−-]+$/.test(s) && !code.test(s)).sort();
fs.mkdirSync(path.join(root, 'i18n'), { recursive: true });
fs.writeFileSync(path.join(root, 'i18n', 'strings-fr.json'), JSON.stringify(list, null, 1));
console.log(list.length + ' textes');
