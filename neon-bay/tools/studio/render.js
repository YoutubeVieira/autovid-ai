// Rendu cloud d'un projet Néon Studio en MP4 H.264 (image par image, sans perte de cadence).
// node tools/studio/render.js projet.json [--out film.mp4] [--res 1080] [--fps 30]
// node tools/studio/render.js --template chase   (scènes prêtes : trailer, chase, arrival, duel, launch)
// --blur 3 : flou de mouvement cinéma (temps de rendu multiplié d'autant)
// --music usa|ita|col|bra|moon|mars|lofi  ajoute la musique du jeu (synthétisée hors ligne), --hot 7-14,21-36 = passages intenses
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..', '..');
// NB_WEB=dossier : rend depuis une copie du site (par défaut dist-web) ; utile quand dist-web est en cours de reconstruction
const web = process.env.NB_WEB ? path.resolve(process.env.NB_WEB) : path.join(root, 'dist-web');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const file = process.argv[2] && !process.argv[2].startsWith('--') ? process.argv[2] : null;
const tpl = arg('template', file ? null : 'chase');
const fps = +arg('fps', 30), res = +arg('res', 1080);
const BLUR = Math.max(1, Math.min(8, +arg('blur', 1))); // --blur 3 : flou de mouvement (3 sous-images par image)
(async () => {
  const studio = path.join(web, 'studio.html');
  if (!fs.existsSync(studio)) { console.error('Lance d’abord : node tools/build-web.js'); process.exit(1); }
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => console.error('page:', e.message));
  await p.goto('file://' + studio); await p.waitForFunction(() => window.STUDIO, null, { timeout: 30000 });
  const proj = file ? JSON.parse(fs.readFileSync(file, 'utf8')) : await p.evaluate(k => window.STUDIO.template(k), tpl);
  const dur = await p.evaluate(async pr => window.STUDIO.load(pr), proj);
  const asp = proj.aspect || '16:9', W = asp === '9:16' ? res : asp === '2.39' ? Math.round(res * 2.39 / 2) * 2 : Math.round(res * 16 / 9 / 2) * 2, H = asp === '9:16' ? Math.round(res * 16 / 9 / 2) * 2 : res;
  const out = arg('out', path.join(root, 'marketing', 'studio', (proj.name || tpl || 'film').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^\w\- ]+/g, '').trim().replace(/\s+/g, '-').toLowerCase() + '.mp4'));
  fs.mkdirSync(path.dirname(out), { recursive: true });
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.round(dur * fps), t0 = Date.now();
  for (let f = 0; f <= N; f++) {
    // flou de mouvement façon caméra de cinéma (obturateur à 180°) : moyenne de BLUR instants dans la demi-image
    const b64 = await p.evaluate(([t, w, h, n, dtf]) => {
      if (n <= 1) { window.STUDIO.frame(t, w, h); return document.getElementById('cv').toDataURL('image/jpeg', .93).split(',')[1]; }
      const acc = window.__acc || (window.__acc = document.createElement('canvas')); acc.width = w; acc.height = h; const g = acc.getContext('2d');
      for (let k = 0; k < n; k++) { window.STUDIO.frame(t + (k / (n - 1) - .5) * dtf * .5, w, h); g.globalAlpha = 1 / (k + 1); g.drawImage(document.getElementById('cv'), 0, 0, w, h); }
      g.globalAlpha = 1; return acc.toDataURL('image/jpeg', .93).split(',')[1];
    }, [f / fps, W, H, BLUR, 1 / fps]);
    if (!ff.stdin.write(Buffer.from(b64, 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (f % fps === 0) process.stdout.write(`\r${Math.round(f / N * 100)} % (${f}/${N} images, ${W}×${H})   `);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  const music = arg('music', null);
  if (music) {
    const g = await b.newPage(); await g.goto('file://' + path.join(web, 'index.html')); await g.waitForFunction(() => window.NB_AUDIO, null, { timeout: 30000 });
    const hot = (arg('hot', '') || '').split(',').filter(Boolean).map(x => { const [a, z] = x.split('-').map(Number); return { hot: true, t: a, d: z - a }; });
    const b64 = await g.evaluate(async ([st, secs, ev]) => { const buf = await window.NB_AUDIO.renderOffline(st, secs, ev); let s = ''; const u = new Uint8Array(buf); for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode.apply(null, u.subarray(i, i + 32768)); return btoa(s); }, [music, Math.ceil(dur) + 1, hot]);
    const wav = out.replace(/\.mp4$/, '.wav'), tmp = out.replace(/\.mp4$/, '.tmp.mp4'); fs.writeFileSync(wav, Buffer.from(b64, 'base64')); fs.renameSync(out, tmp);
    const code = await new Promise(r => spawn('ffmpeg', ['-y', '-loglevel', 'error', '-i', tmp, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-af', `afade=t=in:st=0:duration=0.6,afade=t=out:st=${Math.max(0, dur - 2).toFixed(2)}:duration=2,loudnorm=I=-14:TP=-1`, '-shortest', '-movflags', '+faststart', out], { stdio: 'inherit' }).on('close', r));
    if (code === 0) { fs.unlinkSync(tmp); fs.unlinkSync(wav); } else { fs.renameSync(tmp, out); console.error('Musique non ajoutée (vidéo muette gardée), son : ' + wav); }
  }
  await b.close();
  console.log(`\nVidéo : ${out} · ${Math.round((Date.now() - t0) / 1000)} s de calcul`);
})();
