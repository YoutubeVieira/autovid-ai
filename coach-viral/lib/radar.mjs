/* Radar de tendances : un bot qui cherche, pour chaque niche, les sujets qui montent en ce moment
   et les transforme en thèmes de vidéos prêts à filmer.
   Sources :
   - recherche web de Claude (environ 0,01 $ par recherche, en plus des jetons) ;
   - YouTube Data API (gratuit jusqu'à 10 000 unités par jour, clé YOUTUBE_API_KEY) : vidéos courtes les plus vues de la semaine ;
   - Reddit (gratuit, sans clé, peut être limité) : sujets les plus votés de la semaine. */
import * as z from "zod/v4";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { ask, MODEL } from "./coach.mjs";

const COUNTRY = { fr: "FR", pt: "BR", en: "US" };

export const RadarSchema = z.object({
  themes: z.array(z.object({
    theme: z.string(),
    pourquoi_maintenant: z.string().describe("Why it is rising now, citing the signal (search, video, post) it comes from"),
    accroches: z.array(z.string()).describe("3 hooks"),
    format: z.string(),
    potentiel: z.number().describe("0-100 estimate"),
    concurrence: z.enum(["faible", "moyenne", "forte"]),
    sources: z.array(z.string()).describe("URLs of the signals used, only real ones from the material")
  }))
});

export const slug = (s) => String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "niche";

/* ---------- Sources gratuites ---------- */

export async function youtubeSignals(niche, lang, key, fetchImpl = fetch, now = new Date()) {
  if (!key) return [];
  const since = new Date(now.getTime() - 7 * 86400_000).toISOString();
  const q = new URLSearchParams({
    part: "snippet", q: niche, type: "video", videoDuration: "short", order: "viewCount",
    publishedAfter: since, relevanceLanguage: lang, regionCode: COUNTRY[lang] || "FR", maxResults: "15", key
  });
  const s = await fetchImpl("https://www.googleapis.com/youtube/v3/search?" + q);
  if (!s.ok) return [];
  const items = (await s.json()).items || [];
  const ids = items.map((i) => i.id?.videoId).filter(Boolean);
  if (!ids.length) return [];
  const v = await fetchImpl("https://www.googleapis.com/youtube/v3/videos?" + new URLSearchParams({ part: "statistics,snippet", id: ids.join(","), key }));
  if (!v.ok) return [];
  return ((await v.json()).items || []).map((x) => ({
    source: "youtube", titre: x.snippet?.title, chaine: x.snippet?.channelTitle,
    vues: Number(x.statistics?.viewCount || 0), url: "https://www.youtube.com/shorts/" + x.id
  })).sort((a, b) => b.vues - a.vues);
}

export async function redditSignals(subreddits, fetchImpl = fetch) {
  const out = [];
  for (const sub of subreddits) {
    if (!/^[A-Za-z0-9_]{2,30}$/.test(sub)) continue;
    try {
      const r = await fetchImpl(`https://www.reddit.com/r/${sub}/top.json?t=week&limit=10`, { headers: { "User-Agent": "coach-viral-radar/1.0" } });
      if (!r.ok) continue;
      for (const c of (await r.json()).data?.children || []) {
        out.push({ source: "reddit", sub, titre: c.data?.title, votes: c.data?.ups, commentaires: c.data?.num_comments, url: "https://www.reddit.com" + c.data?.permalink });
      }
    } catch { /* source indisponible : on continue sans */ }
  }
  return out;
}

/* Recherche web par Claude : renvoie un résumé texte avec les adresses trouvées. */
export async function webResearch(client, niche, lang, { maxUses = 5 } = {}) {
  const prompt = `Find what is trending RIGHT NOW (last 7 days) in the niche "${niche}" for short-video creators in ${COUNTRY[lang] || "FR"}: ` +
    "news, challenges, viral sounds or formats, frequent questions, events coming up in the next 2 weeks. " +
    "Report each signal in one line with its date and URL. Do not invent anything; say when you find nothing.";
  /* Gemini : recherche Google intégrée (gratuite dans les limites de l'offre gratuite). */
  if (client?.provider === "gemini") return client.search({ content: prompt });
  const messages = [{ role: "user", content: prompt }];
  let response;
  for (let i = 0; i < 4; i++) {
    response = await client.beta.messages.create({
      model: MODEL,
      max_tokens: 16000,
      output_config: { effort: "medium" },
      tools: [{ type: "web_search_20260209", name: "web_search", max_uses: maxUses, user_location: { type: "approximate", country: COUNTRY[lang] || "FR" } }],
      messages
    });
    if (response.stop_reason !== "pause_turn") break;
    messages.splice(1, messages.length - 1, { role: "assistant", content: response.content });
  }
  if (response.stop_reason === "refusal") return "";
  return response.content.filter((b) => b.type === "text").map((b) => b.text).join("\n").trim();
}

/* ---------- Un passage du bot pour une niche ---------- */

export async function scanNiche(client, niche, opts = {}) {
  const lang = opts.langue || "fr";
  const [web, yt, rd] = await Promise.all([
    opts.web === false ? "" : webResearch(client, niche.nom, lang).catch(() => ""),
    youtubeSignals(niche.nom, lang, opts.youtubeKey, opts.fetch).catch(() => []),
    redditSignals(niche.subreddits || [], opts.fetch).catch(() => [])
  ]);
  const previous = (opts.deja || []).slice(0, 40);
  const text = [
    `Niche: ${niche.nom}. Audience language: ${lang}.`,
    niche.public && `Target audience: ${niche.public}.`,
    "From the signals below, propose 5 to 8 short-video themes to film THIS WEEK. Prefer themes rising now and with low competition.",
    "Only cite URLs that appear in the signals. If signals are thin, say so in pourquoi_maintenant and lower potentiel.",
    previous.length && `Avoid repeating these themes already proposed: ${previous.join(" | ")}`,
    "\n# Web research\n" + (web || "(none)"),
    "\n# YouTube Shorts most viewed this week\n" + (yt.slice(0, 12).map((v) => `- ${v.titre} (${v.vues} vues, ${v.chaine}) ${v.url}`).join("\n") || "(none)"),
    "\n# Reddit top posts this week\n" + (rd.slice(0, 15).map((p) => `- r/${p.sub}: ${p.titre} (${p.votes} votes) ${p.url}`).join("\n") || "(none)")
  ].filter(Boolean).join("\n");
  const out = await ask(client, { lang, content: text, schema: RadarSchema, effort: "medium" });
  return { niche: niche.nom, date: new Date().toISOString(), signaux: { web: Boolean(web), youtube: yt.length, reddit: rd.length }, themes: out.themes };
}

/* ---------- Stockage et planification ---------- */

export class Radar {
  constructor({ client, dir, env = process.env, scan = scanNiche }) {
    this.client = client;
    this.dir = dir;
    this.env = env;
    this.scan = scan;
    this.running = false;
  }
  file(name) { return path.join(this.dir, name); }
  async niches() {
    try { return JSON.parse(await readFile(this.file("niches.json"), "utf8")); }
    catch {
      return (this.env.RADAR_NICHES || "").split(";").map((s) => s.trim()).filter(Boolean).map((nom) => ({ nom, subreddits: [] }));
    }
  }
  async saveNiches(list) {
    await mkdir(this.dir, { recursive: true });
    await writeFile(this.file("niches.json"), JSON.stringify(list, null, 2));
  }
  async results(nom) {
    try { return JSON.parse(await readFile(this.file(slug(nom) + ".json"), "utf8")); } catch { return []; }
  }
  /* Analyse toutes les niches (ou une seule) ; garde les 10 derniers passages par niche. */
  async run(only = null) {
    if (this.running) return { deja_en_cours: true };
    this.running = true;
    const done = [];
    try {
      await mkdir(this.dir, { recursive: true });
      for (const n of await this.niches()) {
        if (only && n.nom !== only) continue;
        const history = await this.results(n.nom);
        const deja = history.flatMap((h) => h.themes.map((t) => t.theme));
        try {
          const r = await this.scan(this.client, n, { langue: n.langue || "fr", youtubeKey: this.env.YOUTUBE_API_KEY, deja, web: this.env.RADAR_WEB !== "0" });
          await writeFile(this.file(slug(n.nom) + ".json"), JSON.stringify([r, ...history].slice(0, 10), null, 2));
          done.push({ niche: n.nom, themes: r.themes.length });
        } catch (e) {
          done.push({ niche: n.nom, erreur: String(e.message || e).slice(0, 200) });
        }
      }
      return { fait: done };
    } finally {
      this.running = false;
    }
  }
  /* Lance le bot chaque jour à l'heure RADAR_HEURE (heure du serveur). */
  schedule() {
    const h = this.env.RADAR_HEURE;
    if (h === undefined || h === "") return null;
    let lastDay = "";
    const t = setInterval(() => {
      const now = new Date();
      const day = now.toISOString().slice(0, 10);
      if (now.getHours() === Number(h) && day !== lastDay) { lastDay = day; this.run().catch(() => {}); }
    }, 60_000);
    t.unref();
    return t;
  }
}
