#!/usr/bin/env node
// Planches contact rapides : une image au milieu de chaque plan, avec le cadre de la zone sûre TikTok.
//   node tools/studio/tiktok/preview.js [numéros...] [--res 360]
// Sortie : marketing/tiktok/apercus/NN-slug.png (à lancer après stage-web.js)
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..', '..', '..'), web = process.env.NB_WEB ? path.resolve(process.env.NB_WEB) : path.join(ROOT, 'marketing', 'tiktok', '.web'), out = path.join(ROOT, 'marketing', 'tiktok', 'apercus');
const ri = process.argv.indexOf('--res'), res = ri > 0 ? +process.argv[ri + 1] : 360;
const nums = process.argv.slice(2).filter((a, i, l) => /^\d+$/.test(a) && l[i - 1] !== '--res').map(Number);
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => console.error('page:', e.message));
  await p.goto('file://' + path.join(web, 'studio.html')); await p.waitForFunction(() => window.STUDIO, null, { timeout: 180000 });
  const dir = path.join(__dirname, 'projets');
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort()) {
    const proj = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); if (nums.length && !nums.includes(proj.tiktok.n)) continue;
    await p.evaluate(async pr => window.STUDIO.load(pr), proj);
    const W = res, H = Math.round(res * 16 / 9 / 2) * 2, times = proj.tiktok.plan.map(x => +(x.t + x.d / 2).toFixed(2)); times.unshift(.5);
    const tmp = fs.mkdtempSync(path.join(out, '.f-'));
    for (const [i, t] of times.entries()) {
      const b64 = await p.evaluate(([t, w, h]) => { window.STUDIO.frame(t, w, h); const c = document.getElementById('cv'), o = document.createElement('canvas'); o.width = w; o.height = h; const x = o.getContext('2d'); x.drawImage(c, 0, 0);
        x.strokeStyle = 'rgba(0,255,0,.7)'; x.lineWidth = 2; x.strokeRect(0, h * .15, w * .88, h * .6); x.fillStyle = '#0f0'; x.font = '14px sans-serif'; x.fillText(t.toFixed(1) + ' s', 6, 16); return o.toDataURL('image/png').split(',')[1]; }, [t, W, H]);
      fs.writeFileSync(path.join(tmp, String(i).padStart(2, '0') + '.png'), Buffer.from(b64, 'base64'));
    }
    const dest = path.join(out, f.replace('.json', '.png')), cols = 6;
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', '1', '-i', path.join(tmp, '%02d.png'), '-vf', `scale=${W}:-2,tile=${cols}x${Math.ceil(times.length / cols)}:padding=4`, '-frames:v', '1', dest]);
    fs.rmSync(tmp, { recursive: true, force: true }); console.log(dest);
  }
  await b.close();
})();
