/* Test de bout en bout dans un vrai navigateur (Playwright).
   Lancer : node tests/smoke.js   (nécessite le paquet « playwright » et un navigateur Chromium installés) */
const http = require("http"), fs = require("fs"), path = require("path"), assert = require("assert");
const { chromium } = require("playwright");
const root = path.resolve(__dirname, "..");
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".webp": "image/webp", ".png": "image/png", ".svg": "image/svg+xml", ".webmanifest": "application/manifest+json" };

const server = http.createServer((req, res) => {
  let f = path.join(root, decodeURIComponent(req.url.split("?")[0]));
  if (f.endsWith(path.sep)) f += "index.html";
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "Content-Type": TYPES[path.extname(f)] || "application/octet-stream" });
  fs.createReadStream(f).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, r));
  const base = "http://localhost:" + server.address().port + "/index.html";
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 320, height: 700 }, locale: "fr-FR" });
  const p = await ctx.newPage();
  const errs = [];
  p.on("pageerror", e => errs.push(e.message));
  /* Les erreurs de chargement réseau sont attendues : réponse 403 simulée du coach IA, polices Google hors connexion. */
  p.on("console", m => { if (m.type() === "error" && !/Failed to load resource/.test(m.text())) errs.push(m.text()); });
  const c = s => p.click(s);
  const txt = s => p.textContent(s);
  const noOverflow = async name => {
    const o = await p.evaluate(() => { const e = document.querySelector("#screen"); return e.scrollWidth - e.clientWidth; });
    if (o > 1) {
      const who = await p.evaluate(() => { const sc = document.querySelector("#screen"), lim = sc.getBoundingClientRect().right; return [...sc.querySelectorAll("*")].filter(e => e.getBoundingClientRect().right > lim + 1).slice(0, 4).map(e => e.tagName + "." + e.className + "#" + e.id); });
      assert.fail("débordement horizontal de " + o + " px sur l'écran " + name + " : " + who.join(", "));
    }
  };
  let n = 0; const ok = m => console.log("ok   " + (++n) + " " + m);

  await p.goto(base);
  assert.strictEqual(await p.evaluate(() => document.documentElement.lang), "fr"); ok("langue du document : fr");
  await noOverflow("welcome");
  await c("[data-act=lang][data-v=pt]"); assert.ok((await txt("#screen h1")).includes("Volte")); ok("portugais affiché");
  assert.strictEqual(await p.evaluate(() => document.documentElement.lang), "pt-BR");
  await c("[data-act=lang][data-v=fr]");
  for (const [go, name] of [["amb", "amb"], ["q1", "q1"], ["q2", "q2"], ["q3", "q3"]]) { await c("[data-act=go][data-v=" + go + "]"); await noOverflow(name); }
  await c(".chip[data-act=zone][data-v=genoux]");
  ok("zone signalée");
  await c("[data-act=finishOnboarding]"); await noOverflow("plan");
  assert.ok((await txt("#planList, .plist")).includes("Remplace")); ok("un exercice remplacé à cause des genoux");
  await c("[data-act=level][data-v=soft]"); assert.ok((await txt(".card.solid p.small")).includes("1 tour")); ok("niveau Doux : 1 tour");
  await c("[data-act=startSession]"); await noOverflow("player");
  const cnt = () => p.evaluate(() => Number(document.querySelector("#count").textContent));
  assert.strictEqual(await cnt(), 30); await c("[data-act=plus]"); assert.strictEqual(await cnt(), 40); ok("+10 s");
  await c("[data-act=pause]"); const a = await cnt(); await p.waitForTimeout(1500); assert.strictEqual(await cnt(), a); ok("pause fige le décompte");
  await c("[data-act=pause]"); await p.waitForTimeout(1300); assert.ok((await cnt()) < a); ok("reprise");
  const h0 = await txt("#screen h2"); await c("[data-act=next]"); const h1 = await txt("#screen h2"); assert.notStrictEqual(h0, h1);
  await c("[data-act=prev]"); assert.strictEqual(await txt("#screen h2"), h0); ok("suivant puis précédent");
  await c("[data-act=redo]"); assert.strictEqual(await cnt(), 30); ok("refaire");
  await p.evaluate(() => { SS.app.ui.sess.left = 1; }); await p.waitForTimeout(1500);
  assert.ok((await txt("#screen h2")).includes("Récupération")); await noOverflow("repos"); ok("écran de récupération");
  await c("[data-act=skipRest]"); assert.notStrictEqual(await txt("#screen h2"), h0); ok("sauter la pause");
  for (let i = 0; i < 6; i++) { if (await p.$("[data-act=fb]")) break; await c("[data-act=next]"); }
  assert.ok((await txt("#screen h2")).includes("Bien joué")); await noOverflow("done"); ok("fin de séance");
  await c("[data-act=fb][data-v=hard]"); assert.strictEqual(await p.evaluate(() => SS.app.state().dur), 20); ok("« trop dur » baisse la durée d'un cran");
  await c("[data-act=go][data-v=path]"); await noOverflow("path");
  assert.ok((await txt(".card .big")).startsWith("1 sur 3")); ok("la semaine compte la séance (objectif : 3 jours)");
  for (const t of ["home", "body", "coach"]) { await c(".tab[data-v=" + t + "]"); await noOverflow(t); }
  await c(".tab[data-v=body]");
  await p.setViewportSize({ width: 320, height: 380 });
  await p.evaluate(() => { document.querySelector("#screen").scrollTop = 80; });
  const before = await p.evaluate(() => document.querySelector("#screen").scrollTop);
  await p.evaluate(() => document.querySelector(".chip[data-act=zone][data-v=cou]").click());
  const after = await p.evaluate(() => document.querySelector("#screen").scrollTop);
  assert.ok(before > 40 && after === before, "le défilement doit être conservé : " + before + " puis " + after); ok("le défilement est conservé quand on touche une zone");
  await p.evaluate(() => document.querySelector(".chip[data-act=zone][data-v=cou]").click());
  await p.setViewportSize({ width: 320, height: 700 });
  await c("[data-act=go][data-v=lib]"); await noOverflow("lib");
  assert.ok(await p.$(".libitem.off")); ok("bibliothèque : des exercices écartés");
  await c("[data-act=go][data-v=body]"); await c("[data-act=go][data-v=anat]"); await c("[data-act=azone][data-v=genoux]"); await noOverflow("anat");
  await c("[data-act=go][data-v=body]"); await c(".tab[data-v=coach]");
  await p.fill("#aiInput", "<img src=x onerror=alert(1)>"); await p.press("#aiInput", "Enter");
  assert.strictEqual(await p.$$eval("#chat img", e => e.length), 0); ok("pas d'injection de HTML dans le chat");
  await c("[data-act=coachtab][data-v=pro]"); await noOverflow("coach privé");
  await c(".tab[data-v=path]"); await c("[data-act=go][data-v=paywall]"); await noOverflow("paywall");
  await c("[data-act=go][data-v=home]"); await c("[data-act=go][data-v=settings]"); await c("[data-act=tz][data-v=\"1.3\"]"); await noOverflow("settings, texte très grand");
  // ----- objectifs, alimentation, vrai coach IA (service Google simulé) -----
  await c("[data-act=go][data-v=home]");
  await c(".tab[data-v=path]"); await c("[data-act=go][data-v=goals]"); await noOverflow("objectifs");
  await c("[data-act=goal][data-v=weight]"); await c("[data-act=goal][data-v=muscle]");
  await c("[data-act=goal][data-v=balance]");
  assert.ok(await p.evaluate(() => SS.app.state().goals.length) <= 3); ok("trois objectifs au maximum");
  await c("[data-act=target][data-v=\"5\"]"); assert.strictEqual(await p.evaluate(() => SS.app.state().weekTarget), 5); ok("objectif de la semaine réglable");
  await p.fill("#weightInput", "abc"); await p.press("#weightInput", "Enter"); assert.ok((await p.textContent(".toast")).includes("25"));
  await p.fill("#weightInput", "82,4"); await p.press("#weightInput", "Enter"); await p.fill("#weightInput", "81"); await p.press("#weightInput", "Enter");
  assert.ok((await txt("#screen")).includes("Écart depuis le début")); ok("suivi du poids");
  await c(".tab[data-v=food]"); await noOverflow("repas");
  await c("[data-act=food][data-v=water]"); await c("[data-act=food][data-v=protein]");
  assert.ok((await txt("#screen")).includes("2 sur 5")); ok("repères alimentaires du jour");

  await c(".tab[data-v=coach]"); await c("[data-act=coachtab][data-v=ai]");
  assert.ok(!(await p.content()).match(/aistudio|AI Studio|Gemini|clé d'API/i)); ok("aucune proposition de clé d'API dans l'application");
  await p.fill("#aiInput", "J'ai une douleur forte dans la poitrine"); await p.press("#aiInput", "Enter");
  await p.waitForTimeout(300); assert.ok((await txt("#chat")).includes("avis médical")); ok("symptôme grave : renvoi vers un médecin");
  await p.fill("#aiInput", "Que manger après la séance ?"); await p.press("#aiInput", "Enter");
  await p.waitForFunction(() => document.querySelector("#chat").textContent.includes("onglet Repas")); ok("le coach répond sur l'alimentation");
  await c(".tab[data-v=home]"); await c("[data-act=go][data-v=settings]"); await noOverflow("réglages");
  await c("[data-act=go][data-v=home]");
  const keep = await p.evaluate(() => JSON.stringify(SS.app.state().zones)); assert.ok(keep.includes("genoux"));
  await p.reload(); assert.ok(await p.evaluate(() => SS.app.state().onboarded)); ok("les données survivent au rechargement");
  await p.evaluate(() => navigator.serviceWorker.ready); await p.waitForTimeout(500);
  await ctx.setOffline(true); await p.reload(); assert.ok((await p.title()).includes("Second")); ok("fonctionne hors connexion");
  assert.deepStrictEqual(errs, [], "erreurs de console : " + errs.join(" | ")); ok("aucune erreur de console");
  await b.close(); server.close(); console.log("\nTous les tests de bout en bout passent");
})().catch(e => { console.log("ÉCHEC : " + e.message); process.exit(1); });
