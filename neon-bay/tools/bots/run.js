// Lance les testeurs automatiques en parallèle et écrit un rapport.
// node tools/bots/run.js [--bots 1,2,3] [--from 1] [--to 30] [--workers 4] [--tries 5]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..', '..');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const PROFILES = require('./profiles.js');
const pick = arg('bots', '') ? arg('bots').split(',').map(Number) : PROFILES.map(p => p.id);
const opts = { from: +arg('from', 1), to: +arg('to', 30), maxTries: +arg('tries', 5), stepCap: +arg('stepcap', 420) };
const workers = +arg('workers', 4);
const outDir = path.join(root, 'reports', 'bots'); fs.mkdirSync(outDir, { recursive: true });

(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const queue = PROFILES.filter(p => pick.includes(p.id)), results = [];
  async function work() {
    while (queue.length) {
      const prof = queue.shift();
      const ctx = await browser.newContext({ viewport: { width: 640, height: 360 } });
      const page = await ctx.newPage(); const errs = [];
      page.on('pageerror', e => errs.push(e.message));
      await page.addInitScript(() => { try { localStorage.clear(); localStorage.setItem('neonbay.save.v2', JSON.stringify({ money: 500, owned: { pistol: true }, weapon: 'pistol', armor: 0, medkits: 2, nitro: 0, perks: {}, done: {}, maxLevel: 30, premium: true, seenOpen: 1, voice: false })); localStorage.setItem('neonbay.audio', JSON.stringify({ sfx: false, music: false })); } catch (e) {} });
      await page.goto('file://' + path.join(root, 'index.html')); await page.waitForTimeout(1500);
      await page.addScriptTag({ path: path.join(__dirname, 'bot.js') });
      await page.evaluate(() => { window.__nb.S.manual = true; });
      await page.exposeFunction('nbLog', s => process.stdout.write(s + '\n'));
      const t0 = Date.now();
      const rep = await page.evaluate(async ({ prof, opts }) => window.NB_BOT.runBot(prof, Object.assign({}, opts, { onLevel: lv => window.nbLog(`[${prof.id} ${prof.name}] niveau ${lv.n} ${lv.ok ? 'OK' : 'ÉCHEC'} ${lv.time}s ${lv.tries.length} essai(s)`) })), { prof, opts });
      rep.errors = errs.slice(0, 10); rep.wall = Math.round((Date.now() - t0) / 1000); rep.profile = prof;
      results.push(rep); fs.writeFileSync(path.join(outDir, `bot-${String(prof.id).padStart(2, '0')}.json`), JSON.stringify(rep, null, 1));
      await ctx.close();
    }
  }
  await Promise.all(Array.from({ length: Math.min(workers, queue.length) }, work));
  await browser.close();
  results.sort((a, b) => a.id - b.id);
  fs.writeFileSync(path.join(outDir, 'latest.json'), JSON.stringify({ date: new Date().toISOString(), opts, results }, null, 1));
  console.log('Rapport : reports/bots/latest.json');
})();
