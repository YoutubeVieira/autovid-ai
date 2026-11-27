// Transforme reports/bots/latest.json en rapport lisible : reports/bots/RAPPORT.md
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, '..', '..', 'reports', 'bots');
const { date, opts, results } = JSON.parse(fs.readFileSync(path.join(dir, 'latest.json'), 'utf8'));
const DIFF = ['Facile', 'Normal', 'Difficile', 'Légende'];
const med = a => { if (!a.length) return 0; const s = a.slice().sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
const min = s => Math.round(s / 60);
const count = arr => { const m = {}; for (const k of arr) m[k] = (m[k] || 0) + 1; return Object.entries(m).sort((a, b) => b[1] - a[1]); };
let md = `# Rapport des 20 testeurs automatiques\n\nDate : ${date.slice(0, 16).replace('T', ' ')} UTC · niveaux ${opts.from} à ${opts.to} · ${opts.maxTries} essais maximum par niveau.\n\n`;
md += `> Les testeurs jouent avec les mêmes règles qu'un joueur (vitesse de marche et de conduite, tir, police, chronos), sans téléportation, en simulation accélérée. Ils conduisent et visent moins bien qu'un bon joueur humain : leurs temps sont des **ordres de grandeur**, et leurs échecs montrent **où** le jeu est dur, pas exactement **combien**.\n\n`;
md += `## Résultats par testeur\n\n| # | Testeur | Fonction | Difficulté | Niveaux réussis | Temps de jeu | Essais | Cause d'échec n° 1 |\n|---|---|---|---|---|---|---|---|\n`;
for (const r of results) {
  const ok = r.levels.filter(l => l.ok).length, fails = r.levels.flatMap(l => l.tries.filter(t => !t.ok).map(t => `${t.reason} (${t.step || '?'})`));
  const top = count(fails)[0];
  md += `| ${r.id} | ${r.name} | ${r.role} | ${DIFF[r.profile.diff]} | ${ok}/${r.levels.length} | ${min(r.totalGame)} min | ${r.attempts} | ${top ? top[0] + ' ×' + top[1] : '—'} |\n`;
}
md += `\n## Difficulté par niveau\n\n| Niveau | Réussite (testeurs) | Temps médian d'une réussite | Étape la plus bloquante |\n|---|---|---|---|\n`;
const N = opts.to - opts.from + 1;
for (let n = opts.from; n <= opts.to; n++) {
  const lv = results.map(r => r.levels.find(l => l.n === n)).filter(Boolean);
  const okT = lv.filter(l => l.ok).map(l => l.tries[l.tries.length - 1].time);
  const steps = count(lv.flatMap(l => l.tries.filter(t => !t.ok).map(t => t.step || '?')))[0];
  md += `| ${n} | ${lv.filter(l => l.ok).length}/${lv.length} | ${okT.length ? Math.round(med(okT) / 60 * 10) / 10 + ' min' : '—'} | ${steps ? steps[0] + ' (' + steps[1] + ' échecs)' : '—'} |\n`;
}
const allFails = results.flatMap(r => r.levels.flatMap(l => l.tries.filter(t => !t.ok)));
md += `\n## Pourquoi on perd\n\n| Cause | Nombre |\n|---|---|\n` + count(allFails.map(t => t.reason)).slice(0, 10).map(([k, v]) => `| ${k} | ${v} |`).join('\n') + '\n';
md += `\n## Étapes qui font perdre\n\n| Type d'étape | Échecs |\n|---|---|\n` + count(allFails.map(t => t.step || '?')).slice(0, 12).map(([k, v]) => `| ${k} | ${v} |`).join('\n') + '\n';
const timing = results.flatMap(r => r.timing || []);
if (timing.length) {
  md += `\n## Chronos : vitesse moyenne exigée sur la route\n\nVoiture du joueur : 520 au maximum. Au-delà d'environ 280 de moyenne, un joueur sur téléphone a du mal.\n\n| Type d'étape | Mesures | Vitesse exigée (médiane) | Pire cas |\n|---|---|---|---|\n`;
  const by = {}; for (const t of timing) (by[t.type] = by[t.type] || []).push(t.need);
  for (const [k, a] of Object.entries(by)) md += `| ${k} | ${a.length} | ${med(a)} | ${Math.max(...a)} |\n`;
}
const errs = results.filter(r => r.gameErrors || (r.errors && r.errors.length) || r.botErrors);
md += `\n## Erreurs techniques\n\n` + (errs.length ? errs.map(r => `- ${r.name} : ${r.gameErrors || 0} erreur(s) du jeu ${r.gameError1 ? '`' + r.gameError1.split('\n')[0] + '`' : ''} ${(r.errors || []).join(' ; ')} ${r.botErrors ? '· ' + r.botErrors + ' erreur(s) du testeur' : ''}`).join('\n') : 'Aucune erreur du jeu pendant les parties.') + '\n';
// stratégies : comparaisons de profils
const S = id => results.find(r => r.id === id), okc = r => r ? r.levels.filter(l => l.ok).length : 0;
const cmp = (a, b, label) => S(a) && S(b) ? `- ${label} : ${S(a).name} ${okc(S(a))} niveaux contre ${S(b).name} ${okc(S(b))}.\n` : '';
md += `\n## Ce que les testeurs nous apprennent (stratégies)\n\n` + cmp(8, 9, 'Acheter de l’équipement') + cmp(10, 2, 'S’entraîner à la salle') + cmp(11, 2, 'Semer la police par les tunnels') + cmp(4, 2, 'Rouler vite en voiture') + cmp(7, 2, 'Rester à pied') + cmp(12, 2, 'Se passer des trousses de soins') + cmp(13, 2, 'Jouer sans armure') + cmp(19, 2, 'Le point de reprise à l’étape 6') + cmp(17, 16, 'Armes gratuites par défis contre achat') + cmp(14, 3, 'Viser mal contre viser bien') + cmp(1, 2, 'Facile contre Normal') + cmp(5, 6, 'Légende contre Difficile');
fs.writeFileSync(path.join(dir, 'RAPPORT.md'), md);
console.log(md);
