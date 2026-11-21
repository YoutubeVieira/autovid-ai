#!/usr/bin/env node
// Néon Bay - générateur de plans vidéo avec Google Veo (Node 18+, aucune dépendance).
//
// Usage :
//   node tools/veo/veo.js [fichier-plans.json] [options]
//
// Options :
//   --dry-run            affiche les requêtes sans appeler l'API (mode par défaut sans clé)
//   --only <id[,id]>     ne génère que ces plans
//   --aspect <9:16|16:9> force le format pour tous les plans
//   --model <id>         force le modèle (sinon celui de shots.json)
//   --backend <gemini|vertex>  gemini = clé API Google AI Studio (défaut) ; vertex = Google Cloud
//   --force              régénère même si le MP4 existe déjà
//   --out <dossier>      dossier de sortie (défaut : neon-bay/marketing/veo)
//   --yes                ne demande pas de confirmation avant de dépenser
//
// Secrets : GEMINI_API_KEY (backend gemini) ou GOOGLE_ACCESS_TOKEN / gcloud (backend vertex)
// sont lus dans l'environnement uniquement. Ils ne sont jamais écrits ni affichés.

'use strict';
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { execFileSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..', '..');           // neon-bay/
const GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta';
const POLL_EVERY_MS = 10_000;
const POLL_TIMEOUT_MS = 12 * 60_000;
const MAX_RETRIES = 4;

// Tarifs indicatifs en dollars par seconde de vidéo (voir VEO.md pour les sources).
// À vérifier avant chaque campagne : Google les change souvent.
const PRICES = {
  'veo-3.1-generate-preview': { '720p': 0.40, '1080p': 0.40, '4k': 0.60 },
  'veo-3.1-fast-generate-preview': { '720p': 0.10, '1080p': 0.12, '4k': 0.30 },
  'veo-3.1-lite-generate-preview': { '720p': 0.05, '1080p': 0.08 },
  'veo-3.1-generate-001': { '720p': 0.40, '1080p': 0.40, '4k': 0.60 },
  'veo-3.1-fast-generate-001': { '720p': 0.10, '1080p': 0.12, '4k': 0.30 },
};

// ---------------------------------------------------------------- arguments
function parseArgs(argv) {
  const o = { file: path.join(__dirname, 'shots.json'), dryRun: false, only: null, aspect: null,
    model: null, backend: null, force: false, out: path.join(ROOT, 'marketing', 'veo'), yes: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => { if (i + 1 >= argv.length) die(`Option ${a} : valeur manquante.`); return argv[++i]; };
    if (a === '--dry-run') o.dryRun = true;
    else if (a === '--only') o.only = next().split(',').map(s => s.trim()).filter(Boolean);
    else if (a === '--aspect') o.aspect = next();
    else if (a === '--model') o.model = next();
    else if (a === '--backend') o.backend = next();
    else if (a === '--force') o.force = true;
    else if (a === '--out') o.out = path.resolve(next());
    else if (a === '--yes' || a === '-y') o.yes = true;
    else if (a === '--help' || a === '-h') { printHelp(); process.exit(0); }
    else if (a.startsWith('--')) die(`Option inconnue : ${a} (voir --help)`);
    else o.file = path.resolve(a);
  }
  if (o.aspect && !['9:16', '16:9'].includes(o.aspect)) die('--aspect doit valoir 9:16 ou 16:9.');
  if (o.backend && !['gemini', 'vertex'].includes(o.backend)) die('--backend doit valoir gemini ou vertex.');
  return o;
}

function printHelp() {
  const src = fs.readFileSync(__filename, 'utf8').split('\n');
  console.log(src.slice(1, 19).map(l => l.replace(/^\/\/ ?/, '')).join('\n'));
}

function die(msg, code = 1) { console.error(`\nErreur : ${msg}`); process.exit(code); }
const sleep = ms => new Promise(r => setTimeout(r, ms));
const log = (...a) => console.log(...a);

// ---------------------------------------------------------------- plans
function loadShots(file, opts) {
  let data;
  try { data = JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch (e) { die(`Impossible de lire ${file} : ${e.message}`); }
  const d = data.defaults || {};
  const backend = opts.backend || d.backend || 'gemini';
  const model = opts.model || (backend === 'vertex' ? (d.vertexModel || d.model) : d.model);
  if (!model) die('Aucun modèle indiqué (defaults.model dans le fichier de plans, ou --model).');
  if (!Array.isArray(data.shots) || !data.shots.length) die('Le fichier ne contient aucun plan ("shots").');

  const ids = new Set();
  let shots = data.shots.map((s, i) => {
    if (!s.id || !/^[a-z0-9-]+$/.test(s.id)) die(`Plan n°${i + 1} : "id" manquant ou invalide (minuscules, chiffres, tirets).`);
    if (ids.has(s.id)) die(`Identifiant en double : ${s.id}`);
    ids.add(s.id);
    if (!s.prompt) die(`Plan ${s.id} : "prompt" manquant.`);
    const shot = {
      id: s.id, title: s.title || s.id,
      prompt: [s.prompt, d.style].filter(Boolean).join(' '),
      negativePrompt: [s.negativePrompt, d.negativePrompt].filter(Boolean).join(', '),
      aspectRatio: opts.aspect || s.aspectRatio || d.aspectRatio || '9:16',
      durationSeconds: Number(s.durationSeconds || d.durationSeconds || 8),
      resolution: s.resolution || d.resolution || '720p',
      personGeneration: s.personGeneration || d.personGeneration || null,
      generateAudio: s.generateAudio ?? d.generateAudio ?? false,
      seed: s.seed ?? null,
      image: s.image ? path.resolve(path.dirname(file), s.image) : null,
    };
    if (![4, 6, 8].includes(shot.durationSeconds)) die(`Plan ${s.id} : durationSeconds doit valoir 4, 6 ou 8.`);
    if (!['720p', '1080p', '4k'].includes(shot.resolution)) die(`Plan ${s.id} : resolution doit valoir 720p, 1080p ou 4k.`);
    if (shot.resolution !== '720p' && shot.durationSeconds !== 8)
      die(`Plan ${s.id} : en ${shot.resolution}, Veo 3.1 n'accepte que 8 secondes.`);
    if (shot.image && !fs.existsSync(shot.image)) die(`Plan ${s.id} : image de départ introuvable (${shot.image}).`);
    return shot;
  });
  if (opts.only) {
    const unknown = opts.only.filter(id => !ids.has(id));
    if (unknown.length) die(`Plan(s) inconnu(s) : ${unknown.join(', ')}. Disponibles : ${[...ids].join(', ')}`);
    shots = shots.filter(s => opts.only.includes(s.id));
  }
  return { shots, model, backend };
}

function estimate(shots, model) {
  const table = PRICES[model];
  let total = 0, unknown = false;
  for (const s of shots) {
    const p = table && table[s.resolution];
    if (p == null) unknown = true; else total += p * s.durationSeconds;
  }
  return { total, unknown, seconds: shots.reduce((n, s) => n + s.durationSeconds, 0) };
}

// ---------------------------------------------------------------- requêtes
function buildBody(shot, backend) {
  const instance = { prompt: shot.prompt };
  if (shot.image) {
    const ext = path.extname(shot.image).toLowerCase();
    const mimeType = ext === '.png' ? 'image/png' : 'image/jpeg';
    instance.image = { bytesBase64Encoded: fs.readFileSync(shot.image).toString('base64'), mimeType };
  }
  const parameters = {
    aspectRatio: shot.aspectRatio,
    durationSeconds: shot.durationSeconds,
    resolution: shot.resolution,
  };
  if (shot.negativePrompt) parameters.negativePrompt = shot.negativePrompt;
  if (shot.personGeneration) parameters.personGeneration = shot.personGeneration;
  if (shot.seed != null) parameters.seed = shot.seed;
  if (backend === 'vertex') {
    parameters.sampleCount = 1;
    parameters.generateAudio = !!shot.generateAudio;   // Vertex : la vidéo muette coûte moins cher
  }
  return { instances: [instance], parameters };
}

function redactBody(body) {
  const copy = JSON.parse(JSON.stringify(body));
  for (const inst of copy.instances) {
    if (inst.image) inst.image.bytesBase64Encoded = `<${Math.round(inst.image.bytesBase64Encoded.length * 3 / 4 / 1024)} Ko en base64>`;
  }
  return copy;
}

// ---------------------------------------------------------------- backends
function geminiBackend(model, apiKey) {
  const headers = { 'x-goog-api-key': apiKey, 'Content-Type': 'application/json' };
  return {
    name: 'gemini',
    startUrl: `${GEMINI_BASE}/models/${model}:predictLongRunning`,
    async check() {
      const r = await httpJson('GET', `${GEMINI_BASE}/models/${model}`, headers);
      if (r.status === 404) {
        throw new FatalError(`Le modèle « ${model} » n'existe pas (ou plus) sur l'API Gemini.\n` +
          `  Google a annoncé l'arrêt des modèles Veo 3.1 « preview » sur l'API Gemini à l'automne 2026.\n` +
          `  Solutions : --backend vertex (Veo 3.1 GA sur Google Cloud), ou un autre --model (voir VEO.md).`);
      }
      if (!r.ok) throw apiError(r, 'vérification du modèle');
    },
    async start(body) {
      const r = await httpJson('POST', this.startUrl, headers, body);
      if (!r.ok) throw apiError(r, 'lancement');
      if (!r.json || !r.json.name) throw new Error('Réponse inattendue : pas de nom d\'opération.');
      return r.json.name;
    },
    async poll(opName) {
      const r = await httpJson('GET', `${GEMINI_BASE}/${opName}`, headers);
      if (!r.ok) throw apiError(r, 'suivi');
      return r.json;
    },
    // Réponse Gemini : response.generateVideoResponse.generatedSamples[].video.uri
    extract(op) {
      const gvr = (op.response && (op.response.generateVideoResponse || op.response)) || {};
      const samples = gvr.generatedSamples || gvr.generatedVideos || [];
      const filtered = { count: gvr.raiMediaFilteredCount || 0, reasons: gvr.raiMediaFilteredReasons || [] };
      const uris = samples.map(s => (s.video && (s.video.uri || s.video.gcsUri)) || s.uri).filter(Boolean);
      return { uris, b64: [], filtered };
    },
    async download(uri, dest) {
      const res = await fetch(uri, { headers: { 'x-goog-api-key': apiKey }, redirect: 'follow' });
      if (!res.ok) throw new Error(`Téléchargement refusé (HTTP ${res.status}). Les vidéos ne restent que 2 jours sur les serveurs de Google.`);
      fs.writeFileSync(dest, Buffer.from(await res.arrayBuffer()));
    },
  };
}

function vertexBackend(model) {
  const project = process.env.VERTEX_PROJECT || process.env.GOOGLE_CLOUD_PROJECT;
  const location = process.env.VERTEX_LOCATION || 'us-central1';
  if (!project) throw new FatalError('Backend vertex : définis VERTEX_PROJECT (identifiant du projet Google Cloud).');
  let token = process.env.GOOGLE_ACCESS_TOKEN;
  if (!token) {
    try { token = execFileSync('gcloud', ['auth', 'print-access-token'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); }
    catch { throw new FatalError('Backend vertex : pas de GOOGLE_ACCESS_TOKEN et « gcloud auth print-access-token » a échoué (lance « gcloud auth login »).'); }
  }
  const base = `https://${location}-aiplatform.googleapis.com/v1/projects/${project}/locations/${location}/publishers/google/models/${model}`;
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  return {
    name: 'vertex',
    startUrl: `${base}:predictLongRunning`,
    async check() { /* la première requête dira si le modèle est accessible */ },
    async start(body) {
      const r = await httpJson('POST', this.startUrl, headers, body);
      if (!r.ok) throw apiError(r, 'lancement');
      return r.json.name;
    },
    async poll(opName) {
      const r = await httpJson('POST', `${base}:fetchPredictOperation`, headers, { operationName: opName });
      if (!r.ok) throw apiError(r, 'suivi');
      return r.json;
    },
    // Réponse Vertex : response.videos[].bytesBase64Encoded (ou gcsUri si storageUri fourni)
    extract(op) {
      const resp = op.response || {};
      const videos = resp.videos || [];
      return {
        uris: videos.map(v => v.gcsUri).filter(Boolean),
        b64: videos.map(v => v.bytesBase64Encoded).filter(Boolean),
        filtered: { count: resp.raiMediaFilteredCount || 0, reasons: resp.raiMediaFilteredReasons || [] },
      };
    },
    async download(uri) {
      throw new Error(`Vidéo déposée sur Cloud Storage (${uri}) : récupère-la avec « gsutil cp ${uri} . ».`);
    },
  };
}

// ---------------------------------------------------------------- HTTP et erreurs
class FatalError extends Error {}
class QuotaError extends Error {}
class SafetyError extends Error {}

async function httpJson(method, url, headers, body) {
  let res;
  try {
    res = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined });
  } catch (e) {
    return { ok: false, status: 0, json: null, text: `réseau injoignable (${e.cause ? e.cause.code || e.cause.message : e.message})` };
  }
  const text = await res.text();
  let json = null;
  try { json = text ? JSON.parse(text) : null; } catch { /* pas du JSON */ }
  return { ok: res.ok, status: res.status, json, text, retryAfter: res.headers.get('retry-after') };
}

function apiError(r, step) {
  const err = (r.json && r.json.error) || {};
  const msg = err.message || r.text || '';
  const status = err.status || '';
  const short = `${step} : HTTP ${r.status} ${status} ${msg}`.trim().slice(0, 600);
  if (r.status === 429 || status === 'RESOURCE_EXHAUSTED') {
    const e = new QuotaError(short); e.retryAfter = Number(r.retryAfter) || 0; return e;
  }
  if (r.status === 401 || r.status === 403) return new FatalError(`${short}\n  Clé refusée, facturation non activée sur le projet, ou modèle non autorisé pour ce compte.`);
  if (r.status === 404) return new FatalError(`${short}\n  Modèle ou opération introuvable : vérifie le nom du modèle (voir VEO.md).`);
  if (r.status === 400 && /safety|blocked|responsible|policy|sensitive/i.test(msg)) return new SafetyError(short);
  if (r.status === 400) return new FatalError(`${short}\n  Paramètre refusé : vérifie format, durée et résolution du plan.`);
  const e = new Error(short); e.retryable = r.status === 0 || r.status >= 500; return e;
}

async function withRetry(label, fn) {
  for (let attempt = 0; ; attempt++) {
    try { return await fn(); }
    catch (e) {
      const retryable = e instanceof QuotaError || e.retryable;
      if (!retryable || attempt >= MAX_RETRIES) throw e;
      const wait = e instanceof QuotaError
        ? Math.max(e.retryAfter * 1000, 30_000 * 2 ** attempt)   // quota : 30 s, 60 s, 120 s, 240 s
        : 5_000 * 2 ** attempt;
      log(`   ${label} : ${e instanceof QuotaError ? 'quota atteint' : 'erreur temporaire'}, nouvel essai dans ${Math.round(wait / 1000)} s…`);
      await sleep(wait);
    }
  }
}

// ---------------------------------------------------------------- génération
async function generate(shot, api, outDir) {
  const body = buildBody(shot, api.name);
  const opName = await withRetry(shot.id, () => api.start(body));
  log(`   opération lancée : ${opName.split('/').pop()}`);
  const t0 = Date.now();
  let op;
  for (;;) {
    await sleep(POLL_EVERY_MS);
    op = await withRetry(shot.id, () => api.poll(opName));
    if (op.done) break;
    if (Date.now() - t0 > POLL_TIMEOUT_MS) throw new Error(`pas de résultat après ${POLL_TIMEOUT_MS / 60000} min (opération ${opName}).`);
    process.stdout.write(`   en cours… ${Math.round((Date.now() - t0) / 1000)} s\r`);
  }
  process.stdout.write('\n');
  if (op.error) {
    const m = op.error.message || JSON.stringify(op.error);
    if (/safety|blocked|responsible|policy|filter/i.test(m)) throw new SafetyError(m);
    throw new Error(`l'opération a échoué : ${m}`);
  }
  const { uris, b64, filtered } = api.extract(op);
  if (!uris.length && !b64.length) {
    if (filtered.count || filtered.reasons.length)
      throw new SafetyError(`vidéo bloquée par le filtre de sécurité de Google : ${filtered.reasons.join(' | ') || 'raison non précisée'}`);
    throw new Error('opération terminée sans vidéo (réponse inattendue).');
  }
  const dest = path.join(outDir, `${shot.id}.mp4`);
  if (b64.length) fs.writeFileSync(dest, Buffer.from(b64[0], 'base64'));
  else await withRetry(shot.id, () => api.download(uris[0], dest));
  return { file: dest, seconds: Math.round((Date.now() - t0) / 1000) };
}

function ask(q) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise(res => rl.question(q, a => { rl.close(); res(a.trim().toLowerCase()); }));
}

// ---------------------------------------------------------------- main
async function main() {
  if (typeof fetch !== 'function') die('Node 18 ou plus récent est nécessaire (fetch intégré).');
  const opts = parseArgs(process.argv.slice(2));
  const { shots, model, backend } = loadShots(opts.file, opts);
  const apiKey = process.env.GEMINI_API_KEY;

  let dry = opts.dryRun;
  if (!dry && backend === 'gemini' && !apiKey) {
    log('GEMINI_API_KEY absente : passage automatique en --dry-run (aucun appel, aucun coût).');
    dry = true;
  }

  const est = estimate(shots, model);
  log(`\nNéon Bay x Veo | backend ${backend} | modèle ${model} | ${shots.length} plan(s), ${est.seconds} s de vidéo`);
  log(est.unknown
    ? 'Coût estimé : tarif inconnu pour ce modèle (voir VEO.md).'
    : `Coût estimé : ${est.total.toFixed(2)} $ (hors régénérations ; tarifs à revérifier, voir VEO.md)`);

  const startUrl = backend === 'gemini'
    ? `${GEMINI_BASE}/models/${model}:predictLongRunning`
    : `https://${process.env.VERTEX_LOCATION || 'us-central1'}-aiplatform.googleapis.com/v1/projects/${process.env.VERTEX_PROJECT || '<VERTEX_PROJECT>'}/locations/${process.env.VERTEX_LOCATION || 'us-central1'}/publishers/google/models/${model}:predictLongRunning`;

  if (dry) {
    log('\n=== DRY-RUN : requêtes qui seraient envoyées (rien n\'est appelé) ===');
    for (const s of shots) {
      const dest = path.join(opts.out, `${s.id}.mp4`);
      log(`\n--- ${s.id} : ${s.title}`);
      log(`POST ${startUrl}`);
      log(backend === 'gemini' ? 'x-goog-api-key: <GEMINI_API_KEY>' : 'Authorization: Bearer <jeton gcloud>');
      log(JSON.stringify(redactBody(buildBody(s, backend)), null, 2));
      log(`-> puis suivi de l'opération toutes les ${POLL_EVERY_MS / 1000} s, téléchargement vers ${path.relative(ROOT, dest)}${fs.existsSync(dest) ? ' (existe déjà : ignoré sans --force)' : ''}`);
    }
    log('\nFin du dry-run.');
    return;
  }

  fs.mkdirSync(opts.out, { recursive: true });
  const todo = shots.filter(s => opts.force || !fs.existsSync(path.join(opts.out, `${s.id}.mp4`)));
  const skipped = shots.length - todo.length;
  if (skipped) log(`${skipped} plan(s) déjà présents, ignorés (--force pour régénérer).`);
  if (!todo.length) { log('Rien à faire.'); return; }

  if (!opts.yes && process.stdin.isTTY) {
    const e2 = estimate(todo, model);
    const a = await ask(`Lancer ${todo.length} génération(s) payante(s) (~${e2.unknown ? '?' : e2.total.toFixed(2)} $) ? [o/N] `);
    if (a !== 'o' && a !== 'oui' && a !== 'y') { log('Annulé.'); return; }
  }

  let api;
  try {
    api = backend === 'vertex' ? vertexBackend(model) : geminiBackend(model, apiKey);
    await api.check();
  } catch (e) { die(e.message); }

  const report = { date: new Date().toISOString(), backend, model, results: [] };
  for (const [i, s] of todo.entries()) {
    log(`\n[${i + 1}/${todo.length}] ${s.id} : ${s.title} (${s.aspectRatio}, ${s.durationSeconds} s, ${s.resolution})`);
    try {
      const r = await generate(s, api, opts.out);
      log(`   OK -> ${path.relative(ROOT, r.file)} (${r.seconds} s d'attente)`);
      report.results.push({ id: s.id, status: 'ok', file: path.relative(ROOT, r.file) });
    } catch (e) {
      const kind = e instanceof SafetyError ? 'filtre-securite' : e instanceof QuotaError ? 'quota' : 'erreur';
      log(`   ÉCHEC (${kind}) : ${e.message}`);
      if (e instanceof SafetyError) log('   Conseil : reformule le prompt (moins de violence, pas de personne réelle ni de marque), puis relance avec --only ' + s.id);
      report.results.push({ id: s.id, status: kind, message: e.message.slice(0, 500) });
      if (e instanceof FatalError) { log('   Erreur bloquante : arrêt des générations suivantes.'); break; }
      if (e instanceof QuotaError) { log('   Quota épuisé malgré les nouveaux essais : arrêt. Relance plus tard, les plans déjà faits seront gardés.'); break; }
    }
  }
  const reportFile = path.join(opts.out, 'rapport.json');
  fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
  const ok = report.results.filter(r => r.status === 'ok').length;
  log(`\nTerminé : ${ok}/${todo.length} plan(s) générés. Rapport : ${path.relative(ROOT, reportFile)}`);
  if (ok < todo.length) process.exitCode = 2;
}

main().catch(e => die(e.stack || e.message));
