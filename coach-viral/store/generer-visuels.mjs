/* Fabrique les visuels de la fiche Play Store à partir de vraies captures de l'application (exemples d'avance) :
     node store/generer-visuels.mjs
   Sortie dans store/visuels/ : icone-512.png, banniere-1024x500.png, capture-1.png … capture-6.png (1080x1920). */
import path from "node:path";
import { mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { fauxClient } from "./donnees-demo.mjs";

process.env.IMAGES = "aucun";
process.env.TRANSCRIPTION = "0";
const { createServer } = await import("../server.mjs");
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const here = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(here, "visuels");
const RAW = await mkdtemp(path.join(tmpdir(), "store-brut-"));
await mkdir(OUT, { recursive: true });
/* Polices intégrées en base64 : une page créée par setContent ne peut pas lire de fichier local. */
const fontData = async (f) => "data:font/otf;base64," + (await readFile(path.join(here, "..", "assets", "fonts", f))).toString("base64");
const FONT = await fontData("Inter-Bold.otf");
const FONT2 = await fontData("Inter-SemiBold.otf");

const dataDir = await mkdtemp(path.join(tmpdir(), "store-data-"));
const srv = createServer({ client: fauxClient, dataDir, env: { VOIX_MOTEURS: "kokoro,chatterbox,edge" } }).listen(0);
await new Promise((r) => srv.once("listening", r));
const base = `http://127.0.0.1:${srv.address().port}/`;
const browser = await chromium.launch();

/* ---------- 1. Captures brutes de l'application (360x640, x3 = 1080x1920) ---------- */
const app = await browser.newPage({ viewport: { width: 360, height: 640 }, deviceScaleFactor: 3, colorScheme: "dark" });
await app.goto(base);
await app.addStyleTag({ content: ".toast{display:none!important}" });
const brut = async (nom, selector, offset = 0) => {
  if (selector) await app.evaluate(([s, o]) => { const el = document.querySelector(s); window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 60 - o); }, [selector, offset]);
  await app.waitForTimeout(250);
  await app.screenshot({ path: path.join(RAW, nom + ".png") });
};

/* Idées */
await app.fill("#niche", "capoeira pour débutants");
await app.click("#f-idees button[type=submit]");
await app.waitForSelector(".idea");
await brut("idees", ".idea");

/* Radar */
await app.fill(".rd-nom", "capoeira débutants");
await app.click("#rd-go");
await app.waitForSelector(".theme", { timeout: 30_000 });
await brut("radar", "#rd-res h3");

/* Score */
await app.click(".tabs [data-vue=score]");
await app.fill("#desc-s", "3 erreurs de débutant en ginga");
await app.click("#f-score button[type=submit]");
await app.waitForSelector(".ring");
await brut("score", "#r-score");

/* Studio : analyse d'un lien -> nouvelle version */
await app.click(".tabs [data-vue=studio]");
await app.check('input[name=mode][value=fichier]');
await app.setInputFiles("#src-file", path.join(here, "..", "tests", "fixtures", "court.webm"));
await app.click("#f-studio button[type=submit]");
await app.waitForSelector("#sc-h-0", { timeout: 60_000 });
await brut("studio", "#r-studio section");

/* Voix */
await app.click(".tabs [data-vue=voix]");
await app.waitForSelector("#vx-go");
await brut("voix", "h1", 40);

/* Publier */
await app.click(".tabs [data-vue=publier]");
await app.fill("#contenu", "3 erreurs de débutant en ginga");
await app.click("#f-pub button[type=submit]");
await app.waitForSelector("#r-pub section.card");
await brut("publier", "#r-pub");

/* ---------- 2. Mise en page des captures (1080x1920) ---------- */
const CAPTURES = [
  ["idees", "Des idées de vidéos", "avec l'accroche et le script seconde par seconde"],
  ["studio", "Collez une vidéo qui marche", "le coach écrit une version originale et meilleure"],
  ["score", "Votre score avant de publier", "et les 3 choses à corriger d'abord"],
  ["radar", "Les tendances de votre niche", "un radar qui cherche pour vous chaque jour"],
  ["voix", "Voix off réaliste", "ou votre propre voix, clonée"],
  ["publier", "Prête pour chaque réseau", "TikTok, Reels et Shorts : la bonne légende"]
];
const css = `
@font-face { font-family: T; src: url("${FONT}"); }
@font-face { font-family: S; src: url("${FONT2}"); }
* { box-sizing: border-box; margin: 0; }
body { width: 1080px; height: 1920px; overflow: hidden; font-family: T, sans-serif; color: #fff;
  background: radial-gradient(120% 80% at 20% 0%, #6A3DF0 0%, #2A1A5E 45%, #100E18 100%); }
.glow { position: absolute; width: 900px; height: 900px; border-radius: 50%; right: -350px; bottom: -250px;
  background: radial-gradient(circle, rgba(255,77,126,.55), rgba(255,77,126,0) 65%); }
h1 { position: absolute; top: 120px; left: 80px; right: 80px; font-size: 92px; line-height: 1.05; letter-spacing: -2px; }
p { position: absolute; top: 340px; left: 80px; right: 80px; font-family: S, sans-serif; font-size: 44px; line-height: 1.25; color: rgba(255,255,255,.82); }
.phone { position: absolute; left: 50%; top: 520px; transform: translateX(-50%); width: 760px; height: 1351px;
  border-radius: 72px; background: #05040a; padding: 22px; box-shadow: 0 40px 120px rgba(0,0,0,.55), 0 0 0 3px rgba(255,255,255,.12); }
.phone img { width: 100%; height: 100%; border-radius: 52px; object-fit: cover; object-position: top; display: block; }
.badge { position: absolute; top: 60px; left: 80px; font-family: S; font-size: 30px; letter-spacing: 3px; text-transform: uppercase; color: #FF8FB0; }`;
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
for (let i = 0; i < CAPTURES.length; i++) {
  const [nom, titre, sous] = CAPTURES[i];
  const img = "data:image/png;base64," + (await readFile(path.join(RAW, nom + ".png"))).toString("base64");
  await page.setContent(`<html><head><style>${css}</style></head><body><div class="glow"></div>
    <div class="badge">Coach Viral</div><h1>${titre}</h1><p>${sous}</p>
    <div class="phone"><img src="${img}"></div></body></html>`);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(OUT, `capture-${i + 1}.png`) });
}

/* ---------- 3. Bannière 1024x500 (sans transparence) ---------- */
const banner = await browser.newPage({ viewport: { width: 1024, height: 500 }, deviceScaleFactor: 1 });
const img1 = "data:image/png;base64," + (await readFile(path.join(RAW, "studio.png"))).toString("base64");
const img2 = "data:image/png;base64," + (await readFile(path.join(RAW, "score.png"))).toString("base64");
await banner.setContent(`<html><head><style>
@font-face { font-family: T; src: url("${FONT}"); } @font-face { font-family: S; src: url("${FONT2}"); }
* { margin: 0; box-sizing: border-box; }
body { width: 1024px; height: 500px; overflow: hidden; font-family: T; color: #fff;
  background: linear-gradient(120deg, #2A1A5E 0%, #6A3DF0 55%, #FF4D7E 130%); }
.t { position: absolute; left: 56px; top: 110px; width: 450px; }
.logo { display: flex; align-items: center; gap: 18px; font-size: 50px; letter-spacing: -1px; }
.logo i { width: 74px; height: 74px; border-radius: 18px; background: #fff; display: grid; place-items: center; }
.logo i::before { content: ""; border-left: 22px solid transparent; border-right: 22px solid transparent; border-bottom: 38px solid #6A3DF0; }
h2 { font-family: S; font-size: 30px; line-height: 1.28; margin-top: 26px; color: rgba(255,255,255,.92); }
.ph { position: absolute; width: 230px; height: 409px; border-radius: 30px; background: #05040a; padding: 9px; box-shadow: 0 20px 60px rgba(0,0,0,.5); }
.ph img { width: 100%; height: 100%; border-radius: 22px; object-fit: cover; object-position: top; }
.a { right: 250px; top: 60px; transform: rotate(-6deg); } .b { right: 40px; top: 30px; transform: rotate(5deg); }
</style></head><body><div class="t"><div class="logo"><i></i>Coach Viral</div>
<h2>Idées, scripts, voix off et vidéos courtes. Votre coach IA pour TikTok, Reels et Shorts.</h2></div>
<div class="ph a"><img src="${img2}"></div><div class="ph b"><img src="${img1}"></div></body></html>`);
await banner.evaluate(() => document.fonts.ready);
await banner.screenshot({ path: path.join(OUT, "banniere-1024x500.png"), omitBackground: false });

/* ---------- 4. Icône 512x512 (pleine, Google arrondit lui-même) ---------- */
const icon = await browser.newPage({ viewport: { width: 512, height: 512 }, deviceScaleFactor: 1 });
await icon.setContent(`<html><body style="margin:0"><svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6A3DF0"/><stop offset="1" stop-color="#FF4D7E"/></linearGradient></defs>
<rect width="512" height="512" fill="url(#g)"/><path d="M256 120 384 360H128Z" fill="#fff"/><path d="M256 236 308 334H204Z" fill="#FF4D7E"/></svg></body></html>`);
await icon.screenshot({ path: path.join(OUT, "icone-512.png"), omitBackground: true });

await browser.close();
srv.close();
console.log("Visuels créés dans " + OUT);
