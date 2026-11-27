#!/usr/bin/env node
// « Oreille » du studio : écoute des fichiers son (via ffmpeg) et classe ceux qui conviennent le mieux à un usage.
// node tools/sound/ecoute.js <fichiers ou dossier...> --pour whoosh|impact|siren|engine|riser|rain|rumble|pop|sting [--garder marketing/sons/whoosh.wav]
// Mesures : durée utile (sans silences), volume (LUFS), crête, attaque (temps pour atteindre le maximum),
// brillance (centroïde spectral moyen), régularité (variation du volume). Puis un score selon le profil attendu.
// --garder : copie le meilleur son, coupé de ses silences et normalisé à -14 LUFS, à l'emplacement donné (WAV 44,1 kHz stéréo).
const fs = require('fs'), path = require('path'), { spawnSync } = require('child_process');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const want = arg('pour', 'whoosh'), keep = arg('garder', null);
const inputs = []; for (let i = 2; i < process.argv.length; i++) { const a = process.argv[i]; if (a.startsWith('--')) { i++; continue; } if (fs.existsSync(a) && fs.statSync(a).isDirectory()) for (const f of fs.readdirSync(a)) { if (/\.(wav|mp3|ogg|flac|m4a|aac|opus)$/i.test(f)) inputs.push(path.join(a, f)); } else inputs.push(a); }
if (!inputs.length) { console.error('Usage : node tools/sound/ecoute.js <fichiers|dossier> --pour whoosh [--garder sortie.wav]'); process.exit(1); }
// profils attendus : durée (s), attaque (s), brillance (Hz), régularité (écart-type du volume en dB : bas = son continu)
const P = {
  whoosh: { dur: [.25, 1.5], atk: [.08, .8], cen: [1500, 6000], var: [3, 20] },
  impact: { dur: [.3, 2.5], atk: [0, .04], cen: [80, 4500], var: [4, 30] },
  siren: { dur: [2, 30], atk: [0, 30], cen: [500, 2500], var: [0, 10] },
  engine: { dur: [1, 30], atk: [0, 30], cen: [80, 2600], var: [0, 10] },
  riser: { dur: [.6, 4], atk: [.5, 4], cen: [800, 8000], var: [3, 25] },
  rain: { dur: [3, 120], atk: [0, 120], cen: [2500, 14000], var: [0, 10] },
  rumble: { dur: [1, 30], atk: [0, 30], cen: [20, 1200], var: [0, 12] },
  pop: { dur: [.03, .5], atk: [0, .03], cen: [600, 4000], var: [2, 30] },
  sting: { dur: [.6, 4], atk: [0, .2], cen: [400, 4000], var: [2, 25] },
}[want];
if (!P) { console.error('Usage inconnu : ' + want); process.exit(1); }
const ff = a => { const r = spawnSync('ffmpeg', ['-hide_banner', '-nostats', ...a], { encoding: 'utf8', maxBuffer: 64e6 }); return (r.stdout || '') + '\n' + (r.stderr || ''); }; // les mesures « ametadata » sortent sur stdout, le bilan ebur128 sur stderr
function analyse(f) {
  const dur = +((spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], { encoding: 'utf8' }).stdout || '0').trim()) || 0;
  const r = ff(['-i', f, '-af', 'silenceremove=start_periods=1:start_threshold=-50dB:stop_periods=-1:stop_threshold=-50dB:stop_duration=0.3,ebur128=peak=true,astats=metadata=1:reset=1,aspectralstats=measure=centroid,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-', '-f', 'null', '-']);
  const lr = ff(['-i', f, '-af', 'ebur128=peak=true', '-f', 'null', '-']), lufs = +(([...lr.matchAll(/I:\s+(-?[\d.]+) LUFS/g)].pop() || [])[1]) || -70 /* le bilan final est la dernière ligne « I: » */, peak = +(lr.match(/Peak:\s+(-?[\d.]+) dBFS/) || [])[1] || -70;
  const rms = [...r.matchAll(/RMS_level=(-?[\d.inf]+)/g)].map(m => +m[1]).filter(v => isFinite(v));
  // brillance pondérée par le volume : les passages presque silencieux (souffle aigu) ne faussent plus la mesure
  const cr = ff(['-i', f, '-af', 'aformat=channel_layouts=mono,asetnsamples=2048,astats=metadata=1:reset=1,aspectralstats=win_size=2048:measure=centroid,ametadata=print:file=-', '-f', 'null', '-']);
  let sw = 0, sc = 0; for (const blk of cr.split(/frame:\d+/)) { const c = +(blk.match(/centroid=([\d.]+)/) || [])[1], l = +(blk.match(/RMS_level=(-?[\d.]+)/) || [])[1]; if (c > 0 && isFinite(l) && l > -60) { const w = Math.pow(10, l / 20); sw += w; sc += w * c; } }
  const centroid = sw ? sc / sw : 0;
  const useful = rms.length ? rms.length * 1024 / 44100 : dur; // astats par bloc ≈ 1024 échantillons
  const mx = rms.length ? Math.max(...rms) : -70, iMax = rms.indexOf(mx), atk = iMax * 1024 / 44100;
  const mean = rms.length ? rms.reduce((a, b) => a + b, 0) / rms.length : 0, variance = rms.length ? Math.sqrt(rms.reduce((a, b) => a + (b - mean) ** 2, 0) / rms.length) : 0;
  return { f, dur: +Math.min(dur, useful || dur).toFixed(2), lufs, peak, atk: +atk.toFixed(3), centroid: Math.round(centroid), var: +variance.toFixed(1) };
}
// écart mesuré en rapport (échelle logarithmique) : 2 fois trop long = même pénalité pour un son court ou long
const fitL = (v, [a, b]) => { v = Math.max(v, 1e-3); a = Math.max(a, 1e-3); return v >= a && v <= b ? 1 : Math.max(0, 1 - Math.abs(Math.log(v < a ? a / v : v / b)) / Math.log(3)); };
const fit = (v, [a, b]) => v >= a && v <= b ? 1 : Math.max(0, 1 - Math.min(Math.abs(v - a), Math.abs(v - b)) / Math.max(1e-3, (b - a) || 1));
const res = inputs.map(analyse).map(m => ({ ...m, score: Math.round(100 * (fitL(m.dur, P.dur) * .3 + fit(m.atk, P.atk) * .25 + fitL(m.centroid, P.cen) * .3 + fit(m.var, P.var) * .15) * (m.lufs < -50 ? .3 : 1)) }));
res.sort((a, b) => b.score - a.score);
console.log(`Pour « ${want} » :\n  score  durée  attaque  brillance  régularité   LUFS  fichier`);
for (const m of res) console.log(`  ${String(m.score).padStart(4)}  ${m.dur.toFixed(2).padStart(5)} s ${m.atk.toFixed(2).padStart(6)} s ${String(m.centroid).padStart(7)} Hz ${m.var.toFixed(1).padStart(8)} dB ${m.lufs.toFixed(1).padStart(6)}  ${path.basename(m.f)}`);
if (keep && res.length) {
  fs.mkdirSync(path.dirname(keep), { recursive: true });
  const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', res[0].f, '-af', 'silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse,loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '44100', '-ac', '2', keep]);
  console.log(r.status === 0 ? `\nGardé : ${path.basename(res[0].f)} → ${keep}` : '\nÉchec de la copie du meilleur son');
}
