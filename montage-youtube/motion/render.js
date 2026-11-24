#!/usr/bin/env node
/* Rend une animation HTML (fonction window.render(t)) en vidéo MP4 1920x1080, image par image.
   Il faut Node 18+, ffmpeg et Playwright (npm i playwright, puis npx playwright install chromium).

     node render.js wellness-60.html --stills 3,20,60     # quelques images PNG pour vérifier
     node render.js wellness-60.html --out video.mp4      # la vidéo complète, sans son
*/
"use strict";
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const path = require("path"), fs = require("fs");

const args = process.argv.slice(2);
const opt = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d; };
const page0 = path.resolve(args[0] || "wellness-60.html");
const FPS = Number(opt("--fps", 30));

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto("file://" + page0);
  await page.evaluate(() => document.fonts.ready);
  const dur = await page.evaluate(() => window.DURATION);
  const stills = opt("--stills");
  if (stills) {
    const dir = opt("--dir", "stills"); fs.mkdirSync(dir, { recursive: true });
    for (const t of stills.split(",").map(Number)) {
      const b64 = await page.evaluate(t => { render(t); return document.getElementById("c").toDataURL("image/png").split(",")[1]; }, t);
      fs.writeFileSync(path.join(dir, `t${String(t).padStart(5, "0")}.png`), Buffer.from(b64, "base64"));
    }
    await browser.close(); return;
  }
  const out = opt("--out", "motion.mp4"), n = Math.round(dur * FPS);
  const ff = spawn("ffmpeg", ["-y", "-v", "error", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", String(FPS), out], { stdio: ["pipe", "inherit", "inherit"] });
  const t0 = Date.now(), BATCH = 10;
  for (let i = 0; i < n; i += BATCH) {
    const frames = await page.evaluate(([i, BATCH, n, FPS]) => {
      const c = document.getElementById("c"), res = [];
      for (let f = i; f < Math.min(n, i + BATCH); f++) { render(f / FPS); res.push(c.toDataURL("image/jpeg", 0.93).split(",")[1]); }
      return res;
    }, [i, BATCH, n, FPS]);
    for (const f of frames) if (!ff.stdin.write(Buffer.from(f, "base64"))) await new Promise(r => ff.stdin.once("drain", r));
    if (i % (FPS * 10) === 0) process.stdout.write(`  ${Math.round(i / FPS)} s / ${Math.round(dur)} s (${Math.round((Date.now() - t0) / 1000)} s écoulées)\n`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on("close", r));
  await browser.close();
  console.log("Vidéo muette : " + out + " (" + dur + " s)");
})().catch(e => { console.error(e); process.exit(1); });
