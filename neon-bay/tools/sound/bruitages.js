#!/usr/bin/env node
// Générateur de bruitages originaux (synthèse du moteur audio du jeu, sans fichier externe ni droits à payer).
// node tools/sound/bruitages.js [whoosh impact riser siren engine rumble rain pop sting | tout] [--out marketing/sons] [--variantes 3]
// Écrit des WAV (44,1 kHz stéréo) : <out>/<type>.wav (et <type>-2.wav, -3.wav… avec --variantes).
// Les vidéos (tools/studio/render.js --sons <out>) utilisent ces fichiers à la place de la synthèse directe.
const { chromium } = require('playwright'), fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..', '..');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const ALL = { whoosh: ['sfxWhoosh', [.45, 0, .9], 1], impact: ['sfxImpact', [1], 1.6], riser: ['sfxRiser', [1.4, .9], 1.6], siren: ['sfxSiren', [6, 0, .6], 6], engine: ['sfxEngine', [3, .8], 3.2], rumble: ['sfxRumble', [4, 1], 4.2], rain: ['sfxRain', [10, .5], 10], pop: ['sfxPop', [.8], .4], sting: ['sfxSting', [.9], 1.8] };
let kinds = process.argv.slice(2).filter(a => !a.startsWith('--') && !/^\d+$/.test(a) && a !== arg('out')); if (!kinds.length || kinds.includes('tout')) kinds = Object.keys(ALL);
const out = arg('out', path.join(root, 'marketing', 'sons')), nv = Math.max(1, +arg('variantes', 1));
(async () => {
  const web = fs.existsSync(path.join(root, 'dist-web', 'index.html')) ? path.join(root, 'dist-web') : root;
  const b = await chromium.launch(), g = await b.newPage(); await g.goto('file://' + path.join(web, 'index.html')); await g.waitForFunction(() => window.NB_AUDIO, null, { timeout: 60000 });
  fs.mkdirSync(out, { recursive: true });
  for (const k of kinds) { const d = ALL[k]; if (!d) { console.error('Type inconnu : ' + k); continue; }
    for (let v = 1; v <= nv; v++) {
      // riser : son « en amont » de l'instant t, on le décale donc de sa durée
      const t0 = k === 'riser' ? d[1][0] : .05, ev = [{ t: t0, fn: d[0], args: d[1] }];
      const b64 = await g.evaluate(async ([secs, ev]) => { const buf = await window.NB_AUDIO.renderOffline('none', secs, ev); let s = ''; const u = new Uint8Array(buf); for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode.apply(null, u.subarray(i, i + 32768)); return btoa(s); }, [d[2] + .2, ev]);
      const file = path.join(out, k + (v > 1 ? '-' + v : '') + '.wav'); fs.writeFileSync(file, Buffer.from(b64, 'base64')); console.log('écrit : ' + path.relative(root, file));
    }
  }
  await b.close();
})();
