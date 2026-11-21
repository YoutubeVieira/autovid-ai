/* Néon Bay : moteur du jeu */
(() => {
'use strict';
const D = window.NB_DATA;
const PI = Math.PI, TAU = PI * 2;
const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
const rnd = (a = 1, b) => b === undefined ? Math.random() * a : a + Math.random() * (b - a);
const pick = a => a[(Math.random() * a.length) | 0];
const dist = (a, b, c, d) => Math.hypot(c - a, d - b);
const angDiff = (t, a) => { let d = (t - a) % TAU; if (d > PI) d -= TAU; if (d < -PI) d += TAU; return d; };
function mulberry(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const hash = (x, y) => (((x * 73856093) ^ (y * 19349663)) >>> 0) % 1000;
const lsGet = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const lsSet = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
const I18 = window.NB_I18N || null;
const TR = v => I18 ? I18.t(v) : v;
const fmt = n => { const l = I18 ? I18.lang : 'fr'; return l === 'en' ? '$' + Math.round(n).toLocaleString('en-US') : Math.round(n).toLocaleString(l === 'fr' ? 'fr-FR' : l) + ' $'; };
const AU = window.NB_AUDIO || null;
const au = (fn, ...a) => { try { if (AU && AU.ready) AU[fn](...a); } catch (e) {} };
const spatial = (x, y) => { const d = Math.hypot(x - P.x, y - P.y); return [Math.max(-1, Math.min(1, (x - P.x) / 600)), Math.max(0, 1 - d / 1000)]; };
const ST = window.NB_STORE || null;
const isPlay = () => !!(ST && ST.isPlay);
const PORTAL = window.NB_PORTAL_API && window.NB_PORTAL_API.active ? window.NB_PORTAL_API : null;
const priceLabel = () => isPlay() ? (ST.state.price || '') : D.SHOP_CONFIG.price;
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// ---------- codes de déblocage ----------
const ALPH = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
function fnv(s) { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); } return h >>> 0; }
function codeCheck(body) { let h = fnv(D.SHOP_CONFIG.salt + body), o = ''; for (let i = 0; i < 4; i++) { o += ALPH[h % 32]; h = Math.floor(h / 32); } return o; }
function validCode(raw) {
  const c = String(raw).toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (c.length !== 16 || !c.startsWith('NBAY')) return false;
  return codeCheck(c.slice(4, 12)) === c.slice(12);
}

// ---------- sauvegarde ----------
const SAVE_KEY = 'neonbay.save.v2';
const fresh = () => ({ money: 500, owned: { pistol: true }, weapon: 'pistol', armor: 0, medkits: 2, nitro: 0, perks: {}, done: {}, maxLevel: 1, premium: false });
let save = (() => { try { const s = JSON.parse(lsGet(SAVE_KEY)); if (s && s.owned) return Object.assign(fresh(), s); } catch (e) {} return fresh(); })();
save.owned.fists = true;
save.outfit = Object.assign({ jacket: 'neon', shirt: 'white', pants: 'dark', hat: 'none', hair: 'short', hairColor: 'black', skin: 't2', shoes: 'white', chain: 'none' }, save.outfit || {});
save.wardrobe = save.wardrobe || {};
const outfitVal = cat => { const c = D.OUTFITS[cat]; const it = c.items.find(i => i[0] === save.outfit[cat]) || c.items[0]; return it[3]; };
function playerLook() {
  const j = outfitVal('jacket');
  return { shirt: outfitVal('shirt'), jacket: j, sleeve: j || outfitVal('shirt'), longSleeve: !!j, pants: outfitVal('pants'), skin: outfitVal('skin'), hair: outfitVal('hairColor'), hairStyle: outfitVal('hair'), hat: outfitVal('hat'), shoes: outfitVal('shoes'), chain: outfitVal('chain'), gun: true };
}
const persist = () => lsSet(SAVE_KEY, JSON.stringify(save));

// ---------- monde ----------
const T = 64, B = 8, N = 82, W = N * T;
const ROAD = 0, WALK = 1, BLD = 2, PARK = 3, PAD = 4, WATER = 5, TREE = 6, PLAZA = 7, SHOP = 8, TUNNEL = 9, GARAGE = 10;
let world = null;
function buildWorld(region) {
  const R = mulberry(region.seed * 7919 + 13);
  const map = new Uint8Array(N * N), bcol = new Uint8Array(N * N), wh = new Uint8Array(N * N);
  const entries = Object.entries(region.blocks), tot = entries.reduce((s, e) => s + e[1], 0);
  const chooseType = () => { let r = R() * tot; for (const [k, w] of entries) { r -= w; if (r <= 0) return k; } return entries[0][0]; };
  for (let by = 0; by < 10; by++) for (let bx = 0; bx < 10; bx++) {
    let type = chooseType();
    if (region.id === 'col' && (bx === 0 || by === 0 || bx === 9 || by === 9) && R() < .6) type = 'jungle';
    const c = (R() * 255) | 0;
    for (let ly = 2; ly < 8; ly++) for (let lx = 2; lx < 8; lx++) {
      const x = bx * B + lx, y = by * B + ly, i = y * N + x;
      let t = WALK;
      if (lx > 2 && lx < 7 && ly > 2 && ly < 7) {
        switch (type) {
          case 'park': t = (hash(x, y) % 6 === 0) ? TREE : PARK; break;
          case 'plaza': t = (lx > 3 && lx < 6 && ly > 3 && ly < 6) ? WATER : PLAZA; break;
          case 'water': t = (ly === 4 || ly === 5) ? WATER : BLD; break;
          case 'jungle': t = R() < .5 ? TREE : PARK; break;
          case 'favela': t = R() < .72 ? BLD : WALK; break;
          case 'split': t = lx === 5 ? WALK : BLD; break;
          case 'warehouse': t = BLD; wh[i] = 1; break;
          default: t = BLD;
        }
      }
      map[i] = t;
      bcol[i] = type === 'favela' ? (R() * 255) | 0 : (type === 'split' && lx > 5 ? c + 1 : c);
    }
  }
  // lieux spéciaux
  const blocks = []; for (let by = 0; by < 10; by++) for (let bx = 0; bx < 10; bx++) blocks.push([bx, by]);
  for (let i = blocks.length - 1; i > 0; i--) { const j = (R() * (i + 1)) | 0; [blocks[i], blocks[j]] = [blocks[j], blocks[i]]; }
  let bi = 0; const take = () => blocks[bi++];
  const at = (tx, ty, t) => { map[ty * N + tx] = t; return { x: (tx + .5) * T, y: (ty + .5) * T }; };
  const pads = [], shops = [], garages = [], tunnels = [];
  for (let k = 0; k < 4; k++) { const [bx, by] = take(); pads.push(at(bx * B + 4, by * B + 7, PAD)); }
  for (let k = 0; k < 4; k++) { const [bx, by] = take(); shops.push(at(bx * B + 3, by * B + 2, SHOP)); }
  for (let k = 0; k < 4; k++) { const [bx, by] = take(); garages.push(at(bx * B + 6, by * B + 7, GARAGE)); }
  const tb = []; for (let k = 0; k < 8; k++) tb.push(take());
  const used = new Set();
  for (let k = 0; k < tb.length; k++) {
    if (used.has(k)) continue;
    let best = -1, bd = 0;
    for (let j = 0; j < tb.length; j++) { if (j === k || used.has(j)) continue; const d = Math.abs(tb[j][0] - tb[k][0]) + Math.abs(tb[j][1] - tb[k][1]); if (d > bd) { bd = d; best = j; } }
    if (best < 0) break;
    used.add(k); used.add(best);
    const a = at(tb[k][0] * B + 7, tb[k][1] * B + 4, TUNNEL), b = at(tb[best][0] * B + 7, tb[best][1] * B + 4, TUNNEL);
    a.to = b; b.to = a; tunnels.push(a, b);
  }
  const hb = take(), sb = take();
  const hospital = at(hb[0] * B + 2, hb[1] * B + 4, WALK), station = at(sb[0] * B + 2, sb[1] * B + 4, WALK);
  // monuments : on réserve des blocs selon le style du pays
  const lm = new Uint8Array(N * N), landmarks = [];
  const looks = region.look || {};
  for (const id of (looks.landmarks || [])) {
    if (['wheel', 'rock', 'cablecar', 'tower'].includes(id)) { landmarks.push({ id }); continue; }
    const blk = take(); if (!blk) break; const [bx, by] = blk;
    const walk = ['stadium', 'pitch', 'plantation'].includes(id);
    for (let ly = 3; ly < 7; ly++) for (let lx = 3; lx < 7; lx++) {
      const i = (by * B + ly) * N + bx * B + lx;
      if (id === 'campanile') { map[i] = (lx === 4 || lx === 5) && (ly === 4 || ly === 5) ? BLD : PLAZA; lm[i] = map[i] === BLD ? 1 : 0; }
      else if (walk) { map[i] = PARK; lm[i] = 2; }
      else { map[i] = BLD; lm[i] = 1; }
    }
    landmarks.push({ id, bx, by, x: (bx * B + 5) * T, y: (by * B + 5) * T });
  }
  // minicarte
  const mm = document.createElement('canvas'); mm.width = mm.height = N * 2;
  const m = mm.getContext('2d'), p = region.pal;
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const t = map[y * N + x];
    m.fillStyle = t === ROAD ? '#4a4078' : t === BLD ? '#120e22' : t === PARK || t === TREE ? p.park : t === WATER ? '#1f6f9a' : '#2a2346';
    m.fillRect(x * 2, y * 2, 2, 2);
  }
  const tags = []; for (let k = 0; tags.length < 12 && k < 4000; k++) { const tx = 2 + ((R() * (N - 4)) | 0), ty = 2 + ((R() * (N - 4)) | 0); const t = map[ty * N + tx]; if ((t === WALK || t === PARK || t === PLAZA) && !tags.some(q => Math.abs(q.tx - tx) + Math.abs(q.ty - ty) < 12)) tags.push({ tx, ty, x: (tx + .5) * T, y: (ty + .5) * T }); }
  return { tags, region, map, bcol, wh, lm, landmarks, pads, shops, garages, tunnels, hospital, station, mm };
}
const tileAt = (x, y) => { const tx = Math.floor(x / T), ty = Math.floor(y / T); if (tx < 0 || ty < 0 || tx >= N || ty >= N) return BLD; return world.map[ty * N + tx]; };
const solidT = t => t === BLD || t === WATER || t === TREE;
const solid = (x, y) => solidT(tileAt(x, y));
const blocksShot = (x, y) => { const t = tileAt(x, y); return t === BLD || t === TREE; };
const isWalkable = t => t === WALK || t === PLAZA || t === PARK;
function los(ax, ay, bx, by) { const d = dist(ax, ay, bx, by), n = Math.ceil(d / 24); for (let i = 1; i < n; i++) { if (blocksShot(ax + (bx - ax) * i / n, ay + (by - ay) * i / n)) return false; } return true; }
function randWalk(minD, maxD, fx, fy) {
  for (let k = 0; k < 600; k++) {
    const tx = (Math.random() * N) | 0, ty = (Math.random() * N) | 0;
    if (world.map[ty * N + tx] !== WALK) continue;
    const x = (tx + .5) * T, y = (ty + .5) * T, d = dist(x, y, fx, fy);
    if (d >= minD && d <= maxD) return { x, y };
  }
  return randWalk(0, W * 2, fx, fy);
}
function freeNear(cx, cy, r) { for (let k = 0; k < 60; k++) { const x = cx + rnd(-r, r), y = cy + rnd(-r, r); const t = tileAt(x, y); if (isWalkable(t) && !solid(x + 10, y) && !solid(x - 10, y) && !solid(x, y + 10) && !solid(x, y - 10)) return { x, y }; } return { x: cx, y: cy }; }

// ---------- état ----------
const S = { heat: 0, hp: 100, unseen: 0, bust: 0, time: 0, mode: 'menu', dead: 0, spawnPol: 0, msgCd: 0, tunnelCd: 0 };
const P = { x: 0, y: 0, a: 0, car: null, cd: 0, hurt: 0, armor: 0, step: 0, nitro: 0 };
let cars = [], peds = [], bullets = [], parts = [], picks = [], enemies = [], cases = [], vip = null, agent = null;
let L = null; // niveau en cours
const cam = { x: 0, y: 0, z: 1 };
let shake = 0, shootersNow = 0;
const DIRA = [0, PI / 2, PI, -PI / 2], DX = [1, 0, -1, 0], DY = [0, 1, 0, -1];
const CIV = ['#ff5d8f', '#ffd23f', '#3ee0c5', '#8b7bff', '#ff8a3d', '#e7e3f5', '#4da3ff', '#b5ff5c', '#c13cff'];
const PEDC = ['#ffcf99', '#e0a070', '#8d5a3b', '#f2d3b3', '#5c3a24', '#c68b59'];
const SHIRT = ['#ff2e93', '#21e6ff', '#ffb627', '#a6ff4d', '#ffffff', '#9d7bff', '#ff6b3d'];
const lvl = () => L ? L.n : 1;
// facilité des premiers niveaux : 0,5 au niveau 1, puis on remonte jusqu'à 1 au niveau 11
const ez = () => { const n = lvl(); return n >= 11 ? 1 : .5 + .05 * (n - 1); };
// qualité graphique : auto (selon les images par seconde), haute, moyenne, basse
const QUAL = { high: { pr: 1.75, peds: 36, traffic: 18, lod: 900, fx: true, label: 'Haute' }, medium: { pr: 1.25, peds: 24, traffic: 13, lod: 600, fx: true, label: 'Moyenne' }, low: { pr: 1, peds: 14, traffic: 8, lod: 350, fx: false, label: 'Basse' } };
const QORDER = ['high', 'medium', 'low'];
let Q = QUAL.high, qLevel = 'high';
const fpsMon = { t: 0, n: 0, slow: 0 };
function setQuality(l) { qLevel = l; Q = QUAL[l]; if (R3.ok) { if (l === 'high' && !R3.composer) setupPost(); R3.r.setPixelRatio(Math.min(Q.pr, devicePixelRatio || 1)); R3.w = 0; if (R3.shadow && l !== 'high') { R3.shadow = false; R3.r.shadowMap.enabled = false; R3.moon.castShadow = false; R3.scene.traverse(o => { if (o.material) [].concat(o.material).forEach(mm => mm.needsUpdate = true); }); } } }
function qualityLabel() { return (save.quality || 'auto') === 'auto' ? 'Auto (' + QUAL[qLevel].label + ')' : QUAL[save.quality].label; }
function monitorFps(dt) {
  if ((save.quality || 'auto') !== 'auto' || S.mode !== 'play' || S.cine) return;
  fpsMon.t += dt; fpsMon.n++;
  if (fpsMon.t >= 3) { const fps = fpsMon.n / fpsMon.t; fpsMon.t = 0; fpsMon.n = 0;
    if (fps < 38) { fpsMon.slow++; if (fpsMon.slow >= 1 && qLevel !== 'low') { setQuality(QORDER[QORDER.indexOf(qLevel) + 1]); msg('Qualité graphique réduite pour plus de fluidité'); fpsMon.slow = 0; } } else fpsMon.slow = 0; }
}
// aide après plusieurs échecs sur un même niveau
const fails = () => (L && save.fails && save.fails[L.n]) || 0;
const assist = () => Math.min(3, Math.max(0, fails() - 1));
const camRot = () => (R3.ok && save.cam && save.cam !== 'top' && R3.yaw !== undefined) ? R3.yaw + PI / 2 : 0;
const stars = () => Math.floor(S.heat);
const WBASE = id => D.WEAPONS.find(w => w.id === id) || D.WEAPONS[0];
const WUPS = [['dmg', 'Dégâts'], ['mag', 'Chargeur'], ['rate', 'Cadence'], ['acc', 'Précision']];
const wup = id => ((save.wup || {})[id]) || {};
const wepDef = id => { const b = WBASE(id), u = wup(id); if (b.melee || !Object.keys(u).length) return b; return Object.assign({}, b, { dmg: b.dmg * (1 + .15 * (u.dmg || 0)), mag: b.mag ? Math.round(b.mag * (1 + .3 * (u.mag || 0))) : b.mag, rate: b.rate * (1 - .1 * (u.rate || 0)), spread: b.spread * (1 - .25 * (u.acc || 0)) }); };
const upPrice = (id, k) => { const b = WBASE(id), l = wup(id)[k] || 0; return Math.round(Math.max(400, b.price * .18) * (l + 1) / 50) * 50; };
const armorMax = () => save.armor || 0;
const bribeDiscount = () => save.perks.contacts ? .6 : 1;

function carStyle(kind) {
  const cs = kind === 'civ' && world && world.region.look && world.region.look.cars;
  if (!cs) return { type: 'sedan', color: null };
  const ent = Object.entries(cs.types), tot = ent.reduce((a, e) => a + e[1], 0); let r = Math.random() * tot, type = 'sedan';
  for (const [k, w] of ent) { r -= w; if (r <= 0) { type = k; break; } }
  return { type, color: type === 'taxi' ? cs.taxi : type === 'bus' ? pick(['#ffd23f', '#ff006e', '#3a86ff', '#8ac926']) : pick(cs.palette) };
}
function mkCar(x, y, a, kind) { const cs = carStyle(kind); return { type: cs.type, x, y, a, v: 0, hp: kind === 'police' ? 150 + lvl() * 4 : 100, kind, color: kind === 'police' ? '#eef0ff' : (cs.color || pick(CIV)), ai: null, dir: 0, wreck: false, stuck: 0, rev: 0, lock: -1, flash: rnd(1), panic: 0 }; }
function pedLook() {
  const pl = (world && world.region.look && world.region.look.peds) || null; if (!pl) return null;
  const f = Math.random() < .5, hat = Math.random() < pl.hat, jk = Math.random() < pl.jacket;
  return { female: f, shirt: pick(pl.shirts), pants: pick(pl.pants), skin: pick(pl.skins), shorts: !f && Math.random() < pl.shorts, skirt: f && Math.random() < pl.skirt ? pick(pl.pants.concat(pl.shirts)) : null,
    hat: hat ? pick(['#111118', '#e3c78a', '#f2f2f2', '#c8102e', '#2e4a7d']) : null, hatType: hat ? pick(pl.hatTypes) : null, jacket: jk ? pick(['#2b2b33', '#5a3a22', '#1f3a5a', '#e8e4da']) : null, tie: jk && Math.random() < (pl.tie || 0) ? pick(['#8a0f1a', '#111111', '#2e4a7d']) : null,
    hair: pick(['#1a120c', '#3b2414', '#0c0c0c', '#6b4a2a', '#d8b46a', '#8a3b1c']), hairStyle: f ? pick(['long', 'ponytail', 'afro', 'short']) : pick(['short', 'short', 'afro', 'none']), longSleeve: jk || Math.random() < .3, height: rnd(.92, 1.06), shoes: pick(['#0c0b12', '#ffffff', '#5a3a22']) };
}
function mkPed(x, y) { const lk = pedLook(); return { look: lk, x, y, a: rnd(TAU), state: 'walk', t: rnd(3), skin: lk ? lk.skin : pick(PEDC), shirt: lk ? lk.shirt : pick(SHIRT), cash: Math.random() < .6 ? (10 + rnd(60)) | 0 : 0, ko: 0, step: rnd(6) }; }

// ---------- apparition ----------
function lanePoint(minD, maxD, cx, cy) {
  for (let k = 0; k < 30; k++) {
    const horiz = Math.random() < .5, r = (Math.random() * 11) | 0;
    const d = horiz ? (Math.random() < .5 ? 0 : 2) : (Math.random() < .5 ? 1 : 3);
    let x, y;
    if (horiz) { y = (r * B + (d === 0 ? 1.5 : .5)) * T; x = cx + rnd(-maxD, maxD); } else { x = (r * B + (d === 1 ? .5 : 1.5)) * T; y = cy + rnd(-maxD, maxD); }
    if (x < T || y < T || x > W - T || y > W - T) continue;
    const dd = dist(x, y, cx, cy); if (dd < minD || dd > maxD) continue;
    if (cars.some(c => dist(c.x, c.y, x, y) < 90)) continue;
    return { x, y, d };
  }
  return null;
}
function spawnTraffic() { const p = lanePoint(560, 1250, P.x, P.y); if (!p) return null; const c = mkCar(p.x, p.y, DIRA[p.d], 'civ'); c.ai = 'traffic'; c.dir = p.d; c.v = 150; cars.push(c); return c; }
function spawnPolice() { const p = lanePoint(650, 1100, P.x, P.y); if (!p) return; const c = mkCar(p.x, p.y, Math.atan2(P.y - p.y, P.x - p.x), 'police'); c.ai = 'police'; c.v = 150; if (carHits(c.x, c.y, c.a)) c.a = DIRA[p.d]; cars.push(c); }
function spawnPed() { for (let k = 0; k < 20; k++) { const x = P.x + rnd(-1000, 1000), y = P.y + rnd(-1000, 1000); if (tileAt(x, y) !== WALK) continue; const d = dist(x, y, P.x, P.y); if (d < 420 || d > 1050) continue; peds.push(mkPed(x, y)); return; } }
function parkedCar(x, y) { for (const a of DIRA) { const c = mkCar(x, y, a, 'civ'); if (!carHits(x, y, a)) { cars.push(c); return c; } } return null; }

// ---------- voitures ----------
const CORN = [[20, 9], [20, -9], [-20, 9], [-20, -9], [0, 10], [0, -10], [10, 0]];
function carHits(x, y, a) { const ca = Math.cos(a), sa = Math.sin(a); for (const [lx, ly] of CORN) if (solid(x + lx * ca - ly * sa, y + lx * sa + ly * ca)) return true; return false; }
function drive(c, dt, thr, st, hb) {
  const boost = c === P.car && P.nitro > 0;
  const maxV = (c.kind === 'police' ? 520 + lvl() * 2 : (c === P.car ? 520 : 380)) * (boost ? 1.5 : 1);
  if (boost) thr = 1;
  if (thr > 0) c.v += thr * (boost ? 900 : 440) * dt * (c.v < 0 ? 2.2 : 1); else if (thr < 0) c.v += thr * (c.v > 0 ? 760 : 320) * dt;
  c.v -= c.v * (S.rain ? .7 : .85) * dt; if (thr === 0 && Math.abs(c.v) < 10) c.v = 0;
  if (hb) c.v -= c.v * 2.2 * dt;
  c.v = clamp(c.v, -180, maxV);
  const sp = clamp(Math.abs(c.v) / 200, 0, 1);
  const na = c.a + st * (hb ? 4.2 : 2.8) * (S.rain && c === P.car ? .82 : 1) * sp * dt * (c.v < 0 ? -1 : 1);
  if (c === P.car) { // dérapage : la voiture glisse sur le côté dans les virages rapides
    const tgt = -st * Math.abs(c.v) * (hb ? .5 : .1) * sp * (S.rain ? 1.4 : 1);
    c.lat = (c.lat || 0) + (tgt - (c.lat || 0)) * Math.min(1, dt * (hb ? 2.2 : 4.5));
    c.drift = Math.abs(c.lat) / Math.max(80, Math.abs(c.v));
    if (c.drift > .18 && Math.abs(c.v) > 140) { const bx2 = c.x - Math.cos(c.a) * 15, by2 = c.y - Math.sin(c.a) * 15, px = -Math.sin(c.a) * 9, py = Math.cos(c.a) * 9;
      skid(bx2 + px, by2 + py, c.a); skid(bx2 - px, by2 - py, c.a); if (Math.random() < dt * 22) puff(bx2, by2, '#8a8698', .9); }
  } else c.lat = 0;
  if (!carHits(c.x, c.y, na) || carHits(c.x, c.y, c.a)) c.a = na;
  if (boost) parts.push({ x: c.x - Math.cos(c.a) * 22, y: c.y - Math.sin(c.a) * 22, vx: -Math.cos(c.a) * 120 + rnd(-30, 30), vy: -Math.sin(c.a) * 120 + rnd(-30, 30), life: .25, max: .25, r: 5, col: pick(['#21e6ff', '#ffffff', '#9d7bff']) });
  moveCar(c, dt);
}
function moveCar(c, dt) {
  const la = c.lat || 0, nx = c.x + (Math.cos(c.a) * c.v - Math.sin(c.a) * la) * dt, ny = c.y + (Math.sin(c.a) * c.v + Math.cos(c.a) * la) * dt;
  if (!carHits(nx, ny, c.a)) { c.x = nx; c.y = ny; return; }
  c.lat = 0;
  const hard = Math.abs(c.v) > 170;
  if (!hard && !carHits(nx, c.y, c.a)) { c.x = nx; c.v *= .95; return; }
  if (!hard && !carHits(c.x, ny, c.a)) { c.y = ny; c.v *= .95; return; }
  if (Math.abs(c.v) > 130) { { const [pn, vl] = spatial(c.x, c.y); if (vl > .1) au('crash', vl * Math.min(1, Math.abs(c.v) / 300), pn); } damageCar(c, Math.abs(c.v) * .05); sparks(c.x + Math.cos(c.a) * 20, c.y + Math.sin(c.a) * 20, 8); if (c === P.car) { shake = Math.min(12, Math.abs(c.v) / 40); vib(Math.min(120, Math.abs(c.v) / 4)); } }
  c.v = -c.v * .3;
}
const skids = []; let skidI = 0;
function skid(x, y, a) { const last = skids[(skidI + 399) % 400]; if (last && Math.abs(last.x - x) + Math.abs(last.y - y) < 6) return; skids[skidI] = { x, y, a, t: S.time }; skidI = (skidI + 1) % 400; }
function damageCar(c, n) { if (c.wreck) return; if (c === P.car && save.perks.carArmor) n *= .5; c.hp -= n; if (c.hp <= 0) explode(c); }
function explosionAt(x, y, r, dmg, byPlayer) {
  shake = Math.max(shake, 14); { const [pn, vl] = spatial(x, y); if (vl > 0) au('boom', pn, vl); if (vl > .35) vib(Math.round(80 + vl * 160)); }
  for (let i = 0; i < 34; i++) parts.push({ x, y, vx: rnd(-260, 260), vy: rnd(-260, 260), life: rnd(.4, 1), max: 1, r: rnd(4, 12), col: pick(['#ffb627', '#ff6b3d', '#ff2e93', '#fff2a8']) });
  for (let i = 0; i < 10; i++) puff(x + rnd(-20, 20), y + rnd(-20, 20), '#3b3550', 1.6);
  for (const p of peds) if (p.state !== 'ko' && dist(p.x, p.y, x, y) < r) koPed(p, byPlayer);
  for (const e of enemies) if (e.hp > 0 && dist(e.x, e.y, x, y) < r) hitEnemy(e, dmg);
  for (const o of cars) if (!o.wreck && dist(o.x, o.y, x, y) < r) setTimeout(() => damageCar(o, dmg * .7), 100);
  if (vip && !vip.inCar && vip.hp > 0 && dist(vip.x, vip.y, x, y) < r) hurtVip(dmg * .5);
  if (!P.car && dist(P.x, P.y, x, y) < r) hurt(dmg * .5);
}
function explode(c) {
  c.wreck = true; c.v = 0; c.ai = null; c.hp = 0; S.flash = { x: c.x, y: c.y, i: 6 }; S.debris = (S.debris || []).concat([{ x: c.x, y: c.y, col: c.color }]); if (S.mode === 'play' && dist(c.x, c.y, P.x, P.y) < 700) track('explosions');
  const wasPlayer = c === P.car;
  if (wasPlayer) { radioOff(); P.car = null; P.x = c.x + 30; P.y = c.y; if (solid(P.x, P.y)) P.x = c.x - 30; hurt(30); toast('Voiture détruite !'); }
  if (vip && vip.inCar === c) { vip.inCar = null; vip.x = c.x; vip.y = c.y + 26; hurtVip(30); }
  explosionAt(c.x, c.y, 85, 45, false);
  if (c.kind === 'police') addHeat(1);
  if (c.kind === 'gang') { track('kills'); picks.push({ x: c.x + 20, y: c.y, ammo: true, t: 30 }); }
}

// ---------- IA circulation ----------
function updTraffic(c, dt) {
  const fx = DX[c.dir], fy = DY[c.dir];
  const ahead = (ox, oy, r) => { const dx = ox - c.x, dy = oy - c.y, al = dx * fx + dy * fy, sd = Math.abs(dx * fy - dy * fx); return al > 0 && al < r && sd < 20; };
  let block = false;
  for (const o of cars) if (o !== c && ahead(o.x, o.y, 64)) { block = true; break; }
  if (!block && !P.car && ahead(P.x, P.y, 52)) block = true;
  if (!block) for (const p of peds) if (p.state !== 'ko' && ahead(p.x, p.y, 46)) { block = true; break; }
  const target = block ? 0 : c.panic > 0 ? 300 : 165; if (c.panic > 0) c.panic -= dt;
  c.v += (target - c.v) * Math.min(1, dt * (block ? 7 : 1.4));
  const horiz = c.dir === 0 || c.dir === 2;
  const prev = horiz ? c.x : c.y, next = prev + (horiz ? fx : fy) * c.v * dt;
  const offs = horiz ? [[.5, 1], [1.5, 3]] : [[1.5, 0], [.5, 2]];
  const lo = Math.min(prev, next), hi = Math.max(prev, next), j0 = Math.floor(lo / (B * T));
  for (let j = j0; j <= j0 + 1; j++) for (const [off, nd] of offs) {
    const L2 = (j * B + off) * T;
    if (L2 > lo && L2 <= hi && c.lock !== L2) {
      c.lock = L2;
      if (Math.random() < .3) {
        const tx = horiz ? L2 : c.x + DX[nd] * 2 * T, ty = horiz ? c.y + DY[nd] * 2 * T : L2;
        if (tx > 0 && ty > 0 && tx < W && ty < W && tileAt(tx, ty) === ROAD) { if (horiz) c.x = L2; else c.y = L2; c.dir = nd; c.a = DIRA[nd]; return; }
      }
    }
  }
  if (horiz) c.x = next; else c.y = next;
  c.a = DIRA[c.dir];
  const ax = c.x + fx * T, ay = c.y + fy * T;
  if (ax < 0 || ay < 0 || ax > W || ay > W) {
    if (c.dir === 0) c.y -= T; else if (c.dir === 2) c.y += T; else if (c.dir === 1) c.x += T; else c.x -= T;
    c.dir = (c.dir + 2) % 4; c.a = DIRA[c.dir]; c.lock = -1;
  }
}
// ---------- IA police ----------
function updPolice(c, dt) {
  const tx = P.car ? P.car.x : P.x, ty = P.car ? P.car.y : P.y;
  const d = dist(c.x, c.y, tx, ty);
  if (c.ai === 'leave') { drive(c, dt, 0, 0, true); return; }
  if (d > 1500) { const p = lanePoint(650, 1050, tx, ty); if (p) { c.x = p.x; c.y = p.y; c.a = Math.atan2(ty - p.y, tx - p.x); if (carHits(c.x, c.y, c.a)) c.a = DIRA[p.d]; c.v = 120; } return; }
  chaseDrive(c, dt, tx, ty, d);
}
// intersections du quadrillage routier : la police et les gangs roulent de carrefour en carrefour
const ixC = i => (i * B + 1) * T;
const ixI = v => clamp(Math.round((v / T - 1) / B), 0, 10);
function roadTarget(c, tx, ty, d) {
  if (d < 380 && los(c.x, c.y, tx, ty)) { c.wp = null; return [tx, ty]; }
  const ci = ixI(c.x), cj = ixI(c.y), cx = ixC(ci), cy = ixC(cj);
  if (!c.wp) c.wp = dist(c.x, c.y, cx, cy) > 70 ? { i: ci, j: cj } : null;
  if (!c.wp || dist(c.x, c.y, ixC(c.wp.i), ixC(c.wp.j)) < 70) {
    const from = c.wp || { i: ci, j: cj };
    const cand = [[1, 0], [-1, 0], [0, 1], [0, -1]].map(([a, b]) => ({ i: from.i + a, j: from.j + b })).filter(q => q.i >= 0 && q.j >= 0 && q.i <= 10 && q.j <= 10 && !(c.prev && q.i === c.prev.i && q.j === c.prev.j));
    cand.sort((p1, p2) => dist(ixC(p1.i), ixC(p1.j), tx, ty) - dist(ixC(p2.i), ixC(p2.j), tx, ty));
    c.prev = from; c.wp = cand[0] || from;
  }
  return [ixC(c.wp.i), ixC(c.wp.j)];
}
function chaseDrive(c, dt, tx, ty, d) {
  const [gx, gy] = roadTarget(c, tx, ty, d);
  const want = Math.atan2(gy - c.y, gx - c.x), diff = angDiff(want, c.a);
  let thr = d < 70 ? (P.car ? .6 : -.3) : 1, st = clamp(diff * 2.6, -1, 1);
  if (c.wp && Math.abs(diff) > .6 && Math.abs(c.v) > 260) thr = -.4;
  if (c.rev > 0) { c.rev -= dt; thr = -1; st = -st; }
  else if (Math.abs(c.v) < 30 && d > 90) { c.stuck += dt; if (c.stuck > .7) { c.rev = .7; c.stuck = 0; } } else c.stuck = 0;
  if (c.rev <= 0 && Math.abs(diff) > 2.2 && d > 90) thr = .45;
  if (c.rev > 0 && c.wp) c.wp = null;
  drive(c, dt, thr, st, false);
}

// ---------- voitures de gang ----------
function spawnGangCar(cx, cy, f, group) {
  const p = lanePoint(150, 650, cx, cy); if (!p) return null;
  const c = mkCar(p.x, p.y, DIRA[p.d], 'gang'); c.ai = 'gang'; c.color = f.color; c.gang = f; c.group = group; c.keep = true; c.hp = 120 + lvl() * 8; c.cd = 1.5; c.active = false;
  cars.push(c); return c;
}
function updGang(c, dt) {
  const tx = P.car ? P.car.x : P.x, ty = P.car ? P.car.y : P.y, d = dist(c.x, c.y, tx, ty);
  if (!c.active) { if (d < 650) c.active = true; else { drive(c, dt, 0, 0, true); return; } }
  chaseDrive(c, dt, tx, ty, d);
  c.cd -= dt;
  if (c.cd <= 0 && d < 330 && los(c.x, c.y, tx, ty)) {
    const a = Math.atan2(ty - c.y, tx - c.x) + rnd(-.18, .18), dmg = 4 + lvl() * .3;
    bullets.push({ x: c.x + Math.cos(a) * 24, y: c.y + Math.sin(a) * 24, vx: Math.cos(a) * 560, vy: Math.sin(a) * 560, life: .8, dmg, from: 'enemy' });
    { const [pn, vl] = spatial(c.x, c.y); au('shot', 'enemy', pn, vl * .8); }
    c.cd = Math.max(.45, 1 - lvl() * .015) * rnd(.7, 1.3);
  }
}
// ---------- hélicoptère de police (4 étoiles et plus) ----------
let heli = null;
function updHeli(dt) {
  S.heliCd = (S.heliCd || 0) - dt;
  if (!heli && stars() >= 4 && S.heliCd <= 0) { const a = rnd(TAU); heli = { x: P.x + Math.cos(a) * 1000, y: P.y + Math.sin(a) * 1000, a: 0, hp: 300 + lvl() * 10, max: 300 + lvl() * 10, cd: 2, t: rnd(6), leave: 0 }; toast('Hélicoptère de police !'); }
  if (!heli) return;
  const h = heli; h.t += dt;
  if (stars() < 4) h.leave += dt;
  if (h.leave > 5 || dist(h.x, h.y, P.x, P.y) > 2600) { heli = null; return; }
  const tx = h.leave ? h.x + Math.cos(h.a) * 400 : P.x + Math.cos(h.t * .6) * 170, ty = h.leave ? h.y + Math.sin(h.a) * 400 : P.y + Math.sin(h.t * .6) * 170;
  const want = Math.atan2(ty - h.y, tx - h.x); h.a += angDiff(want, h.a) * Math.min(1, dt * 2);
  const sp = Math.min(320, dist(h.x, h.y, tx, ty) * 1.5); h.x += Math.cos(h.a) * sp * dt; h.y += Math.sin(h.a) * sp * dt;
  h.cd -= dt;
  if (!h.leave && h.cd <= 0 && dist(h.x, h.y, P.x, P.y) < 420) {
    for (let k = 0; k < 3; k++) { const a = Math.atan2(P.y - h.y, P.x - h.x) + rnd(-.15, .15); bullets.push({ x: h.x, y: h.y, vx: Math.cos(a) * 600, vy: Math.sin(a) * 600, life: .9, dmg: 3 + lvl() * .2, from: 'enemy', air: true }); }
    au('shot', 'uzi', 0, .7); h.cd = Math.max(1, 2.2 - lvl() * .03);
  }
}
function hitHeli(dmg) {
  if (!heli) return; heli.hp -= dmg; sparks(heli.x, heli.y, 3);
  if (heli.hp <= 0) { explosionAt(heli.x, heli.y, 110, 50, true); track('explosions'); addHeat(1); toast('Hélicoptère abattu !'); heli = null; S.heliCd = 25; }
}
// ---------- barrages routiers (3 étoiles et plus) ----------
function updRoadblocks(dt) {
  S.blockCd = (S.blockCd || 15) - dt;
  if (S.blockCd > 0 || stars() < 3 || !P.car || Math.abs(P.car.v) < 200) return;
  S.blockCd = 22;
  const a = P.car.a; let ax = 0, ay = 0, found = false;
  for (let dd = 500; dd <= 850 && !found; dd += 50) { ax = P.car.x + Math.cos(a) * dd; ay = P.car.y + Math.sin(a) * dd; if (tileAt(ax, ay) === ROAD) found = true; }
  if (!found) { S.blockCd = 4; return; }
  const tx = Math.floor(ax / T), ty = Math.floor(ay / T);
  const horiz = Math.abs(Math.cos(a)) > Math.abs(Math.sin(a));
  const base = horiz ? { x: (tx + .5) * T, y: ixC(ixI(ay)) } : { x: ixC(ixI(ax)), y: (ty + .5) * T };
  for (const off of [-32, 32]) {
    const x = base.x + (horiz ? 0 : off), y = base.y + (horiz ? off : 0);
    const c = mkCar(x, y, horiz ? PI / 2 : 0, 'police'); if (carHits(c.x, c.y, c.a)) continue;
    c.ai = 'block'; c.ttl = 40; cars.push(c);
  }
  msg('Barrage de police devant !');
}

// ---------- piétons ----------
function koPed(p, byPlayer) {
  if (p.state === 'ko') return;
  p.state = 'ko'; p.ko = 9; { const [pn, vl] = spatial(p.x, p.y); if (vl > .2) au('ko', pn); }
  for (let i = 0; i < 6; i++) parts.push({ x: p.x, y: p.y, vx: rnd(-90, 90), vy: rnd(-90, 90), life: .5, max: .5, r: 3, col: '#fff2a8' });
  if (p.cash) picks.push({ x: p.x + rnd(-8, 8), y: p.y + rnd(-8, 8), amt: p.cash, t: 30 });
  if (byPlayer) { addHeat(.6); if (L) L.kos = (L.kos || 0) + 1; }
  panic(p.x, p.y, 320);
}
function panic(x, y, r) {
  for (const q of peds) if (q.state === 'walk' && dist(q.x, q.y, x, y) < r) { q.state = 'flee'; q.t = rnd(4, 7); }
  for (const c of cars) if (c.ai === 'traffic' && dist(c.x, c.y, x, y) < r) c.panic = 4;
}
function updPed(p, dt) {
  if (p.state === 'ko') { p.ko -= dt; return; }
  p.t -= dt;
  let sp = 38;
  if (p.state === 'flee') { sp = 150; p.a = Math.atan2(p.y - P.y, p.x - P.x) + Math.sin(S.time * 3 + p.step) * .6; if (p.t < 0) { p.state = 'walk'; p.t = 2; } }
  else if (p.t < 0) { p.a = pick(DIRA) + rnd(-.3, .3); p.t = rnd(2, 6); }
  const nx = p.x + Math.cos(p.a) * sp * dt, ny = p.y + Math.sin(p.a) * sp * dt;
  const t = tileAt(nx + Math.cos(p.a) * 6, ny + Math.sin(p.a) * 6);
  if (solidT(t) || (p.state === 'walk' && t === ROAD)) { p.a += PI / 2 * (Math.random() < .5 ? 1 : -1); p.t = rnd(1, 3); }
  else { p.x = nx; p.y = ny; p.step += dt * sp * .25; }
}

// ---------- ennemis ----------
function mkEnemy(x, y, faction, boss, group) {
  const n = lvl();
  const hp = (boss ? 380 + n * 55 : 38 + n * 5) * (.6 + .4 * ez());
  return { role: !boss && Math.random() < .3 ? 'flank' : 'cover', mode: 'move', modeT: rnd(1, 2), look: faction.look || null, x, y, a: rnd(TAU), hp, max: hp, color: faction.color, boss: boss || null, group, alert: false, cd: rnd(1, 2), strafe: Math.random() < .5 ? 1 : -1, step: 0, st: rnd(2) };
}
function hitEnemy(e, dmg) {
  if (e.hp <= 0) return;
  e.hp -= dmg; e.alert = true; e.hitT = S.time; au('hit', spatial(e.x, e.y)[0]);
  for (let i = 0; i < 4; i++) parts.push({ x: e.x, y: e.y, vx: rnd(-80, 80), vy: rnd(-80, 80), life: .3, max: .3, r: 2.5, col: '#ff4d5e' });
  if (e.hp <= 0) {
    track('kills');
    for (const o of enemies) if (o.group === e.group && dist(o.x, o.y, e.x, e.y) < 600) o.alert = true;
    if (Math.random() < .5) picks.push({ x: e.x, y: e.y, amt: (20 + lvl() * 8 + rnd(30)) | 0, t: 30 });
    else if (Math.random() < .55) picks.push({ x: e.x + 6, y: e.y, ammo: true, t: 30 });
    if (e.boss) { toast(e.boss + ' est tombé !'); for (let i = 0; i < 3; i++) picks.push({ x: e.x + rnd(-20, 20), y: e.y + rnd(-20, 20), amt: 200 + lvl() * 40, t: 40 }); }
  }
}
function findCover(e, tx, ty) {
  let best = null, bd = 1e9;
  for (let k = 0; k < 12; k++) { const a = k / 12 * TAU, r = 60 + (k % 3) * 45, x = e.x + Math.cos(a) * r, y = e.y + Math.sin(a) * r;
    if (solid(x, y) || solid(x + 10, y) || solid(x - 10, y) || solid(x, y + 10) || solid(x, y - 10)) continue;
    const dt2 = dist(x, y, tx, ty); if (dt2 < 140 || dt2 > 480 || los(x, y, tx, ty)) continue;
    const dd = dist(x, y, e.x, e.y); if (dd < bd) { bd = dd; best = { x, y }; } }
  return best;
}
const grenades = [];
function throwGrenade(e, tx, ty) {
  const ox = tx + rnd(-40, 40), oy = ty + rnd(-40, 40), t = 1.5;
  grenades.push({ x: e.x, y: e.y, sx: e.x, sy: e.y, tx: ox, ty: oy, t: 0, dur: t }); e.firedT = S.time;
}
function updGrenades(dt) {
  for (const g of grenades) { g.t += dt; const k = Math.min(1, g.t / (g.dur * .7)); g.x = g.sx + (g.tx - g.sx) * k; g.y = g.sy + (g.ty - g.sy) * k; g.h = Math.sin(k * PI) * 60;
    if (g.t >= g.dur) { g.done = true; explosionAt(g.x, g.y, 85, 18 + lvl() * .8 * ez(), false); } }
  for (let i = grenades.length - 1; i >= 0; i--) if (grenades[i].done) grenades.splice(i, 1);
}
function updEnemy(e, dt) {
  if (e.hp <= 0) return;
  const n = lvl();
  let tx = P.x, ty = P.y;
  if (vip && vip.hp > 0 && !vip.inCar && dist(e.x, e.y, vip.x, vip.y) < dist(e.x, e.y, P.x, P.y) * .8) { tx = vip.x; ty = vip.y; }
  const d = dist(e.x, e.y, tx, ty);
  if (!e.alert && d < 300 + 160 * ez() && los(e.x, e.y, tx, ty)) e.alert = true;
  if (!e.alert) { e.st -= dt; if (e.st < 0) { e.a = rnd(TAU); e.st = rnd(1, 3); } moveBody(e, Math.cos(e.a) * 25 * dt, Math.sin(e.a) * 25 * dt); return; }
  e.a = Math.atan2(ty - e.y, tx - e.x);
  const sp = (e.boss ? 70 : 95) + n * 1.5;
  let mx = 0, my = 0;
  e.modeT -= dt; if (e.hitT && S.time - e.hitT < .05 && e.role === 'cover' && e.mode !== 'cover') e.modeT = 0;
  // tactique : se mettre à couvert, sortir pour tirer, ou contourner le joueur
  if (e.role === 'cover' && n >= 2) {
    if (e.modeT <= 0) {
      if (e.mode === 'cover') { e.mode = 'peek'; e.modeT = rnd(1.2, 2); e.goal = null; }
      else { e.mode = 'cover'; e.modeT = rnd(1.3, 2.2); e.goal = findCover(e, tx, ty); }
    }
    if (e.mode === 'cover' && e.goal) { const gd = dist(e.x, e.y, e.goal.x, e.goal.y); if (gd > 8) { mx = (e.goal.x - e.x) / gd; my = (e.goal.y - e.y) / gd; } }
    else { if (d > 260) { mx = Math.cos(e.a); my = Math.sin(e.a); } else if (d < 120) { mx = -Math.cos(e.a); my = -Math.sin(e.a); } mx += -Math.sin(e.a) * e.strafe * .5; my += Math.cos(e.a) * e.strafe * .5; }
  } else if (e.role === 'flank') {
    const ang = Math.atan2(e.y - ty, e.x - tx) + e.strafe * .9 * dt * 2, rad = 210, gx = tx + Math.cos(ang) * rad, gy = ty + Math.sin(ang) * rad, gd = dist(e.x, e.y, gx, gy);
    if (gd > 6) { mx = (gx - e.x) / gd; my = (gy - e.y) / gd; }
  } else {
    if (d > 230) { mx = Math.cos(e.a); my = Math.sin(e.a); } else if (d < 120) { mx = -Math.cos(e.a); my = -Math.sin(e.a); }
    mx += -Math.sin(e.a) * e.strafe * .6; my += Math.cos(e.a) * e.strafe * .6;
  }
  if (Math.random() < dt * .4) e.strafe *= -1;
  moveBody(e, mx * sp * dt, my * sp * dt); if (mx || my) e.step += sp * dt * .25;
  // grenades à partir du niveau 8
  if (n >= 8 && !e.boss && d > 150 && d < 380 && Math.random() < dt * (.03 + n * .002) && los(e.x, e.y, tx, ty)) throwGrenade(e, tx, ty);
  e.cd -= dt;
  if (e.cd <= 0 && d < 520 && shootersNow < 4 && los(e.x, e.y, tx, ty)) {
    shootersNow++; e.firedT = S.time;
    const spread = Math.max(.05, .32 - n * .009) + (1 - ez()) * .35, a = e.a + rnd(-spread, spread);
    const dmg = (4 + n * .35) * (e.boss ? 1.4 : 1) * (1 - .15 * assist()) * ez();
    const shots = e.boss && n >= 15 ? 3 : 1;
    { const [pn, vl] = spatial(e.x, e.y); if (vl > .05) au('shot', 'enemy', pn, vl * .8); }
    for (let k = 0; k < shots; k++) { const aa = a + (k - (shots - 1) / 2) * .12; bullets.push({ x: e.x + Math.cos(aa) * 12, y: e.y + Math.sin(aa) * 12, vx: Math.cos(aa) * 560, vy: Math.sin(aa) * 560, life: 1, dmg, from: 'enemy' }); }
    e.cd = Math.max(.8, 2.4 - n * .04) * rnd(.75, 1.35) * (e.boss ? .6 : 1) / ez();
  }
}
function movePlayer(vx, vy) {
  if (save.ghost === false) return moveBody(P, vx, vy);
  const ok = (x, y) => { const t = tileAt(x, y); return t !== WATER && x > 6 && y > 6 && x < W - 6 && y < W - 6; };
  if (ok(P.x + vx, P.y)) P.x += vx; if (ok(P.x, P.y + vy)) P.y += vy;
}
function moveBody(o, vx, vy) { if (!solid(o.x + vx + Math.sign(vx) * 8, o.y)) o.x += vx; if (!solid(o.x, o.y + vy + Math.sign(vy) * 8)) o.y += vy; }

// ---------- joueur ----------
function hurt(n) {
  if (S.dead > 0 || S.mode !== 'play') return;
  if (P.armor > 0) { const a = Math.min(P.armor, n * .7); P.armor -= a; n -= a; }
  S.hp -= n; P.hitT = S.time; shake = Math.max(shake, 5); if (n > 2 && (S.hurtSnd || 0) < S.time) { au('hurt'); vib(Math.min(140, 30 + n * 4)); S.hurtSnd = S.time + .35; }
  if (S.hp <= 0) { S.hp = 0; failLevel('Tu as été mis K.O.'); }
}
function hurtVip(n) { if (!vip || vip.hp <= 0) return; vip.hp -= n; if (vip.hp <= 0) { vip.hp = 0; failLevel(vip.name + ' n’a pas survécu'); } }
function addHeat(n) { S.heat = Math.min(5.99, S.heat + n); if (S.heat < 1) S.heat = 1; S.unseen = 0; }
function policeLeave() { for (const c of cars) if (c.kind === 'police' && c.ai === 'police') c.ai = 'leave'; }
function bribeCost() { return Math.round(stars() * (250 + lvl() * 120) * bribeDiscount() / 10) * 10; }
function nearCop() { const tx = P.x, ty = P.y; return cars.some(c => c.kind === 'police' && c.ai === 'police' && !c.wreck && dist(c.x, c.y, tx, ty) < 170); }
function bribePolice() {
  if (S.mode !== 'play' || stars() < 1) return;
  if (!nearCop()) { msg('Approche-toi d’une voiture de police pour la soudoyer'); return; }
  const c = bribeCost();
  if (save.money < c) { msg('Il te faut ' + fmt(c) + ' pour soudoyer les agents'); return; }
  au('cash'); save.money -= c; S.heat = 0; S.unseen = 0; policeLeave(); track('bribes'); toast('Agents soudoyés (−' + fmt(c) + ')');
}
function contextAction() {
  if (S.mode !== 'play' || S.dead > 0) return;
  // agent corrompu
  if (agent && !agent.paid && dist(P.x, P.y, agent.x, agent.y) < 60) { payAgent(); return; }
  const t = tileAt(P.x, P.y);
  if (t === TUNNEL && S.tunnelCd <= 0) { takeTunnel(); return; }
  if (!P.car && t === SHOP) { openShop(true); return; }
  toggleCar();
}
function payAgent() {
  const c = agent.cost;
  au('cash');
  if (save.money >= c) { save.money -= c; toast('L’agent empoche ' + fmt(c) + ' et te donne le tuyau'); }
  else { toast('Pas assez d’argent : l’agent prend ' + fmt(save.money) + ' et te balance !'); save.money = 0; addHeat(2); }
  agent.paid = true; if (L) L.bribed = true;
}
function takeTunnel() {
  const here = world.tunnels.find(u => dist(u.x, u.y, P.x, P.y) < 48);
  if (!here) return;
  S.tunnelCd = 3; fade('Tunnel souterrain…'); au('whoosh');
  setTimeout(() => {
    const to = here.to;
    if (P.car) { const c = P.car; c.x = to.x; c.y = to.y; c.v = 0; for (const a of DIRA) if (!carHits(to.x, to.y, a)) { c.a = a; break; } P.x = c.x; P.y = c.y; }
    else { P.x = to.x; P.y = to.y + 4; }
    if (vip && vip.hp > 0 && (vip.inCar || vip.following)) { vip.x = to.x + 20; vip.y = to.y; }
    cam.x = P.x; cam.y = P.y;
    if (S.heat >= 1) { S.heat = Math.max(0, stars() - 1); if (S.heat < 1) { S.heat = 0; policeLeave(); track('escapes'); } for (const c of cars) if (c.kind === 'police') { c.x += 2000 * Math.sign(c.x - P.x || 1); } }
    if (L) L.tunneled = true; track('tunnels');
    toast('Sortie du tunnel');
  }, 700);
}
function toggleCar() {
  if (P.car) {
    const c = P.car, px = -Math.sin(c.a), py = Math.cos(c.a);
    const opts = [[px * -30, py * -30], [px * 30, py * 30], [-Math.cos(c.a) * 36, -Math.sin(c.a) * 36], [Math.cos(c.a) * 36, Math.sin(c.a) * 36]];
    for (const [ox, oy] of opts) { if (!solid(c.x + ox, c.y + oy)) { P.x = c.x + ox; P.y = c.y + oy; break; } }
    c.ai = null; P.car = null; au('door'); radioOff();
    if (vip && vip.inCar === c) { vip.inCar = null; vip.x = c.x - (P.x - c.x); vip.y = c.y - (P.y - c.y); if (solid(vip.x, vip.y)) { vip.x = P.x + 12; vip.y = P.y; } }
    return;
  }
  let best = null, bd = 48;
  for (const c of cars) { if (c.wreck) continue; const d = dist(c.x, c.y, P.x, P.y) - (c.mark && !c.convoy ? 30 : 0); if (d < bd) { bd = d; best = c; } }
  if (!best) { msg('Aucune voiture à portée'); return; }
  if (best.ai === 'traffic' || best.ai === 'convoy') { const d = mkPed(best.x - Math.sin(best.a) * 24, best.y + Math.cos(best.a) * 24); d.state = 'flee'; d.t = 6; peds.push(d); if (Math.random() < .3) addHeat(.4); }
  if (best.kind === 'police') { S.heat = Math.max(S.heat, 2); S.unseen = 0; toast('Voiture de police volée !'); }
  if (best !== P.lastCar) track('carsStolen'); P.lastCar = best;
  best.ai = null; best.v = Math.min(best.v, 40); P.car = best; au('door'); radioOn();
}
function startReload() {
  const w = wepDef(save.weapon), am = P.ammo && P.ammo[w.id];
  if (!w.mag || !am || P.reload > 0 || am.mag >= w.mag) return;
  if (am.res <= 0) { msg('Plus de munitions : ramasse des caisses ou change d\u2019arme'); au('deny'); return; }
  P.reload = w.reload; P.reloadW = w.id; au('click'); msg('Rechargement…');
}
function finishReload() {
  const w = wepDef(P.reloadW), am = P.ammo[w.id]; if (!am) return;
  const take = Math.min(w.mag - am.mag, am.res); am.mag += take; if (am.res !== Infinity) am.res -= take;
  au('door');
}
function melee() {
  let best = null, bd = 42, kind = null;
  for (const e of enemies) { if (e.hp <= 0) continue; const d = dist(P.x, P.y, e.x, e.y); if (d < bd && Math.abs(angDiff(Math.atan2(e.y - P.y, e.x - P.x), P.a)) < 1.2) { bd = d; best = e; kind = 'e'; } }
  for (const q of peds) { if (q.state === 'ko') continue; const d = dist(P.x, P.y, q.x, q.y); if (d < bd && Math.abs(angDiff(Math.atan2(q.y - P.y, q.x - P.x), P.a)) < 1.2) { bd = d; best = q; kind = 'p'; } }
  P.cd = wepDef('fists').rate; P.punch = .25; P.lastShot = S.time;
  if (!best) { au('click'); return; }
  P.a = Math.atan2(best.y - P.y, best.x - P.x);
  if (kind === 'e') { hitEnemy(best, wepDef('fists').dmg); best.x += Math.cos(P.a) * 10; best.y += Math.sin(P.a) * 10; } else koPed(best, true);
  au('hit', 0); vib(25); sparks(best.x, best.y, 4);
}
function fire() {
  const w = wepDef(save.weapon);
  if (w.melee) { melee(); return; }
  const am = P.ammo && P.ammo[w.id];
  if (P.reload > 0) return;
  if (am && am.mag <= 0) { startReload(); if (am.res <= 0) { const alt = D.WEAPONS.find(x => save.owned[x.id] && x.id === 'pistol'); if (alt) save.weapon = 'pistol'; } return; }
  if (am) { am.mag--; if (am.mag <= 0 && am.res > 0) setTimeout(startReload, 150); }
  let a = P.a;
  if (P.lock && lockAlive(P.lock)) { a = Math.atan2(P.lock.y - P.y, P.lock.x - P.x); P.a = a; }
  else if (touch.aiming) { a = touch.aimA; P.a = a; }
  else if (mouse.aim > 0) { a = Math.atan2(mouse.wy - P.y, mouse.wx - P.x); P.a = a; }
  if (!touch.aiming && mouse.aim <= 0 && (!touch.on || touch.autoAim)) { // visée auto vers l'ennemi le plus proche devant
    let best = null, bd = 520;
    for (const e of enemies) { if (e.hp <= 0) continue; const d = dist(P.x, P.y, e.x, e.y); if (d < bd && Math.abs(angDiff(Math.atan2(e.y - P.y, e.x - P.x), P.a)) < (touch.on ? 1.9 : .9) && los(P.x, P.y, e.x, e.y)) { bd = d; best = e; } }
    if (best) a = Math.atan2(best.y - P.y, best.x - P.x);
  }
  for (let k = 0; k < w.pellets; k++) {
    const aa = a + rnd(-w.spread, w.spread);
    bullets.push({ x: P.x + Math.cos(aa) * 12, y: P.y + Math.sin(aa) * 12, vx: Math.cos(aa) * w.speed, vy: Math.sin(aa) * w.speed, life: w.life, dmg: w.dmg, from: 'player', explosive: w.explosive });
  }
  parts.push({ x: P.x + Math.cos(a) * 14, y: P.y + Math.sin(a) * 14, vx: 0, vy: 0, life: .06, max: .06, r: w.explosive ? 10 : 7, col: '#fff2a8' });
  P.cd = w.rate; P.lastShot = S.time; S.flash = { x: P.x + Math.cos(a) * 18, y: P.y + Math.sin(a) * 18, i: w.explosive ? 3 : 1.6 }; panic(P.x, P.y, 380); au('shot', w.id, 0, 1); if (touch.on) vib({ shotgun: 35, sniper: 50, rocket: 70, rifle: 12, minigun: 6, uzi: 6 }[w.id] || 10);
}
// radio de voiture : stations originales générées par le jeu
const STATIONS = [['Néon FM', 'synth'], ['808 City', 'trap'], ['Calle 95', 'dembow'], ['Baile Azul', 'funk'], ['Lo-fi Nuit', 'lofi'], ['Radio coupée', null]];
const REGION_RADIO = { usa: 1, ita: 0, col: 2, bra: 3 };
function radioOn() { if (save.radio === undefined) save.radio = REGION_RADIO[world.region.id] || 0; const st = STATIONS[save.radio]; au('setMusic', st[1] || '__none'); msg('Radio : ' + st[0]); }
function radioNext() { if (!P.car) return; save.radio = ((save.radio || 0) + 1) % STATIONS.length; persist(); radioOn(); }
function radioOff() { au('setMusic', world.region.id); }
// ---------- verrouillage de cible (façon avion de chasse) ----------
const lockAlive = t => t && (t.hp === undefined ? !t.wreck : t.hp > 0) && dist(t.x, t.y, P.x, P.y) < 700 && (t !== heli || heli);
function lockCandidates() {
  const list = [];
  for (const e of enemies) if (e.hp > 0 && dist(e.x, e.y, P.x, P.y) < 620) list.push(e);
  for (const c of cars) if (!c.wreck && (c.ai === 'gang' || c.convoy) && dist(c.x, c.y, P.x, P.y) < 620) list.push(c);
  if (heli && dist(heli.x, heli.y, P.x, P.y) < 650) list.push(heli);
  return list.sort((p1, p2) => dist(p1.x, p1.y, P.x, P.y) - dist(p2.x, p2.y, P.x, P.y));
}
function lockNext() {
  if (S.mode !== 'play') return;
  const list = lockCandidates();
  if (!list.length) { P.lock = null; msg('Aucune cible à portée'); au('deny'); return; }
  const i = P.lock ? list.indexOf(P.lock) : -1;
  P.lock = list[(i + 1) % list.length]; P.lockT = S.time;
  au('lock'); vib([15, 30, 15]); msg('Cible verrouillée');
}
function updLock() {
  if (P.lock && !lockAlive(P.lock)) { const was = P.lock; P.lock = null; if (was.hp !== undefined ? was.hp <= 0 : was.wreck) { const nx = lockCandidates()[0]; if (nx) { P.lock = nx; P.lockT = S.time; au('lock'); } } }
}
const CAMS = [['top', 'Vue de dessus'], ['chase', 'Vue poursuite'], ['car', 'Caméra embarquée']];
function cycleCam() { const i = CAMS.findIndex(c => c[0] === (save.cam || 'top')); save.cam = CAMS[(i + 1) % CAMS.length][0]; persist(); toast(CAMS.find(c => c[0] === save.cam)[1]); }
const canVib = () => typeof navigator !== 'undefined' && 'vibrate' in navigator;
function vib(p) { if (save.vib === false || !canVib()) return; try { navigator.vibrate(p); } catch (e) {} }
function cycleWeapon(dir = 1) {
  const owned = D.WEAPONS.filter(w => save.owned[w.id]);
  const i = owned.findIndex(w => w.id === save.weapon);
  save.weapon = owned[(i + dir + owned.length) % owned.length].id;
  msg(wepDef(save.weapon).name);
}
function useMedkit() { if (S.mode !== 'play') return; if (save.medkits <= 0) { msg('Plus de trousse de soins (boutique)'); return; } if (S.hp >= 100) { msg('Santé déjà au maximum'); return; } save.medkits--; S.hp = Math.min(100, S.hp + 50); toast('+50 santé'); }
function useNitro() { if (S.mode !== 'play' || !P.car) return; if (P.nitro > 0) return; if (save.nitro <= 0) { msg('Plus de nitro (boutique)'); return; } save.nitro--; P.nitro = 2.5; }

// ---------- étapes de mission ----------
function faction(i) { const f = world.region.factions; return f[i % f.length]; }
function place() { return pick(world.region.places); }
function nearestOf(list) { let b = list[0], bd = 1e9; for (const p of list) { const d = dist(p.x, p.y, P.x, P.y); if (d < bd) { bd = d; b = p; } } return b; }
function spawnGroup(cx, cy, count, f, group, bossName) {
  for (let k = 0; k < count; k++) { const p = freeNear(cx, cy, 170); enemies.push(mkEnemy(p.x, p.y, f, null, group)); }
  if (bossName) { const p = freeNear(cx, cy, 60); const b = mkEnemy(p.x, p.y, f, bossName, group); enemies.push(b); return b; }
  return null;
}
function makeStep(type, n, idx) {
  const st = { type, label: D.STEP_LABEL[type], target: null, time: null, survive: false, desc: '' };
  const g = 'g' + idx;
  const f = faction(idx);
  switch (type) {
    case 'goto': { const pl = place(); st.target = randWalk(1100, 2100, P.x, P.y); st.desc = 'Rejoins ' + pl; st.check = () => dist(P.x, P.y, st.target.x, st.target.y) < 56; break; }
    case 'deliver': {
      const pl = place(); st.target = randWalk(1700, 3000, P.x, P.y); const d = dist(P.x, P.y, st.target.x, st.target.y);
      st.time = Math.round(d / (240 + n * 2) + 22 - n * .35); st.needCar = true;
      st.desc = 'Livre la marchandise à ' + pl + ' en voiture';
      st.check = () => P.car && dist(P.x, P.y, st.target.x, st.target.y) < 64; break;
    }
    case 'steal': {
      const p = randWalk(700, 1400, P.x, P.y); let c = parkedCar(p.x, p.y) || parkedCar(p.x + T, p.y);
      if (!c) { c = mkCar(p.x, p.y, 0, 'civ'); cars.push(c); }
      c.color = '#ffd700'; c.mark = true; c.hp = 130 + n * 5; c.keep = true; L.stolen = c; st.car = c;
      st.desc = 'Vole la voiture dorée'; st.dyn = () => st.car;
      st.check = () => P.car === st.car;
      st.fail = () => st.car.wreck ? 'La voiture dorée a été détruite' : null; break;
    }
    case 'garage': {
      st.target = nearestOf(world.garages); st.needCar = true; st.time = Math.round(dist(P.x, P.y, st.target.x, st.target.y) / 220 + 30);
      st.desc = 'Dépose la voiture au garage (G vert)';
      st.check = () => { if (!P.car || dist(P.x, P.y, st.target.x, st.target.y) > 60) return false; if (L.stolen && !L.stolen.wreck && P.car !== L.stolen) { msg('Ramène la voiture dorée'); return false; } if (P.car.mark) { P.car.mark = false; P.car.keep = false; } return true; }; break;
    }
    case 'buy': { st.target = nearestOf(world.shops); st.desc = 'Passe à la boutique (case verte) pour t\u2019équiper : E pour entrer'; L.bought = false; st.check = () => L.bought; break; }
    case 'collect': {
      const c = randWalk(900, 1900, P.x, P.y), count = Math.min(8, 3 + Math.floor(n / 6));
      st.items = []; for (let k = 0; k < count; k++) { const p = freeNear(c.x, c.y, 330); const it = { x: p.x, y: p.y, got: false }; cases.push(it); st.items.push(it); }
      const guards = n < 6 ? 0 : Math.floor(n / 4); if (guards) spawnGroup(c.x, c.y, guards, f, g);
      st.desc = () => 'Récupère les valises près de ' + st.pl + ' (' + st.items.filter(i => i.got).length + '/' + count + ')'; st.pl = place();
      st.dyn = () => { const r = st.items.filter(i => !i.got); return r.length ? nearestOf(r) : null; };
      st.check = () => st.items.every(i => i.got); break;
    }
    case 'elim': case 'boss': {
      const c = randWalk(1000, 1900, P.x, P.y);
      const count = Math.max(2, Math.round((type === 'boss' ? Math.min(10, 2 + Math.floor(n / 3)) : Math.min(14, 3 + Math.floor(n / 2.5))) * (.6 + .4 * ez())));
      const boss = spawnGroup(c.x, c.y, count, f, g, type === 'boss' ? (L.def.boss || 'le chef') : null);
      if (n >= 4) for (let k = 0; k < 1 + Math.floor(n / 12); k++) spawnGangCar(c.x, c.y, f, g);
      st.center = c; st.boss = boss;
      st.desc = () => type === 'boss' ? 'Élimine ' + boss.boss + ', chef de ' + f.name : 'Neutralise ' + f.name + ' (' + enemies.filter(e => e.group === g && e.hp > 0).length + ' restants)';
      st.dyn = () => { const al = enemies.filter(e => e.group === g && e.hp > 0); if (!al.length) return null; if (dist(P.x, P.y, c.x, c.y) > 500 && !al.some(e => e.alert)) return c; return type === 'boss' && boss.hp > 0 && dist(P.x, P.y, boss.x, boss.y) < 600 ? boss : nearestOf(al); };
      st.check = () => type === 'boss' ? boss.hp <= 0 : !enemies.some(e => e.group === g && e.hp > 0); break;
    }
    case 'escape': {
      S.heat = Math.max(S.heat, Math.min(5, (n < 4 ? 1 : 2) + Math.floor(n / 8))); S.unseen = 0; st.time = 150; st.grace = 2;
      st.desc = 'La police te traque : sème-la (tunnel, atelier de peinture ou pot-de-vin)';
      st.check = dt => { st.grace -= dt; return st.grace <= 0 && stars() === 0; }; break;
    }
    case 'survive': {
      S.heat = Math.max(S.heat, Math.min(5, (n < 6 ? 2 : 3) + Math.floor(n / 10))); S.unseen = 0; st.time = 30 + Math.round(n * 1.2); st.survive = true; st.lock = true;
      st.desc = 'Survis jusqu’à la fin du chrono'; st.check = () => false; break;
    }
    case 'tunnel': { L.tunneled = false; st.target = nearestOf(world.tunnels); st.desc = 'Prends le tunnel souterrain (E sur la bouche T)'; st.check = () => L.tunneled; break; }
    case 'bribe': {
      const p = randWalk(900, 1700, P.x, P.y); const cost = Math.round((200 + n * 180) * bribeDiscount() / 10) * 10;
      agent = { x: p.x, y: p.y, a: 0, cost, paid: false }; L.bribed = false; st.target = agent;
      st.desc = 'Va voir l’agent corrompu et donne-lui ' + fmt(cost) + ' (E)'; st.check = () => L.bribed; break;
    }
    case 'escort': {
      const p = randWalk(700, 1400, P.x, P.y); const name = world.region.vip;
      vip = { x: p.x, y: p.y, a: 0, hp: 100 + n * 5, max: 100 + n * 5, name: name.split(',')[0], full: name, following: false, inCar: null, step: 0 };
      st.phase = 0; st.dest = null;
      st.desc = () => st.phase === 0 ? 'Retrouve ' + vip.full : 'Emmène ' + vip.name + ' à ' + st.pl + ' en vie';
      st.pl = place();
      st.dyn = () => st.phase === 0 ? vip : st.dest;
      st.check = () => {
        if (st.phase === 0 && dist(P.x, P.y, vip.x, vip.y) < 70) {
          st.phase = 1; vip.following = true; st.dest = randWalk(1800, 2900, vip.x, vip.y);
          st.time = Math.round(dist(vip.x, vip.y, st.dest.x, st.dest.y) / 200 + 40);
          const mx = (vip.x + st.dest.x) / 2, my = (vip.y + st.dest.y) / 2; spawnGroup(mx, my, 2 + Math.floor(n / 5), f, g); if (n >= 6) spawnGangCar(mx, my, f, g);
          toast(vip.name + ' te suit'); return false;
        }
        const vx = vip.inCar ? vip.inCar.x : vip.x, vy = vip.inCar ? vip.inCar.y : vip.y;
        if (st.phase === 1 && dist(vx, vy, st.dest.x, st.dest.y) < 75) { vip.following = false; vip.done = true; return true; }
        return false;
      };
      break;
    }
    case 'destroy': {
      const count = 2 + Math.floor(n / 10); st.cars = [];
      for (let k = 0; k < count; k++) { const c = spawnTraffic() || (() => { const p = randWalk(900, 1500, P.x, P.y); const cc = mkCar(p.x, p.y, 0, 'civ'); cars.push(cc); return cc; })(); c.ai = c.ai ? 'convoy' : null; c.color = '#141018'; c.mark = true; c.keep = true; c.hp = 120 + n * 10; c.convoy = true; st.cars.push(c); }
      st.desc = () => 'Détruis le convoi de ' + f.name + ' (' + st.cars.filter(c => !c.wreck).length + ' restants)';
      st.dyn = () => { const r = st.cars.filter(c => !c.wreck); return r.length ? nearestOf(r) : null; };
      st.check = () => st.cars.every(c => c.wreck); break;
    }
    case 'race': {
      let x = P.x, y = P.y, tot = 0; st.pts = [];
      for (let k = 0; k < 4; k++) { const d = randWalk(800, 1400, x, y); tot += dist(x, y, d.x, d.y); st.pts.push(d); x = d.x; y = d.y; }
      st.k = 0; st.time = Math.round(tot / (250 + n * 2.5) + 16 - n * .3);
      st.desc = () => 'Course : passe les checkpoints (' + st.k + '/4)';
      st.dyn = () => st.pts[st.k];
      st.check = () => { if (dist(P.x, P.y, st.pts[st.k].x, st.pts[st.k].y) < 60) { st.k++; if (st.k < 4) msg('Checkpoint ' + st.k + '/4'); } return st.k >= 4; }; break;
    }
  }
  return st;
}
const stepDesc = st => typeof st.desc === 'function' ? st.desc() : st.desc;
const stepTarget = st => st.dyn ? st.dyn() : st.target;
const stepReward = n => 100 + n * 60;
const levelBonus = n => 1000 + n * 800;

// ---------- niveaux ----------
function regionOf(n) { return D.REGIONS.find(r => n >= r.from && n <= r.to); }
function canPlay(n) { return n <= save.maxLevel && (n === 1 || save.premium || !!PORTAL); }
function startLevel(n) {
  const region = regionOf(n); au('init'); au('setMusic', region.id); au('setIntensity', 0);
  if (!world || world.region !== region) world = buildWorld(region);
  cars = []; peds = []; bullets = []; parts = []; picks = []; enemies = []; cases = []; vip = null; agent = null;
  S.heat = 0; S.unseen = 0; S.bust = 0; S.hp = 100; S.dead = 0; S.tunnelCd = 0; S.spawnPol = 0;
  P.car = null; P.x = world.hospital.x; P.y = world.hospital.y + 20; P.a = PI / 2; P.armor = armorMax(); P.nitro = 0; P.cd = 0;
  if (!save.owned[save.weapon]) save.weapon = 'pistol';
  grenades.length = 0; skids.length = 0; skidI = 0;
  P.ammo = {}; for (const w0 of D.WEAPONS) if (w0.mag) { const w = wepDef(w0.id); P.ammo[w.id] = { mag: w.mag, res: w.reserve }; } P.reload = 0;
  heli = null; S.heliCd = 0; S.blockCd = 15;
  cam.x = P.x; cam.y = P.y;
  for (let i = 0; i < 90; i++) { const t = randWalk(0, W * 2, 0, 0); parkedCar(t.x, t.y); }
  for (let k = 0; k < 3; k++) { const p = freeNear(P.x + 60, P.y + 40, 80); parkedCar(p.x, p.y); }
  for (let i = 0; i < 25; i++) spawnPed();
  for (let i = 0; i < 14; i++) spawnTraffic();
  L = { n, def: D.LEVELS[n - 1], region, idx: -1, earned: 0, time: 0, step: null, kos: 0 };
  S.tod = ((n * .23) % 1) * .6 + .7; if (S.tod > 1) S.tod -= 1;
  S.rain = n > 1 && Math.random() < (['col', 'bra'].includes(region.id) ? .4 : .25);
  save.seenIntro = save.seenIntro || {}; const firstIntro = !save.seenIntro[n]; save.seenIntro[n] = 1;
  S.cine = { type: 'intro', t: 0, dur: firstIntro ? 7 : 3 }; showCine('Niveau ' + n + ' · ' + region.name, L.def.t, firstIntro ? L.def.s : '');
  if (S.rain) setTimeout(() => msg('Il pleut : la route glisse'), 3600);
  ensureDaily();
  if (n === 1) { const c = nearestFreeCar(); if (c) { setTimeout(() => { if (P.car) radioOn(); }, 3600); c.color = '#ff2e93'; P.car = c; c.ai = null; P.x = c.x; P.y = c.y; S.heat = 1.2; S.unseen = 0; S.spawnPol = 0; setTimeout(() => { if (L && L.n === 1) spawnPolice(); }, 400); } }
  try { if (touch.on && screen.orientation && screen.orientation.lock && (document.fullscreenElement || document.webkitFullscreenElement)) screen.orientation.lock('landscape').catch(() => {}); } catch (e) {}
  S.mode = 'play'; showScreen(null); S.levelsStarted = (S.levelsStarted || 0) + 1; if (PORTAL) PORTAL.start();
  nextStep();
}
function nearestFreeCar() { let b = null, bd = 400; for (const c of cars) { if (c.wreck || c.ai) continue; const d = dist(c.x, c.y, P.x, P.y); if (d < bd) { bd = d; b = c; } } return b; }
function nextStep() {
  if (L.step) { if (L.idx < 9) { au('step'); vib([30, 50, 30]); } const r = stepReward(L.n); save.money += r; L.earned += r; if (L.idx >= 0) toast('Étape ' + (L.idx + 1) + '/10 réussie · +' + fmt(r)); }
  L.idx++;
  if (L.idx >= 10) { completeLevel(); return; }
  if (agent && agent.paid) agent = null;
  if (vip && (vip.done || vip.hp <= 0)) vip = null;
  L.step = makeStep(L.def.steps[L.idx], L.n, L.idx);
  persist();
}
function updLevel(dt) {
  const st = L.step; if (!st) return;
  L.time += dt;
  if (st.time !== null && !st.assisted) { st.assisted = true; if (!st.survive) st.time = Math.round(st.time * (1 + .2 * assist()) * (2 - ez())); else st.time = Math.round(st.time * (.6 + .4 * ez())); }
  if (st.time !== null) {
    st.time -= dt;
    if (st.time <= 0) { if (st.survive) { nextStep(); return; } failLevel('Temps écoulé'); return; }
  }
  if (st.fail) { const r = st.fail(); if (r) { failLevel(r); return; } }
  if (st.needCar && !P.car && st.target && dist(P.x, P.y, st.target.x, st.target.y) < 70) msg('Il faut arriver en voiture');
  if (st.type === 'boss' && st.boss && !st.introDone && st.boss.hp > 0 && dist(P.x, P.y, st.boss.x, st.boss.y) < 480) { st.introDone = true; S.cine = { type: 'boss', t: 0, dur: 2.6, focus: st.boss }; showCine('Chef de gang', st.boss.boss.toUpperCase()); au('boom', 0, .4); }
  if (st.check(dt)) nextStep();
}
function completeLevel() {
  const n = L.n, bonus = levelBonus(n);
  save.money += bonus; L.earned += bonus; au('win'); vib([60, 40, 60, 40, 160]); au('setMusic', 'menu');
  const first = !save.done[n]; if (save.fails) delete save.fails[n];
  const sc = levelStars(L); save.stars = save.stars || {}; const prevStars = save.stars[n] || 0; save.stars[n] = Math.max(prevStars, sc.stars);
  if (first) track('levelsDone'); track('levelsPlayed');
  if (sc.stars === 3 && prevStars < 3) track('threeStars');
  save.done[n] = true; save.maxLevel = Math.max(save.maxLevel, Math.min(30, n + 1)); persist();
  S.mode = 'result'; if (PORTAL) PORTAL.stop();
  const unlockW = D.WEAPONS.filter(w => w.lvl === n + 1).concat(D.GEAR.filter(g => g.lvl === n + 1));
  showScreen('result', { ok: true, n, earned: L.earned, bonus, time: L.time, first, unlocks: unlockW, sc, kos: L.kos || 0 });
}
function failLevel(reason) {
  if (S.mode !== 'play') return;
  save.fails = save.fails || {}; save.fails[L.n] = (save.fails[L.n] || 0) + 1;
  S.mode = 'result'; if (PORTAL) PORTAL.stop(); persist(); au('fail'); vib(300); au('setMusic', null);
  showBanner(reason.includes('K.O') ? 'K.O.' : reason.includes('Arrêté') ? 'ARRÊTÉ' : 'ÉCHEC');
  setTimeout(() => showScreen('result', { ok: false, n: L.n, reason, earned: L.earned }), 1100);
}

// ---------- progression : succès, défis du jour, conseils ----------
const ACH = [
  { id: 'steal10', name: 'Voleur de voitures', key: 'carsStolen', goal: 10, r: 500 },
  { id: 'steal100', name: 'Grand voleur', key: 'carsStolen', goal: 100, r: 3000 },
  { id: 'esc10', name: 'Fantôme', key: 'escapes', goal: 10, r: 1000 },
  { id: 'esc50', name: 'Insaisissable', key: 'escapes', goal: 50, r: 5000 },
  { id: 'kill50', name: 'Tireur', key: 'kills', goal: 50, r: 1000 },
  { id: 'kill500', name: 'Nettoyeur', key: 'kills', goal: 500, r: 8000 },
  { id: 'tun10', name: 'La taupe', key: 'tunnels', goal: 10, r: 800 },
  { id: 'bribe5', name: 'Bon payeur', key: 'bribes', goal: 5, r: 800 },
  { id: 'boom25', name: 'Artificier', key: 'explosions', goal: 25, r: 1500 },
  { id: 'cash5k', name: 'Les poches pleines', key: 'cashPicked', goal: 5000, r: 1000 },
  { id: 'tags12', name: 'Graffeur', key: 'tags', goal: 12, r: 2000 },
  { id: 'tags48', name: 'Chasseur de tags', key: 'tags', goal: 48, r: 10000 },
  { id: 'star5', name: 'Trois étoiles', key: 'threeStars', goal: 5, r: 2000 },
  { id: 'star30', name: 'Perfectionniste', key: 'threeStars', goal: 30, r: 20000 },
  { id: 'lvl8', name: 'Roi de Néon Bay', key: 'levelsDone', goal: 8, r: 3000 },
  { id: 'lvl16', name: 'Parrain de Porto Lumi', key: 'levelsDone', goal: 16, r: 6000 },
  { id: 'lvl23', name: 'Maître de Sierra Verde', key: 'levelsDone', goal: 23, r: 9000 },
  { id: 'lvl30', name: 'Légende de Morro Azul', key: 'levelsDone', goal: 30, r: 15000 },
];
const STAT_LABEL = { carsStolen: 'Vole {n} voitures', escapes: 'Sème la police {n} fois', kills: 'Neutralise {n} ennemis', tunnels: 'Prends {n} tunnels', bribes: 'Soudoie la police {n} fois', explosions: 'Fais exploser {n} véhicules', cashPicked: 'Ramasse {n} $ par terre', levelsDone: 'Termine {n} niveaux différents', levelsPlayed: 'Termine {n} niveau(x)', threeStars: 'Obtiens 3 étoiles sur {n} niveaux', tags: 'Trouve {n} tags secrets' };
const DAILY_POOL = [['escapes', 3], ['carsStolen', 5], ['kills', 20], ['tunnels', 2], ['cashPicked', 400], ['explosions', 4], ['levelsPlayed', 1], ['bribes', 1]];
const today = () => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
function ensureDaily() {
  const t = today();
  if (save.daily && save.daily.date === t) return save.daily;
  const prev = save.daily && save.daily.date;
  const y = new Date(Date.now() - 864e5), yd = y.getFullYear() + '-' + String(y.getMonth() + 1).padStart(2, '0') + '-' + String(y.getDate()).padStart(2, '0');
  save.streak = prev === yd && save.daily.items.every(i => i.done) ? (save.streak || 0) + 1 : (prev === t ? save.streak || 0 : 0);
  let h = 0; for (const c of t) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  const pool = DAILY_POOL.slice(), items = [];
  for (let k = 0; k < 3; k++) { const i = (h >>> (k * 5)) % pool.length; const [key, goal] = pool.splice(i, 1)[0]; items.push({ key, goal, prog: 0, done: false }); }
  save.daily = { date: t, items }; persist(); return save.daily;
}
const dailyReward = () => 600 + Math.min(10, save.streak || 0) * 100;
function track(key, n = 1) {
  save.stats = save.stats || {};
  save.stats[key] = (save.stats[key] || 0) + n;
  const d = ensureDaily();
  for (const it of d.items) if (it.key === key && !it.done) {
    it.prog = Math.min(it.goal, it.prog + n);
    if (it.prog >= it.goal) { it.done = true; const r = dailyReward(); save.money += r; reward('Défi du jour réussi', STAT_LABEL[key].replace('{n}', it.goal), r); }
  }
  save.ach = save.ach || {};
  for (const a of ACH) if (a.key === key && !save.ach[a.id] && save.stats[key] >= a.goal) { save.ach[a.id] = Date.now(); save.money += a.r; reward('Succès débloqué', a.name, a.r); }
}
let rewardQ = [];
function reward(title, name, r) { rewardQ.push({ title, name, r }); if (rewardQ.length === 1) showReward(); }
function showReward() {
  const it = rewardQ[0]; if (!it) return;
  const el = $('reward'); el.innerHTML = `<b>${esc(TR(it.title))}</b><span>${esc(TR(it.name))}</span><i>+${fmt(it.r)}</i>`; el.hidden = false; el.classList.remove('in'); void el.offsetWidth; el.classList.add('in');
  au('win'); vib([40, 30, 40]);
  setTimeout(() => { el.classList.remove('in'); setTimeout(() => { el.hidden = true; rewardQ.shift(); showReward(); }, 350); }, 2600);
}
// conseils affichés une seule fois, au bon moment
function tip(id, kb, tc) {
  save.tips = save.tips || {};
  if (save.tips[id] || S.mode !== 'play') return;
  if (S.tipT > 0 || S.cine || (L && L.time < 2.5)) return;
  save.tips[id] = 1; persist();
  const el = $('tip'); el.textContent = TR(touch.on ? (tc || kb) : kb); el.hidden = false; S.tipT = 4.5;
}
function updTips(dt) {
  if (S.tipT > 0) { S.tipT -= dt; if (S.tipT <= 0) $('tip').hidden = true; }
  if (!L) return;
  if (L.n === 1 && L.time > 1) tip('chase', 'Tu viens de voler cette voiture : la police te suit ! Roule (ZQSD ou flèches), sème-la, puis suis la flèche bleue.', 'Tu viens de voler cette voiture : la police te suit ! Pointe le joystick pour rouler, sème-la, puis suis la flèche bleue.');
  if (P.car && L.time > 8) tip('drive', 'Espace = frein à main pour tourner sec. C = changer de caméra. N = nitro.', 'FREIN = frein à main pour tourner sec. CAM = changer de caméra.');
  if (!P.car) { for (const c of cars) if (!c.wreck && dist(c.x, c.y, P.x, P.y) < 70) { tip('car', 'Appuie sur E pour voler cette voiture.', 'Touche ACTION pour voler cette voiture.'); break; } }
  if (stars() >= 2) tip('police', 'Plus tu as d’étoiles, plus la police est nombreuse. Pour la semer : reste hors de vue, prends un tunnel (T), repeins ta voiture (case rose) ou paie les agents (B).', 'Pour semer la police : reste hors de vue, prends un tunnel, repeins ta voiture (case rose) ou touche PAYER FLICS.');
  if (enemies.some(e => e.alert && e.hp > 0)) tip('fight', 'Des ennemis ! Tire avec Espace ou clic gauche. La visée aide automatiquement. Q = changer d’arme.', 'Des ennemis ! Garde TIRER appuyé, la visée est automatique. ARME = changer d’arme.');
  if (S.hp < 40) tip('heal', 'Santé basse : H pour une trousse de soins, ou mets-toi à l’abri.', 'Santé basse : touche SOIN, ou mets-toi à l’abri.');
  if (tileAt(P.x, P.y) === SHOP) tip('shop', 'Boutique : E pour acheter armes, armure et nitro avec l’argent gagné.', 'Boutique : touche ACTION pour acheter armes et équipement.');
}
// note de fin de niveau
const parTime = n => 360 + n * 12;
function levelStars(L) {
  const s1 = L.time <= parTime(L.n), s2 = S.hp >= 60 && (L.kos || 0) <= 3;
  return { stars: 1 + (s1 ? 1 : 0) + (s2 ? 1 : 0), fast: s1, clean: s2 };
}
const starStr = n => '★'.repeat(n) + '☆'.repeat(3 - n);

// ---------- effets ----------
function puff(x, y, col, s = 1) { parts.push({ x, y, vx: rnd(-20, 20), vy: rnd(-20, 20), life: s, max: s, r: rnd(6, 12), col, grow: 18 }); }
function sparks(x, y, n) { for (let i = 0; i < n; i++) parts.push({ x, y, vx: rnd(-200, 200), vy: rnd(-200, 200), life: rnd(.15, .35), max: .35, r: 2, col: '#fff2a8' }); }

// ---------- entrées ----------
const keys = {};
const mouse = { sx: 0, sy: 0, wx: 0, wy: 0, down: false, aim: 0 };
const touch = { jx: 0, jy: 0, mag: 0, shoot: false, on: false, autoAim: true };
addEventListener('keydown', e => {
  if (e.target && e.target.tagName === 'INPUT') return;
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) e.preventDefault();
  if (e.repeat) return;
  keys[e.code] = true;
  if (S.mode === 'play') {
    if (e.code === 'KeyE' || e.code === 'KeyF') contextAction();
    else if (e.code === 'KeyB') bribePolice();
    else if (e.code === 'KeyQ') cycleWeapon(1);
    else if (e.code === 'KeyH') useMedkit();
    else if (e.code === 'KeyN') useNitro();
    else if (e.code === 'KeyC') cycleCam();
    else if (e.code === 'KeyT') radioNext();
    else if (e.code === 'Tab' || e.code === 'KeyL') { e.preventDefault && e.preventDefault(); lockNext(); }
    else if (e.code === 'KeyR') startReload();
    else if (/^Digit[1-8]$/.test(e.code)) { const w = D.WEAPONS[+e.code.slice(5) - 1]; if (w && save.owned[w.id]) { save.weapon = w.id; msg(w.name); } }
    else if (e.code === 'Escape' || e.code === 'KeyP') pauseGame();
  } else if (S.mode === 'pause' && (e.code === 'Escape' || e.code === 'KeyP')) resumeGame();
});
addEventListener('keyup', e => { keys[e.code] = false; });
addEventListener('blur', () => { for (const k in keys) keys[k] = false; if (S.mode === 'play') pauseGame(); });
const cvs = document.getElementById('game'); let ctx = cvs.getContext('2d');
addEventListener('contextmenu', e => { if (S.mode === 'play') { e.preventDefault(); lockNext(); } });
[cvs, document.getElementById('game3d')].forEach(el => {
  el.addEventListener('mousemove', e => { mouse.sx = e.clientX; mouse.sy = e.clientY; mouse.aim = 3; });
  el.addEventListener('mousedown', e => { if (e.button === 0) { mouse.down = true; mouse.aim = 3; } });
  el.addEventListener('wheel', e => { if (S.mode === 'play') cycleWeapon(e.deltaY > 0 ? 1 : -1); }, { passive: true });
});
addEventListener('mouseup', () => { mouse.down = false; });
const $ = id => document.getElementById(id);
const touchEl = $('touch'), zone = $('stickZone'), base = $('stickBase'), knob = $('stickKnob');
function enableTouch() { if (touch.on) return; touch.on = true; touchEl.hidden = S.mode !== 'play'; document.body.classList.add('touch'); }
if (matchMedia('(pointer:coarse)').matches) enableTouch();
addEventListener('touchstart', enableTouch, { passive: true });
['pointerdown', 'keydown'].forEach(ev => addEventListener(ev, () => { if (S.cine && S.cine.t > .4) skipCine(); if (AU) { AU.init(); if (S.mode === 'menu' && !L) au('setMusic', 'menu'); } }, { passive: true }));
let stickId = null, sc = { x: 0, y: 0 };
zone.addEventListener('pointerdown', e => {
  stickId = e.pointerId; zone.setPointerCapture(e.pointerId);
  const r = base.getBoundingClientRect(); sc = { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  if (Math.hypot(e.clientX - sc.x, e.clientY - sc.y) > 90) { base.style.left = (e.clientX - 60) + 'px'; base.style.bottom = (innerHeight - e.clientY - 60) + 'px'; sc = { x: e.clientX, y: e.clientY }; }
  moveStick(e);
});
zone.addEventListener('pointermove', e => { if (e.pointerId === stickId) moveStick(e); });
const endStick = e => { if (e.pointerId !== stickId) return; stickId = null; touch.jx = touch.jy = touch.mag = 0; knob.style.transform = ''; };
zone.addEventListener('pointerup', endStick); zone.addEventListener('pointercancel', endStick);
function moveStick(e) { let dx = e.clientX - sc.x, dy = e.clientY - sc.y; const m = Math.hypot(dx, dy), mx = 50; if (m > mx) { dx *= mx / m; dy *= mx / m; } knob.style.transform = `translate(${dx}px,${dy}px)`; touch.mag = Math.min(1, m / mx); touch.jx = dx / mx; touch.jy = dy / mx; }
// ---------- manette (Xbox, PlayStation, Bluetooth) ----------
const pad = { on: false, lx: 0, ly: 0, lmag: 0, rx: 0, ry: 0, rmag: 0, rt: 0, lt: 0, hb: false, prev: [] };
addEventListener('gamepadconnected', () => { pad.on = true; document.body.classList.add('pad'); toast('Manette connectée'); });
addEventListener('gamepaddisconnected', () => { pad.on = false; document.body.classList.remove('pad'); });
function pollPad() {
  if (!navigator.getGamepads) return;
  const gp = [...navigator.getGamepads()].find(g => g && g.connected); if (!gp) { pad.on = false; return; }
  pad.on = true;
  const dz = v => Math.abs(v) < .15 ? 0 : v, ax = gp.axes;
  pad.lx = dz(ax[0] || 0); pad.ly = dz(ax[1] || 0); pad.lmag = Math.min(1, Math.hypot(pad.lx, pad.ly));
  pad.rx = dz(ax[2] || 0); pad.ry = dz(ax[3] || 0); pad.rmag = Math.min(1, Math.hypot(pad.rx, pad.ry));
  const bv = i => gp.buttons[i] ? (gp.buttons[i].value || (gp.buttons[i].pressed ? 1 : 0)) : 0;
  pad.rt = bv(7); pad.lt = bv(6); pad.hb = bv(1) > .5 && !!P.car;
  const press = i => bv(i) > .5 && !pad.prev[i];
  if (S.mode === 'play') {
    if (press(0)) contextAction();                       // A : action / voiture
    if (press(1) && !P.car) useMedkit();                 // B : soin (frein à main en voiture)
    if (press(2)) P.car ? useNitro() : startReload();    // X : recharger / nitro
    if (press(3) || press(5)) cycleWeapon(1);            // Y / RB : arme suivante
    if (press(4)) cycleCam();                            // LB : caméra
    if (press(8)) bribePolice();                         // Select : soudoyer
    if (press(12)) useMedkit();                          // croix haut : soin
    if (press(15)) radioNext();
    if (press(6) && !P.car) lockNext();                  // gâchette gauche à pied : verrouiller                          // croix droite : radio
    if (press(9)) pauseGame();                           // Start : pause
  } else if (S.mode === 'pause' && press(9)) resumeGame();
  pad.prev = gp.buttons.map(b => b.pressed);
}
const tb = (id, fn) => $(id).addEventListener('pointerdown', e => { e.preventDefault(); fn(); });
{ const fb = $('bShoot'), knob2 = $('fireKnob'); let fid = null, fx0 = 0, fy0 = 0;
  fb.addEventListener('pointerdown', e => { e.preventDefault(); fid = e.pointerId; try { fb.setPointerCapture(e.pointerId); } catch (er) {} fx0 = e.clientX; fy0 = e.clientY; touch.shoot = true; touch.aiming = false; vib(8); });
  fb.addEventListener('pointermove', e => { if (e.pointerId !== fid) return; let dx = e.clientX - fx0, dy = e.clientY - fy0; const m = Math.hypot(dx, dy);
    if (m > 12 && !P.car) { touch.aiming = true; touch.aimA = Math.atan2(dy, dx) + camRot(); fb.classList.add('aiming'); const k = Math.min(1, 40 / m); knob2.style.transform = `translate(${dx * k}px,${dy * k}px)`; } });
  const endF = e => { if (e.pointerId !== fid) return; fid = null; touch.shoot = false; touch.aiming = false; fb.classList.remove('aiming'); knob2.style.transform = ''; };
  fb.addEventListener('pointerup', endF); fb.addEventListener('pointercancel', endF); }
$('portraitOk').addEventListener('click', () => { save.portraitOk = true; persist(); $('rotate').hidden = true; S.rot = false; });
tb('bLock', lockNext); tb('bRadio', radioNext); tb('bCam', cycleCam); tb('bAct', contextAction); tb('bWep', () => cycleWeapon(1)); tb('bMed', () => P.car ? (S.hbTouch = 1) : useMedkit()); tb('bRel', () => P.car ? useNitro() : startReload()); tb('bBribe', bribePolice); tb('bNitro', useNitro); tb('bPause', pauseGame);

// ---------- HUD ----------
const hud = { money: $('money'), stars: $('stars'), hp: $('hp'), armor: $('armor'), wep: $('wep'), inv: $('inv'), step: $('step'), sN: $('sN'), sD: $('sD'), sC: $('sC'), dots: $('dots'), lvlName: $('lvlName'), toast: $('toast'), banner: $('banner'), prompt: $('prompt'), vipBar: $('vipBar'), vipHp: $('vipHp'), fade: $('fade') };
const starEls = [...hud.stars.children];
const last = {};
let toastT = 0, msgT = 0;
function toast(t) { t = TR(t); hud.toast.textContent = t; hud.toast.style.opacity = 1; toastT = 2.4; }
function msg(t) { if (S.msgCd > 0 && last.msg === t) return; last.msg = t; S.msgCd = 1.5; hud.prompt.textContent = TR(t); hud.prompt.hidden = false; msgT = 1.6; }
function showBanner(t) { hud.banner.textContent = TR(t); hud.banner.style.opacity = 1; setTimeout(() => { hud.banner.style.opacity = 0; }, 1500); }
function fade(t) { hud.fade.textContent = TR(t); hud.fade.style.opacity = 1; setTimeout(() => { hud.fade.style.opacity = 0; }, 1300); }
function setText(el, k, v) { if (last[k] !== v) { last[k] = v; el.textContent = TR(v); } }
function setW(el, k, v) { if (last[k] !== v) { last[k] = v; el.style.width = v + '%'; } }
function updHud(dt) {
  setText(hud.money, 'm', fmt(save.money));
  const s = stars(); if (last.s !== s) { last.s = s; starEls.forEach((e, i) => e.classList.toggle('on', i < s)); }
  const seen = s > 0 && S.unseen < .5; if (last.seen !== seen) { last.seen = seen; hud.stars.classList.toggle('blink', seen); }
  setW(hud.hp, 'hp', Math.max(0, Math.round(S.hp)));
  setW(hud.armor, 'ar', armorMax() ? Math.round(P.armor / 150 * 100) : 0);
  { const w = wepDef(save.weapon), am = P.ammo && P.ammo[w.id]; setText(hud.wep, 'w', w.name + (am ? ` ${am.mag}/${w.mag} · ${am.res === Infinity ? '∞' : am.res}` : '') + (P.reload > 0 ? ' · recharge…' : '')); }
  { const m = Math.floor(((S.tod || 0) * 1440)), hh = Math.floor(m / 60), mm = m % 60; setText($('clock'), 'clk', String(hh).padStart(2, '0') + ':' + String(mm - mm % 5).padStart(2, '0') + (S.rain ? ' · pluie' : '')); }
  setText(hud.inv, 'inv', 'Soins ' + save.medkits + ' · Nitro ' + save.nitro);
  if (L && L.step) {
    const st = L.step;
    setText(hud.lvlName, 'ln', 'Niveau ' + L.n + ' · ' + L.def.t);
    setText(hud.sN, 'sn', 'Étape ' + (L.idx + 1) + '/10 · ' + st.label);
    setText(hud.sD, 'sd', st.needCar && !P.car ? stepDesc(st) + ' (monte dans une voiture : E)' : stepDesc(st));
    const t = st.time !== null ? Math.max(0, Math.ceil(st.time)) : null;
    const km = gps.len ? (gps.len / 1000 * .5).toFixed(1).replace('.', ',') + ' km' : '', eta = gps.len ? Math.ceil(gps.len / (P.car ? 300 : 150)) : 0;
    const late = t !== null && eta > t && !st.survive;
    setText(hud.sC, 'sc', (t === null ? '' : `${(t / 60) | 0}:${String(t % 60).padStart(2, '0')}`) + (km ? (t === null ? '' : ' · ') + km + ' · ~' + eta + ' s' : ''));
    if (last.late !== late) { last.late = late; hud.sC.style.color = late ? 'var(--danger)' : ''; }
    if (last.dots !== L.idx) { last.dots = L.idx; hud.dots.innerHTML = Array.from({ length: 10 }, (_, i) => `<i class="${i < L.idx ? 'd' : i === L.idx ? 'c' : ''}"></i>`).join(''); }
  }
  const vipOn = !!(vip && vip.hp > 0 && !vip.done);
  if (last.vip !== vipOn) { last.vip = vipOn; hud.vipBar.hidden = !vipOn; }
  if (vipOn) { setW(hud.vipHp, 'vh', Math.round(vip.hp / vip.max * 100)); }
  // aide contextuelle
  let hint = '';
  const t2 = tileAt(P.x, P.y);
  if (agent && !agent.paid && dist(P.x, P.y, agent.x, agent.y) < 60) hint = 'E : payer l’agent (' + fmt(agent.cost) + ')';
  else if (t2 === TUNNEL) hint = 'E : prendre le tunnel';
  else if (t2 === SHOP && !P.car) hint = 'E : ouvrir la boutique';
  else if (s > 0 && nearCop()) hint = 'B : soudoyer les agents (' + fmt(bribeCost()) + ')';
  if (msgT > 0) { msgT -= dt; if (msgT <= 0) hud.prompt.hidden = true; }
  else { hud.prompt.hidden = !hint; if (hint) setText(hud.prompt, 'hint', hint); }
  const bb = $('bBribe'), bn = $('bNitro'); const showB = s > 0 && nearCop(); if (last.bb !== showB) { last.bb = showB; bb.hidden = !showB; }
  const inCar = !!P.car; if (last.bn !== inCar) { last.bn = inCar; bn.hidden = true; $('bRadio').hidden = !inCar; $('fireLbl').textContent = TR(inCar ? 'FREIN' : 'TIRER'); $('bShoot').querySelector('small').textContent = TR(inCar ? 'frein à main' : 'glisse pour viser'); $('lblX').textContent = TR(inCar ? 'NITRO' : 'RECHARGE'); $('lblB').textContent = TR(inCar ? 'SOIN' : 'SOIN'); }
  { let la = 'ACTION'; if (P.car) la = 'DESCENDRE'; else if (agent && !agent.paid && dist(P.x, P.y, agent.x, agent.y) < 60) la = 'PAYER'; else if (tileAt(P.x, P.y) === TUNNEL) la = 'TUNNEL'; else if (tileAt(P.x, P.y) === SHOP) la = 'BOUTIQUE'; else if (cars.some(c => !c.wreck && dist(c.x, c.y, P.x, P.y) < 48)) la = 'MONTER';
    if (last.la !== la) { last.la = la; $('lblA').textContent = TR(la); } }
  if (toastT > 0) { toastT -= dt; if (toastT <= 0) hud.toast.style.opacity = 0; }
}

// ---------- boucle de jeu ----------
const PCOUNT = [0, 1, 2, 3, 5, 7];
function update(dt) {
  S.time += dt; S.msgCd -= dt; mouse.aim -= dt; S.tunnelCd -= dt;
  if (P.nitro > 0) P.nitro -= dt;
  if (peds.length < Q.peds && Math.random() < .5) spawnPed();
  if (cars.filter(c => c.ai === 'traffic').length < Q.traffic && Math.random() < .3) spawnTraffic();
  const want = Math.max(stars() ? 1 : 0, Math.round(PCOUNT[stars()] * (save.perks.radio ? .6 : 1) * (.5 + .5 * ez()) + (stars() >= 3 ? Math.floor(lvl() / 12) : 0)));
  const cops = cars.filter(c => c.kind === 'police' && c.ai === 'police');
  S.spawnPol -= dt; if (cops.length < want && S.spawnPol <= 0) { spawnPolice(); S.spawnPol = save.perks.radio ? 2 : 1.2; }
  const Lk = keys.KeyA || keys.ArrowLeft, Rk = keys.KeyD || keys.ArrowRight, U = keys.KeyW || keys.ArrowUp, Dn = keys.KeyS || keys.ArrowDown;
  pollPad();
  const act = keys.Space || mouse.down || touch.shoot || pad.rt > .3;
  if (S.dead <= 0) {
    if (P.car) {
      const c = P.car; let thr = (U ? 1 : 0) - (Dn ? 1 : 0), st = (Rk ? 1 : 0) - (Lk ? 1 : 0);
      if (pad.on) { if (pad.rt > .05 || pad.lt > .05) thr = pad.rt - pad.lt; if (Math.abs(pad.lx) > .15) st = pad.lx; }
      if (touch.mag > .2) { const ja = Math.atan2(touch.jy, touch.jx) + camRot(), d = angDiff(ja, c.a); if (Math.abs(d) > 2.5) { thr = -touch.mag; st = 0; } else { thr = touch.mag; st = clamp(d * 2.2, -1, 1); } }
      if ((keys.ShiftLeft || keys.ShiftRight) && P.nitro <= 0 && save.nitro > 0 && thr > 0 && !last.shiftN) { useNitro(); }
      last.shiftN = keys.ShiftLeft || keys.ShiftRight;
      drive(c, dt, thr, st, (keys.Space || mouse.down || touch.shoot || pad.hb || S.hbTouch > 0) && true); if (S.hbTouch > 0) S.hbTouch -= dt * 3;
      P.x = c.x; P.y = c.y; P.a = c.a;
    } else {
      let mx = (Rk ? 1 : 0) - (Lk ? 1 : 0), my = (Dn ? 1 : 0) - (U ? 1 : 0);
      if (touch.mag > .15) { mx = touch.jx; my = touch.jy; }
      if (pad.lmag > .2) { mx = pad.lx; my = pad.ly; }
      const m = Math.hypot(mx, my);
      if (m > .1) { const sp = (keys.ShiftLeft || keys.ShiftRight || touch.mag > .9 || pad.lmag > .9 ? 230 : 150) * Math.min(1, m); const ma = Math.atan2(my, mx) + camRot(); P.a = ma; movePlayer(Math.cos(ma) * sp * dt, Math.sin(ma) * sp * dt); P.step += sp * dt * .25; }
      if (pad.rmag > .3) { touch.aiming = true; touch.aimA = Math.atan2(pad.ry, pad.rx) + camRot(); S.padAim = true; } else if (S.padAim) { S.padAim = false; if (!touch.shoot) touch.aiming = false; }
      if (touch.aiming) P.a = touch.aimA;
      P.cd -= dt; if (act && P.cd <= 0) fire();
    }
  }
  for (const c of cars) {
    if (c === P.car || c.wreck) { if (c.wreck && Math.random() < dt * 3) puff(c.x, c.y, '#2d283f', 1.4); continue; }
    if (c.ai === 'traffic' || c.ai === 'convoy') updTraffic(c, dt); else if (c.ai === 'gang') updGang(c, dt); else if (c.ai === 'block') drive(c, dt, 0, 0, true); else if (c.kind === 'police' && c.ai) updPolice(c, dt); else drive(c, dt, 0, 0, false);
    if (c.hp < 35 && Math.random() < dt * 6) puff(c.x + Math.cos(c.a) * 14, c.y + Math.sin(c.a) * 14, '#4a4560', 1);
  }
  if (P.car && P.car.hp < 35 && Math.random() < dt * 6) puff(P.car.x + Math.cos(P.car.a) * 14, P.car.y + Math.sin(P.car.a) * 14, '#4a4560', 1);
  for (let i = 0; i < cars.length; i++) {
    const a = cars[i];
    for (let j = i + 1; j < cars.length; j++) {
      const b = cars[j];
      const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy); if (d >= 30 || d === 0) continue;
      const push = (30 - d) / 2, nx = dx / d, ny = dy / d;
      if (!a.wreck && !carHits(a.x - nx * push, a.y - ny * push, a.a)) { a.x -= nx * push; a.y -= ny * push; }
      if (!b.wreck && !carHits(b.x + nx * push, b.y + ny * push, b.a)) { b.x += nx * push; b.y += ny * push; }
      const rel = Math.hypot(Math.cos(a.a) * a.v - Math.cos(b.a) * b.v, Math.sin(a.a) * a.v - Math.sin(b.a) * b.v);
      if (rel > 110) {
        { const [pn, vl] = spatial(a.x, a.y); if (vl > .1) au('crash', vl * Math.min(1, rel / 300), pn); } damageCar(a, rel * .045); damageCar(b, rel * .045); sparks((a.x + b.x) / 2, (a.y + b.y) / 2, 6);
        if (a === P.car || b === P.car) { vib(Math.min(120, rel / 4)); shake = Math.min(10, rel / 40); const o = a === P.car ? b : a; if (o.kind === 'police' && o.ai) addHeat(.15); if (o.ai === 'traffic' || o.ai === 'convoy') o.panic = 3; }
      }
      a.v *= .7; b.v *= .7;
    }
  }
  for (const c of cars) {
    const sp = Math.abs(c.v); if (sp < 55 || c.wreck) continue;
    for (const p of peds) if (p.state !== 'ko' && dist(c.x, c.y, p.x, p.y) < 20) koPed(p, c === P.car);
    for (const e of enemies) if (e.hp > 0 && dist(c.x, c.y, e.x, e.y) < 22) { hitEnemy(e, sp * .5); }
    if (vip && vip.hp > 0 && !vip.inCar && c !== P.car && dist(c.x, c.y, vip.x, vip.y) < 20) hurtVip(sp * .05);
    if (!P.car && S.dead <= 0 && dist(c.x, c.y, P.x, P.y) < 22 && P.hurt <= 0) { hurt(sp * .06); P.hurt = .6; const a = Math.atan2(P.y - c.y, P.x - c.x); moveBody(P, Math.cos(a) * 30, Math.sin(a) * 30); }
  }
  P.hurt -= dt; updLock();
  if (P.reload > 0) { P.reload -= dt; if (P.reload <= 0) finishReload(); }
  if (P.punch > 0) P.punch -= dt;
  updHeli(dt); updRoadblocks(dt);
  for (const p of peds) updPed(p, dt);
  shootersNow = Math.max(0, shootersNow - dt * 6);
  for (const e of enemies) updEnemy(e, dt);
  updGrenades(dt);
  updVip(dt);
  // balles
  for (const b of bullets) {
    b.life -= dt; const nx = b.x + b.vx * dt, ny = b.y + b.vy * dt;
    if (!b.air && blocksShot(nx, ny)) { b.life = 0; sparks(b.x, b.y, 3); if (b.explosive) explosionAt(b.x, b.y, 95, b.dmg, true); continue; }
    b.x = nx; b.y = ny;
    if (b.from === 'player') {
      let hit = false;
      for (const e of enemies) if (e.hp > 0 && dist(b.x, b.y, e.x, e.y) < (e.boss ? 16 : 12)) { hitEnemy(e, b.dmg); hit = true; break; }
      if (!hit) for (const p of peds) if (p.state !== 'ko' && dist(b.x, b.y, p.x, p.y) < 11) { koPed(p, true); hit = true; break; }
      if (!hit) for (const c of cars) if (c !== P.car && !c.wreck && dist(b.x, b.y, c.x, c.y) < 20) { damageCar(c, b.dmg * .7); sparks(b.x, b.y, 4); hit = true; if (c.kind === 'police') addHeat(.35); else if (c.ai) c.panic = 4; break; }
      if (!hit && heli && dist(b.x, b.y, heli.x, heli.y) < 28) { hitHeli(b.dmg); hit = true; }
      if (hit) { b.life = 0; if (b.explosive) explosionAt(b.x, b.y, 95, b.dmg, true); }
      else if (b.life <= 0 && b.explosive) explosionAt(b.x, b.y, 95, b.dmg, true);
    } else {
      if (P.car && dist(b.x, b.y, P.car.x, P.car.y) < 20) { damageCar(P.car, b.dmg * .6); b.life = 0; sparks(b.x, b.y, 3); continue; }
      if (!P.car && dist(b.x, b.y, P.x, P.y) < 12) { hurt(b.dmg); b.life = 0; continue; }
      if (vip && vip.hp > 0 && !vip.inCar && dist(b.x, b.y, vip.x, vip.y) < 12) { hurtVip(b.dmg * .8); b.life = 0; continue; }
      for (const p of peds) if (p.state !== 'ko' && dist(b.x, b.y, p.x, p.y) < 10) { koPed(p, false); b.life = 0; break; }
    }
  }
  bullets = bullets.filter(b => b.life > 0);
  for (const k of picks) { k.t -= dt; if (k.ammo) { if (dist(P.x, P.y, k.x, k.y) < 30) { for (const w of D.WEAPONS) if (w.mag && P.ammo[w.id] && save.owned[w.id] && P.ammo[w.id].res !== Infinity) P.ammo[w.id].res = Math.min(w.reserve, P.ammo[w.id].res + w.mag); au('pickup'); msg('Munitions'); k.t = 0; } continue; } if (dist(P.x, P.y, k.x, k.y) < 30) { save.money += k.amt; if (L) L.earned += k.amt; au('cash'); track('cashPicked', k.amt); msg('+' + fmt(k.amt)); k.t = 0; } }
  picks = picks.filter(k => k.t > 0);
  { const rid = world.region.id; save.tagsFound = save.tagsFound || {}; const got = save.tagsFound[rid] = save.tagsFound[rid] || [];
    world.tags.forEach((tg, i) => { if (got.includes(i) || dist(P.x, P.y, tg.x, tg.y) > 34) return; got.push(i); const r = 300 + 150 * Object.keys(REGION_RADIO).indexOf(rid); save.money += r; au('pickup'); vib([30, 30, 60]); toast('Tag secret ' + got.length + '/12 · +' + fmt(r)); track('tags'); persist(); }); }
  for (const c of cases) if (!c.got && dist(P.x, P.y, c.x, c.y) < 32) { c.got = true; au('pickup'); msg('Valise récupérée'); sparks(c.x, c.y, 10); }
  // atelier de peinture
  if (P.car && tileAt(P.car.x, P.car.y) === PAD && stars() > 0 && !(L && L.step && L.step.lock)) {
    const cost = 200 + lvl() * 60;
    if (save.money >= cost) { save.money -= cost; S.heat = 0; P.car.color = pick(CIV); P.car.hp = Math.max(P.car.hp, 100); track('escapes'); toast('Voiture repeinte · police semée (−' + fmt(cost) + ')'); policeLeave(); }
    else msg('Il faut ' + fmt(cost) + ' pour repeindre');
  }
  // police
  const s = stars();
  if (s > 0) {
    if (cars.some(c => c.kind === 'police' && (c.ai === 'police' || c.ai === 'block') && dist(c.x, c.y, P.x, P.y) < 430) || (heli && !heli.leave && dist(heli.x, heli.y, P.x, P.y) < 600)) S.unseen = 0; else S.unseen += dt;
    const lose = ((save.perks.radio ? 5 : 7) + lvl() * .04) * (.55 + .45 * ez());
    if (S.unseen > lose && !(L && L.step && L.step.lock)) { S.heat = Math.max(0, s - 1); S.unseen = 0; if (S.heat < 1) { S.heat = 0; msg('Police semée'); policeLeave(); track('escapes'); } }
    let near = false; for (const c of cars) if (c.kind === 'police' && c.ai === 'police' && !c.wreck && dist(c.x, c.y, P.x, P.y) < (P.car ? 62 : 56) && Math.abs(c.v) < 90) { near = true; break; }
    if (near && (!P.car || Math.abs(P.car.v) < 30)) S.bust += dt * (P.car ? .6 : 1); else S.bust = Math.max(0, S.bust - dt);
    if (S.bust > 1.6 + (1 - ez()) * 3) failLevel('Arrêté par la police');
  } else { S.bust = 0; if (S.hp < 100) S.hp = Math.min(100, S.hp + dt * (1.5 + (1 - ez()) * 6)); }
  // nettoyage
  for (const c of cars) if (c.ai === 'block') { c.ttl -= dt; if (c.ttl <= 0 || stars() === 0) c.ai = 'leave'; }
  cars = cars.filter(c => { if (c === P.car || c.keep) return true; const d = dist(c.x, c.y, P.x, P.y); if (c.ai === 'leave' && d > 800) return false; return d < (c.ai ? 1700 : 2600); });
  peds = peds.filter(p => (p.state !== 'ko' || p.ko > 0) && dist(p.x, p.y, P.x, P.y) < 1300);
  enemies = enemies.filter(e => e.hp > 0 || (e.dead = (e.dead || 0) + dt) < 8);
  for (const p of parts) { p.life -= dt; p.x += p.vx * dt; p.y += p.vy * dt; p.vx *= .92; p.vy *= .92; if (p.grow) p.r += p.grow * dt; }
  parts = parts.filter(p => p.life > 0); if (parts.length > 600) parts.splice(0, parts.length - 600);
  if (L) updLevel(dt);
}
function updVip(dt) {
  if (!vip || vip.hp <= 0) return;
  if (vip.inCar) { if (vip.inCar !== P.car) { const c = vip.inCar; vip.inCar = null; vip.x = c.x + 24; vip.y = c.y; } else { vip.x = vip.inCar.x; vip.y = vip.inCar.y; return; } }
  if (!vip.following) return;
  const d = dist(vip.x, vip.y, P.x, P.y);
  if (P.car && d < 80 && Math.abs(P.car.v) < 120) { vip.inCar = P.car; msg(vip.name + ' monte dans la voiture'); return; }
  if (d > 46) { const a = Math.atan2(P.y - vip.y, P.x - vip.x); vip.a = a; const sp = d > 200 ? 200 : 160; moveBody(vip, Math.cos(a) * sp * dt, Math.sin(a) * sp * dt); vip.step += sp * dt * .25; }
}

// ---------- rendu ----------
let DPR = 1, VW = 0, VH = 0;
function resize() { DPR = Math.min(2, devicePixelRatio || 1); VW = innerWidth; VH = innerHeight; cvs.width = Math.round(VW * DPR); cvs.height = Math.round(VH * DPR); }
addEventListener('resize', resize); resize();
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
function label(txt, x, y, col, size = 11) { ctx.fillStyle = col; ctx.font = size + 'px Bungee, Impact, sans-serif'; ctx.textAlign = 'center'; ctx.fillText(txt, x, y); }
function drawTile(tx, ty) {
  const i = ty * N + tx, t = world.map[i], x = tx * T, y = ty * T, h = hash(tx, ty), p = world.region.pal;
  if (t === ROAD) {
    ctx.fillStyle = p.road; ctx.fillRect(x, y, T, T);
    const mx = tx % B, my = ty % B, hr = my < 2, vr = mx < 2;
    if (hr && !vr) {
      if (mx === 2 || mx === 7) { ctx.fillStyle = 'rgba(235,230,255,.5)'; for (let k = 0; k < 5; k++) ctx.fillRect(x + (mx === 2 ? 6 : 44), y + 4 + k * 12, 14, 6); }
      else if (my === 0) { ctx.fillStyle = 'rgba(255,182,39,.7)'; ctx.fillRect(x + 8, y + T - 2, 20, 4); ctx.fillRect(x + 40, y + T - 2, 20, 4); }
    } else if (vr && !hr) {
      if (my === 2 || my === 7) { ctx.fillStyle = 'rgba(235,230,255,.5)'; for (let k = 0; k < 5; k++) ctx.fillRect(x + 4 + k * 12, y + (my === 2 ? 6 : 44), 6, 14); }
      else if (mx === 0) { ctx.fillStyle = 'rgba(255,182,39,.7)'; ctx.fillRect(x + T - 2, y + 8, 4, 20); ctx.fillRect(x + T - 2, y + 40, 4, 20); }
    }
    return;
  }
  if (t === WATER) {
    ctx.fillStyle = p.water; ctx.fillRect(x, y, T, T);
    ctx.strokeStyle = 'rgba(120,200,255,.18)'; ctx.lineWidth = 2; const o = (S.time * 12 + h) % 24;
    for (let k = 0; k < 3; k++) { ctx.beginPath(); ctx.moveTo(x + 6, y + 10 + k * 20 + o * .2); ctx.lineTo(x + 26, y + 10 + k * 20 + o * .2); ctx.stroke(); }
    return;
  }
  if (t === PARK || t === TREE) {
    ctx.fillStyle = p.park; ctx.fillRect(x, y, T, T);
    if (t === TREE || h % 4 === 0) {
      ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.beginPath(); ctx.arc(x + 36, y + 38, 22, 0, TAU); ctx.fill();
      ctx.fillStyle = p.tree; ctx.beginPath(); ctx.arc(x + 32, y + 32, t === TREE ? 24 : 15, 0, TAU); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,.08)'; ctx.beginPath(); ctx.arc(x + 26, y + 26, 8, 0, TAU); ctx.fill();
    }
    return;
  }
  if (t === BLD) {
    const fav = world.region.id === 'bra' && !world.wh[i] && tileIsFavela(tx, ty);
    let base = world.wh[i] ? '#2d2c35' : p.bld[(world.bcol[i] + (fav ? 0 : (h & 1))) % p.bld.length];
    ctx.fillStyle = base; ctx.fillRect(x, y, T, T);
    if (fav) {
      ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.fillRect(x, y + T - 10, T, 10);
      ctx.fillStyle = 'rgba(255,255,255,.12)'; ctx.fillRect(x + 4, y + 4, T - 8, 6);
      if (h % 3 === 0) { ctx.fillStyle = 'rgba(255,220,120,.55)'; ctx.fillRect(x + 12 + h % 30, y + 22, 8, 8); }
      ctx.strokeStyle = 'rgba(0,0,0,.4)'; ctx.lineWidth = 2; ctx.strokeRect(x + 1, y + 1, T - 2, T - 2);
      return;
    }
    if (world.wh[i]) { ctx.strokeStyle = 'rgba(255,255,255,.06)'; ctx.lineWidth = 2; for (let k = 8; k < T; k += 12) { ctx.beginPath(); ctx.moveTo(x, y + k); ctx.lineTo(x + T, y + k); ctx.stroke(); } }
    if (h % 4 === 0) { ctx.fillStyle = 'rgba(255,255,255,.07)'; ctx.fillRect(x + 14 + h % 20, y + 12 + h % 24, 16, 12); ctx.fillStyle = 'rgba(0,0,0,.3)'; ctx.fillRect(x + 14 + h % 20, y + 24 + h % 24, 16, 3); }
    const col = p.neon[world.bcol[i] % p.neon.length];
    ctx.strokeStyle = col;
    const edge = (nx, ny) => tileAt(nx, ny) !== BLD;
    const sides = [[edge(x + 1, y - 1), x, y + 3, x + T, y + 3], [edge(x + 1, y + T + 1), x, y + T - 3, x + T, y + T - 3], [edge(x - 1, y + 1), x + 3, y, x + 3, y + T], [edge(x + T + 1, y + 1), x + T - 3, y, x + T - 3, y + T]];
    for (const [on, a, b, c, d] of sides) { if (!on) continue; ctx.globalAlpha = .18; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(a, b); ctx.lineTo(c, d); ctx.stroke(); ctx.globalAlpha = 1; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(a, b); ctx.lineTo(c, d); ctx.stroke(); }
    return;
  }
  // sols praticables
  const sw = (world.region.look || {}).sidewalk;
  const beachWalk = sw === 'waves' && ty > N - 14;
  ctx.fillStyle = beachWalk ? '#e8e2d2' : t === PLAZA ? p.plaza : p.walk; ctx.fillRect(x, y, T, T);
  ctx.strokeStyle = p.line; ctx.lineWidth = 1; ctx.strokeRect(x + .5, y + .5, T - 1, T - 1);
  if (beachWalk) { ctx.strokeStyle = '#1c1a20'; ctx.lineWidth = 5; for (let k = 0; k < 3; k++) { ctx.beginPath(); for (let xx = 0; xx <= T; xx += 4) { const yy = y + 12 + k * 20 + Math.sin((x + xx) / 10) * 5; xx ? ctx.lineTo(x + xx, yy) : ctx.moveTo(x + xx, yy); } ctx.stroke(); } }
  else if (sw === 'cobble') { ctx.fillStyle = 'rgba(0,0,0,.18)'; for (let r = 0; r < 8; r++) for (let q = 0; q < 6; q++) ctx.fillRect(x + q * 11 + (r % 2) * 5 + 1, y + r * 8 + 1, 9, 6); }
  else if (sw === 'terracotta') { ctx.strokeStyle = 'rgba(120,50,20,.22)'; ctx.lineWidth = 2; for (let k = -T; k < T; k += 16) { ctx.beginPath(); ctx.moveTo(x + k, y); ctx.lineTo(x + k + T, y + T); ctx.moveTo(x + k + T, y); ctx.lineTo(x + k, y + T); ctx.stroke(); } }
  if (t === PLAZA) { ctx.strokeRect(x + 16.5, y + 16.5, 31, 31); }
  ctx.fillStyle = p.curb;
  if (tileAt(x - 1, y + 1) === ROAD) ctx.fillRect(x, y, 3, T); if (tileAt(x + T + 1, y + 1) === ROAD) ctx.fillRect(x + T - 3, y, 3, T);
  if (tileAt(x + 1, y - 1) === ROAD) ctx.fillRect(x, y, T, 3); if (tileAt(x + 1, y + T + 1) === ROAD) ctx.fillRect(x, y + T - 3, T, 3);
  const pad = (col, a, b) => { ctx.fillStyle = col + '33'; ctx.fillRect(x + 4, y + 4, T - 8, T - 8); ctx.strokeStyle = col; ctx.lineWidth = 3; ctx.strokeRect(x + 5, y + 5, T - 10, T - 10); ctx.fillStyle = col; ctx.font = '700 10px "Chakra Petch",sans-serif'; ctx.textAlign = 'center'; ctx.fillText(a, x + T / 2, y + T / 2 + 2); if (b) ctx.fillText(b, x + T / 2, y + T / 2 + 14); };
  if (t === PAD) pad('#ff2e93', TR('PEINTURE'), fmt(200 + lvl() * 60));
  else if (t === SHOP) { pad('#a6ff4d', TR('BOUTIQUE'), TR('armes')); }
  else if (t === GARAGE) { pad('#3ee0c5', TR('GARAGE'), ''); }
  else if (t === TUNNEL) {
    ctx.fillStyle = '#05040a'; ctx.beginPath(); ctx.arc(x + T / 2, y + T / 2, 22, 0, TAU); ctx.fill();
    ctx.strokeStyle = '#ffb627'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(x + T / 2, y + T / 2, 22, 0, TAU); ctx.stroke();
    ctx.fillStyle = '#ffb627'; ctx.font = '700 10px "Chakra Petch",sans-serif'; ctx.textAlign = 'center'; ctx.fillText(TR('TUNNEL'), x + T / 2, y + T / 2 + 4);
  }
}
function tileIsFavela(tx, ty) { const bx = Math.floor(tx / B), by = Math.floor(ty / B); const k = world.favCache || (world.favCache = {}); const key = bx + ',' + by; if (k[key] === undefined) { let w = 0; for (let ly = 3; ly < 7; ly++) for (let lx = 3; lx < 7; lx++) if (world.map[(by * B + ly) * N + bx * B + lx] === WALK) w++; k[key] = w > 0 && w < 10 && !(w === 4); } return k[key]; }
function drawCar(c) {
  ctx.save(); ctx.translate(c.x, c.y); ctx.rotate(c.a);
  ctx.fillStyle = 'rgba(0,0,0,.35)'; rr(-19, -8, 42, 22, 6); ctx.fill();
  ctx.fillStyle = c.wreck ? '#2a2633' : c.color; rr(-21, -10, 42, 20, 6); ctx.fill();
  if (!c.wreck) {
    ctx.fillStyle = 'rgba(10,8,25,.85)'; rr(3, -8, 9, 16, 2); ctx.fill(); rr(-15, -7, 6, 14, 2); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,.18)'; ctx.fillRect(-8, -8, 10, 16);
    ctx.fillStyle = '#fff7cc'; ctx.fillRect(18, -8, 3, 4); ctx.fillRect(18, 4, 3, 4);
    ctx.fillStyle = '#ff2e4d'; ctx.fillRect(-21, -8, 2, 4); ctx.fillRect(-21, 4, 2, 4);
    if (c.kind === 'police') { ctx.fillStyle = '#1b1f4a'; ctx.fillRect(-21, -10, 10, 20); ctx.fillRect(12, -10, 4, 20); const f = Math.sin((S.time + c.flash) * 14) > 0; ctx.fillStyle = f ? '#ff2e4d' : '#2e6bff'; ctx.fillRect(-4, -9, 4, 8); ctx.fillStyle = f ? '#2e6bff' : '#ff2e4d'; ctx.fillRect(-4, 1, 4, 8); }
    if (c.convoy) { ctx.strokeStyle = '#ff4d5e'; ctx.lineWidth = 2; rr(-21, -10, 42, 20, 6); ctx.stroke(); }
  } else { ctx.strokeStyle = '#14111d'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-14, -6); ctx.lineTo(10, 6); ctx.moveTo(-6, 8); ctx.lineTo(6, -8); ctx.stroke(); }
  ctx.restore();
  if (c.mark && !c.wreck) { const b = Math.sin(S.time * 6) * 4; ctx.fillStyle = c.convoy ? '#ff4d5e' : '#ffd700'; ctx.beginPath(); ctx.moveTo(c.x, c.y - 26 + b); ctx.lineTo(c.x - 8, c.y - 40 + b); ctx.lineTo(c.x + 8, c.y - 40 + b); ctx.closePath(); ctx.fill(); }
}
function drawPerson(x, y, a, skin, shirt, step, glow, scale = 1) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(a); ctx.scale(scale, scale);
  const sw = Math.sin(step) * 4;
  ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.beginPath(); ctx.ellipse(2, 2, 8, 9, 0, 0, TAU); ctx.fill();
  ctx.fillStyle = '#1a1530'; ctx.fillRect(-2 + sw, -6, 6, 4); ctx.fillRect(-2 - sw, 2, 6, 4);
  if (glow) { ctx.shadowColor = glow; ctx.shadowBlur = 14; }
  ctx.fillStyle = shirt; ctx.beginPath(); ctx.ellipse(0, 0, 6, 9, 0, 0, TAU); ctx.fill(); ctx.shadowBlur = 0;
  ctx.fillStyle = skin; ctx.beginPath(); ctx.arc(1, 0, 4.6, 0, TAU); ctx.fill();
  ctx.restore();
}
function bar(x, y, w, v, col) { ctx.fillStyle = 'rgba(0,0,0,.6)'; ctx.fillRect(x - w / 2, y, w, 4); ctx.fillStyle = col; ctx.fillRect(x - w / 2, y, w * clamp(v, 0, 1), 4); }
function render(dt) {
  if (R3.ok && world) { render3D(dt); return; }
  if (!world) { ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.fillStyle = '#0d0b1a'; ctx.fillRect(0, 0, VW, VH); return; }
  const tx = P.car ? P.car.x + Math.cos(P.car.a) * P.car.v * .35 : P.x, ty = P.car ? P.car.y + Math.sin(P.car.a) * P.car.v * .35 : P.y;
  const k = Math.min(1, dt * 4); cam.x += (tx - cam.x) * k; cam.y += (ty - cam.y) * k;
  const baseZ = clamp(Math.min(VW, VH) / 700, .55, 1.05), zt = baseZ * (P.car ? 1 - Math.min(.3, Math.abs(P.car.v) / 1700) : 1);
  cam.z += (zt - cam.z) * Math.min(1, dt * 2);
  const z = cam.z, sx = shake ? rnd(-shake, shake) : 0, sy = shake ? rnd(-shake, shake) : 0; shake = Math.max(0, shake - dt * 30);
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.fillStyle = world.region.pal.ground; ctx.fillRect(0, 0, VW, VH);
  ctx.translate(VW / 2 + sx, VH / 2 + sy); ctx.scale(z, z); ctx.translate(-cam.x, -cam.y);
  const x0 = cam.x - VW / 2 / z - T, x1 = cam.x + VW / 2 / z + T, y0 = cam.y - VH / 2 / z - T, y1 = cam.y + VH / 2 / z + T;
  const vis = (x, y, m = 60) => x > x0 - m && x < x1 + m && y > y0 - m && y < y1 + m;
  for (let yy = Math.max(0, Math.floor(y0 / T)); yy <= Math.min(N - 1, Math.floor(y1 / T)); yy++) for (let xx = Math.max(0, Math.floor(x0 / T)); xx <= Math.min(N - 1, Math.floor(x1 / T)); xx++) drawTile(xx, yy);
  const pulse = .5 + .5 * Math.sin(S.time * 4);
  for (const [pt, txt, col] of [[world.hospital, 'HÔPITAL', '#a6ff4d'], [world.station, 'POLICE', '#2e6bff']]) if (vis(pt.x, pt.y)) { ctx.fillStyle = col; ctx.globalAlpha = .25; rr(pt.x - 28, pt.y - 14, 56, 28, 6); ctx.fill(); ctx.globalAlpha = 1; label(txt, pt.x, pt.y + 4, col); }
  // cible
  const st = L && L.step, target = st ? stepTarget(st) : null;
  if (target) { ctx.strokeStyle = '#21e6ff'; ctx.lineWidth = 4; ctx.globalAlpha = .6 + .4 * pulse; ctx.beginPath(); ctx.arc(target.x, target.y, 36 + pulse * 8, 0, TAU); ctx.stroke(); ctx.globalAlpha = .15; ctx.fillStyle = '#21e6ff'; ctx.beginPath(); ctx.arc(target.x, target.y, 36, 0, TAU); ctx.fill(); ctx.globalAlpha = 1; }
  for (const p of picks) if (vis(p.x, p.y)) { ctx.fillStyle = '#a6ff4d'; ctx.shadowColor = '#a6ff4d'; ctx.shadowBlur = 10; rr(p.x - 8, p.y - 5, 16, 10, 2); ctx.fill(); ctx.shadowBlur = 0; ctx.fillStyle = '#0d2a10'; ctx.font = '700 9px "Chakra Petch",sans-serif'; ctx.textAlign = 'center'; ctx.fillText('$', p.x, p.y + 3); }
  for (const c of cases) if (!c.got && vis(c.x, c.y)) { const b = Math.sin(S.time * 5 + c.x) * 2; ctx.fillStyle = '#c98a2b'; ctx.shadowColor = '#ffb627'; ctx.shadowBlur = 12; rr(c.x - 9, c.y - 6 + b, 18, 13, 2); ctx.fill(); ctx.shadowBlur = 0; ctx.fillStyle = '#4a2f10'; ctx.fillRect(c.x - 3, c.y - 9 + b, 6, 3); }
  for (const p of peds) { if (!vis(p.x, p.y)) continue; if (p.state === 'ko') { ctx.fillStyle = p.shirt; ctx.globalAlpha = .6; ctx.beginPath(); ctx.ellipse(p.x, p.y, 9, 5, .4, 0, TAU); ctx.fill(); ctx.globalAlpha = 1; } else drawPerson(p.x, p.y, p.a, p.skin, p.shirt, p.step); }
  for (const e of enemies) { if (!vis(e.x, e.y)) continue; if (e.hp <= 0) { ctx.fillStyle = e.color; ctx.globalAlpha = .35; ctx.beginPath(); ctx.ellipse(e.x, e.y, 10, 5, .3, 0, TAU); ctx.fill(); ctx.globalAlpha = 1; continue; }
    drawPerson(e.x, e.y, e.a, '#c68b59', '#16121f', e.step, e.color, e.boss ? 1.5 : 1);
    ctx.strokeStyle = e.color; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(e.x, e.y, e.boss ? 16 : 11, 0, TAU); ctx.stroke();
    ctx.save(); ctx.translate(e.x, e.y); ctx.rotate(e.a); ctx.fillStyle = '#0a0a0a'; ctx.fillRect(6, 2, 12, 3); ctx.restore();
    if (e.alert || e.boss) bar(e.x, e.y - (e.boss ? 30 : 20), e.boss ? 46 : 22, e.hp / e.max, e.color);
    if (e.boss) label(e.boss.toUpperCase(), e.x, e.y - 34, e.color, 10); }
  if (agent && !agent.paid && vis(agent.x, agent.y)) { drawPerson(agent.x, agent.y, S.time, '#f2d3b3', '#2e6bff', 0, '#2e6bff'); label('AGENT  $', agent.x, agent.y - 18, '#ffb627', 10); }
  if (vip && vip.hp > 0 && !vip.inCar && !vip.done && vis(vip.x, vip.y)) { drawPerson(vip.x, vip.y, vip.a, '#8d5a3b', '#ffd700', vip.step, '#ffd700'); bar(vip.x, vip.y - 20, 26, vip.hp / vip.max, '#ffd700'); label('VIP', vip.x, vip.y - 24, '#ffd700', 9); }
  for (const c of cars) if (vis(c.x, c.y)) drawCar(c);
  if (heli && vis(heli.x, heli.y)) { ctx.fillStyle = 'rgba(255,247,192,.18)'; ctx.beginPath(); ctx.arc(heli.x, heli.y, 60, 0, TAU); ctx.fill(); ctx.fillStyle = '#1b1f4a'; ctx.beginPath(); ctx.ellipse(heli.x, heli.y - 40, 26, 12, 0, 0, TAU); ctx.fill(); ctx.strokeStyle = '#333'; ctx.lineWidth = 3; ctx.beginPath(); const ra = S.time * 20; ctx.moveTo(heli.x - Math.cos(ra) * 50, heli.y - 40 - Math.sin(ra) * 50); ctx.lineTo(heli.x + Math.cos(ra) * 50, heli.y - 40 + Math.sin(ra) * 50); ctx.stroke(); }
  if (!P.car && S.mode === 'play') { drawPerson(P.x, P.y, P.a, '#f2d3b3', '#21e6ff', P.step, '#21e6ff'); ctx.save(); ctx.translate(P.x, P.y); ctx.rotate(P.a); ctx.fillStyle = '#0a0a0a'; const wl = { pistol: 8, uzi: 10, shotgun: 14, rifle: 16, sniper: 20, rocket: 18, minigun: 16 }[save.weapon] || 8; ctx.fillRect(6, 2, wl, 3); ctx.restore(); }
  for (const b of bullets) { ctx.strokeStyle = b.from === 'enemy' ? '#ff6b6b' : b.explosive ? '#ffb627' : '#fff2a8'; ctx.lineWidth = b.explosive ? 5 : 2; ctx.beginPath(); ctx.moveTo(b.x, b.y); ctx.lineTo(b.x - b.vx * .02, b.y - b.vy * .02); ctx.stroke(); }
  for (const p of parts) { if (!vis(p.x, p.y)) continue; ctx.globalAlpha = clamp(p.life / p.max, 0, 1) * (p.grow ? .5 : 1); ctx.fillStyle = p.col; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, TAU); ctx.fill(); }
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'lighter';
  for (const c of cars) {
    if (c.wreck || !vis(c.x, c.y, 150)) continue;
    ctx.save(); ctx.translate(c.x, c.y); ctx.rotate(c.a);
    const g = ctx.createLinearGradient(20, 0, 150, 0); g.addColorStop(0, 'rgba(255,240,190,.2)'); g.addColorStop(1, 'rgba(255,240,190,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(20, -8); ctx.lineTo(150, -46); ctx.lineTo(150, 46); ctx.lineTo(20, 8); ctx.closePath(); ctx.fill();
    if (c.kind === 'police') { const f = Math.sin((S.time + c.flash) * 14) > 0; ctx.fillStyle = f ? 'rgba(255,46,77,.22)' : 'rgba(46,107,255,.22)'; ctx.beginPath(); ctx.arc(-2, 0, 44, 0, TAU); ctx.fill(); }
    ctx.restore();
  }
  ctx.globalCompositeOperation = 'source-over';
  if (target && S.mode === 'play') { const d = dist(P.x, P.y, target.x, target.y); if (d > 200) { const a = Math.atan2(target.y - P.y, target.x - P.x), r = P.car ? 54 : 40; ctx.save(); ctx.translate(P.x + Math.cos(a) * r, P.y + Math.sin(a) * r); ctx.rotate(a); ctx.fillStyle = '#21e6ff'; ctx.shadowColor = '#21e6ff'; ctx.shadowBlur = 10; ctx.beginPath(); ctx.moveTo(12, 0); ctx.lineTo(-6, -8); ctx.lineTo(-2, 0); ctx.lineTo(-6, 8); ctx.closePath(); ctx.fill(); ctx.restore(); } }
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  const vg = ctx.createRadialGradient(VW / 2, VH / 2, Math.min(VW, VH) * .35, VW / 2, VH / 2, Math.max(VW, VH) * .75); vg.addColorStop(0, 'rgba(10,8,20,0)'); vg.addColorStop(1, 'rgba(10,8,20,.65)'); ctx.fillStyle = vg; ctx.fillRect(0, 0, VW, VH);
  if (S.hp < 30 && S.mode === 'play') { ctx.fillStyle = `rgba(255,46,77,${.12 + .08 * pulse})`; ctx.fillRect(0, 0, VW, VH); }
  mouse.wx = cam.x + (mouse.sx - VW / 2) / z; mouse.wy = cam.y + (mouse.sy - VH / 2) / z;
  drawMini(target);
}
const mini = $('mini'), mctx = mini.getContext('2d');
// ---------- GPS : chemin par les routes jusqu'à l'objectif ----------
const gps = { path: [], len: 0, key: '', t: 0 };
function gpsCompute(sx, sy, tx, ty) {
  const s0 = [Math.floor(sx / T), Math.floor(sy / T)], g0 = [Math.floor(tx / T), Math.floor(ty / T)];
  const idx = (x, y) => y * N + x, cost = t => t === ROAD ? 1 : (t === WALK || t === PAD || t === SHOP || t === GARAGE || t === TUNNEL || t === PLAZA || t === PARK) ? 4 : 0;
  const open = [[0, s0[0], s0[1]]], gS = new Float32Array(N * N).fill(1e9), from = new Int32Array(N * N).fill(-1), closed = new Uint8Array(N * N);
  gS[idx(...s0)] = 0; let found = false, guard = 0;
  while (open.length && guard++ < 9000) {
    let bi = 0; for (let i = 1; i < open.length; i++) if (open[i][0] < open[bi][0]) bi = i;
    const [, x, y] = open.splice(bi, 1)[0], k = idx(x, y); if (closed[k]) continue; closed[k] = 1;
    if (x === g0[0] && y === g0[1]) { found = true; break; }
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const nx = x + dx, ny = y + dy; if (nx < 0 || ny < 0 || nx >= N || ny >= N) continue; const nk = idx(nx, ny); const c = (nx === g0[0] && ny === g0[1]) ? 1 : cost(world.map[nk]); if (!c || closed[nk]) continue;
      const ng = gS[k] + c; if (ng < gS[nk]) { gS[nk] = ng; from[nk] = k; open.push([ng + Math.abs(nx - g0[0]) + Math.abs(ny - g0[1]), nx, ny]); } }
  }
  if (!found) return [];
  const out = []; let k = idx(...g0); while (k >= 0) { out.push({ x: (k % N + .5) * T, y: (Math.floor(k / N) + .5) * T }); k = from[k]; }
  out.reverse(); out[0] = { x: sx, y: sy }; out[out.length - 1] = { x: tx, y: ty };
  // on ne garde que les virages
  const simp = [out[0]]; for (let i = 1; i < out.length - 1; i++) { const a = simp[simp.length - 1], b = out[i], c = out[i + 1]; if (Math.sign(b.x - a.x) !== Math.sign(c.x - b.x) || Math.sign(b.y - a.y) !== Math.sign(c.y - b.y)) simp.push(b); } simp.push(out[out.length - 1]);
  return simp;
}
function gpsUpdate(target, dt) {
  gps.t -= dt;
  if (!target) { gps.path = []; gps.len = 0; return; }
  const px = P.car ? P.car.x : P.x, py = P.car ? P.car.y : P.y, key = Math.floor(px / T) + ',' + Math.floor(py / T) + '>' + Math.floor(target.x / T) + ',' + Math.floor(target.y / T);
  if (key !== gps.key && gps.t <= 0) { gps.key = key; gps.t = .35; gps.path = gpsCompute(px, py, target.x, target.y); }
  if (gps.path.length) { gps.path[0] = { x: px, y: py }; let l = 0; for (let i = 1; i < gps.path.length; i++) l += dist(gps.path[i - 1].x, gps.path[i - 1].y, gps.path[i].x, gps.path[i].y); gps.len = l; }
}
function drawMini(target) {
  const s = mini.width / W; mctx.drawImage(world.mm, 0, 0, mini.width, mini.height);
  const dot = (x, y, c, r) => { mctx.fillStyle = c; mctx.beginPath(); mctx.arc(x * s, y * s, r, 0, TAU); mctx.fill(); };
  for (const p of world.pads) dot(p.x, p.y, '#ff2e93', 2.5);
  for (const p of world.shops) dot(p.x, p.y, '#a6ff4d', 3);
  for (const p of world.tunnels) dot(p.x, p.y, '#ffb627', 2.5);
  for (const c of cars) if (c.kind === 'police' && c.ai === 'police') dot(c.x, c.y, Math.sin(S.time * 10) > 0 ? '#ff2e4d' : '#2e6bff', 2.5);
  for (const e of enemies) if (e.hp > 0 && e.alert) dot(e.x, e.y, '#ff4d5e', 2);
  for (const c of cars) if (c.ai === 'gang' && !c.wreck) dot(c.x, c.y, '#ff4d5e', 3);
  if (heli) dot(heli.x, heli.y, '#ffffff', 4);
  if (gps.path.length > 1) { const s2 = mini.width / W; mctx.strokeStyle = '#ffd23f'; mctx.lineWidth = 2.4; mctx.beginPath(); gps.path.forEach((q, i) => i ? mctx.lineTo(q.x * s2, q.y * s2) : mctx.moveTo(q.x * s2, q.y * s2)); mctx.stroke(); }
  if (target) dot(target.x, target.y, '#21e6ff', 4.5);
  dot(P.x, P.y, '#ffffff', 3.5);
}

// ---------- rendu 3D (three.js) ----------
const R3 = { ok: false };
const matCache = {}, geoCache = {}, colCache = {};
function mat(col, em) { const k = col + '|' + (em || ''); return matCache[k] || (matCache[k] = new THREE.MeshLambertMaterial({ color: col, emissive: em || '#000000' })); }
function bmat(col, op = 1, add = false) { const k = 'b' + col + op + add; return matCache[k] || (matCache[k] = new THREE.MeshBasicMaterial({ color: col, transparent: op < 1, opacity: op, depthWrite: !add, blending: add ? THREE.AdditiveBlending : THREE.NormalBlending, side: THREE.DoubleSide })); }
function bx(w, h, d) { const k = w + 'x' + h + 'x' + d; return geoCache[k] || (geoCache[k] = new THREE.BoxGeometry(w, h, d)); }
function col3(c) { return colCache[c] || (colCache[c] = new THREE.Color(c)); }
function init3D() {
  if (!window.THREE) return;
  const c3 = $('game3d');
  try {
    const r = new THREE.WebGLRenderer({ canvas: c3, antialias: (devicePixelRatio || 1) < 2, powerPreference: 'high-performance' });
    r.setPixelRatio(Math.min(touch.on ? 1.25 : 1.75, devicePixelRatio || 1));
    R3.r = r;
  } catch (e) { return; }
  const sc = R3.scene = new THREE.Scene();
  R3.cam = new THREE.PerspectiveCamera(46, 1, 10, 5000);
  R3.hemi = new THREE.HemisphereLight(0xa7b0ff, 0x241838, .95); sc.add(R3.hemi);
  const moon = R3.moon = new THREE.DirectionalLight(0xfff0dd, .6); moon.position.set(-400, 900, 300); sc.add(moon); sc.add(moon.target);
  R3.shadow = !touch.on; // ombres réelles sur ordinateur (désactivées automatiquement si la qualité baisse)
  if (R3.shadow) { R3.r.shadowMap.enabled = true; R3.r.shadowMap.type = THREE.PCFSoftShadowMap; moon.castShadow = true; moon.shadow.mapSize.set(2048, 2048); const sc2 = moon.shadow.camera; sc2.left = sc2.bottom = -520; sc2.right = sc2.top = 520; sc2.near = 50; sc2.far = 2400; moon.shadow.bias = -.0015; }
  R3.flash = new THREE.PointLight(0xffd27a, 0, 320, 2); sc.add(R3.flash);
  R3.head = new THREE.SpotLight(0xfff2cc, 0, 620, .55, .6, 1.4); R3.head.target = new THREE.Object3D(); sc.add(R3.head, R3.head.target);
  { const NR = touch.on ? 700 : 1400, rg = new THREE.BufferGeometry(); rg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(NR * 6), 3));
    R3.rain = new THREE.LineSegments(rg, new THREE.LineBasicMaterial({ color: 0xa9c4ff, transparent: true, opacity: .45 })); R3.rain.frustumCulled = false; R3.rain.visible = false; R3.NR = NR; R3.drops = [];
    for (let i = 0; i < NR; i++) R3.drops.push({ x: rnd(-700, 700), y: rnd(0, 400), z: rnd(-700, 700) }); sc.add(R3.rain); }
  { const MS = 260, sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(MS * 3), 3)); sg.setAttribute('color', new THREE.BufferAttribute(new Float32Array(MS * 3), 3));
    R3.smoke = new THREE.Points(sg, new THREE.PointsMaterial({ size: 34, vertexColors: true, transparent: true, opacity: .55, depthWrite: false })); R3.smoke.frustumCulled = false; R3.MS = MS; sc.add(R3.smoke); }
  R3.debris = [];
  { const sg = new THREE.SphereGeometry(4200, 24, 12), cols = []; const pos = sg.attributes.position;
    for (let i = 0; i < pos.count; i++) cols.push(1, 1, 1);
    sg.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
    R3.sky = new THREE.Mesh(sg, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, fog: false, depthWrite: false })); R3.sky.renderOrder = -10; R3.sky.frustumCulled = false; sc.add(R3.sky);
    const NS = 900, sp = new Float32Array(NS * 3); for (let i = 0; i < NS; i++) { const a = Math.random() * TAU, e = Math.random() * 1.3 + .15, r = 3900; sp[i * 3] = Math.cos(a) * Math.cos(e) * r; sp[i * 3 + 1] = Math.sin(e) * r; sp[i * 3 + 2] = Math.sin(a) * Math.cos(e) * r; }
    const stg = new THREE.BufferGeometry(); stg.setAttribute('position', new THREE.BufferAttribute(sp, 3));
    R3.stars = new THREE.Points(stg, new THREE.PointsMaterial({ color: 0xffffff, size: 2.2, sizeAttenuation: false, transparent: true, fog: false, depthWrite: false })); R3.stars.frustumCulled = false; sc.add(R3.stars);
    R3.moonDisk = new THREE.Mesh(new THREE.SphereGeometry(120, 16, 10), new THREE.MeshBasicMaterial({ color: 0xfff6dd, fog: false })); sc.add(R3.moonDisk);
    R3.glow = new THREE.Mesh(new THREE.CircleGeometry(40, 24), new THREE.MeshBasicMaterial({ color: 0x21e6ff, transparent: true, opacity: .45, blending: THREE.AdditiveBlending, depthWrite: false })); R3.glow.rotation.x = -PI / 2; R3.glow.scale.set(1.5, .8, 1); sc.add(R3.glow); }
  R3.dyn = new THREE.Group(); sc.add(R3.dyn);
  R3.seen = new Set();
  const MAXP = 700, pg = new THREE.BufferGeometry();
  pg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(MAXP * 3), 3));
  pg.setAttribute('color', new THREE.BufferAttribute(new Float32Array(MAXP * 3), 3));
  R3.pts = new THREE.Points(pg, new THREE.PointsMaterial({ size: 10, vertexColors: true, transparent: true, opacity: .9, depthWrite: false, blending: THREE.AdditiveBlending }));
  R3.pts.frustumCulled = false; R3.MAXP = MAXP; sc.add(R3.pts);
  R3.bul = new THREE.InstancedMesh(bx(12, 2.5, 2.5), new THREE.MeshBasicMaterial({ color: 0xfff2a8 }), 300);
  R3.bul.instanceMatrix.setUsage(THREE.DynamicDrawUsage); R3.bul.frustumCulled = false; sc.add(R3.bul);
  R3.bulE = new THREE.InstancedMesh(bx(12, 2.5, 2.5), new THREE.MeshBasicMaterial({ color: 0xff5a5a }), 300);
  R3.bulE.instanceMatrix.setUsage(THREE.DynamicDrawUsage); R3.bulE.frustumCulled = false; sc.add(R3.bulE);
  R3.ring = new THREE.Mesh(new THREE.TorusGeometry(38, 3, 8, 40), bmat('#21e6ff', .9)); R3.ring.rotation.x = -PI / 2; sc.add(R3.ring);
  R3.beam = new THREE.Mesh(new THREE.CylinderGeometry(30, 30, 300, 24, 1, true), bmat('#21e6ff', .16, true)); sc.add(R3.beam);
  const cone = new THREE.Mesh(new THREE.ConeGeometry(9, 24, 4), new THREE.MeshBasicMaterial({ color: 0x21e6ff, depthTest: false }));
  cone.rotation.z = -PI / 2; cone.renderOrder = 10;
  R3.arrow = new THREE.Group(); R3.arrow.add(cone); sc.add(R3.arrow);
  R3.me = new THREE.Mesh(new THREE.RingGeometry(20, 24, 28), new THREE.MeshBasicMaterial({ color: 0x21e6ff, depthTest: false, transparent: true, opacity: .85, side: THREE.DoubleSide }));
  R3.me.rotation.x = -PI / 2; R3.me.renderOrder = 11; sc.add(R3.me);
  R3.ray = new THREE.Raycaster(); R3.plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0); R3.hit = new THREE.Vector3(); R3.ndc = new THREE.Vector2();
  R3.m4 = new THREE.Matrix4(); R3.q = new THREE.Quaternion(); R3.v = new THREE.Vector3(); R3.s = new THREE.Vector3(1, 1, 1); R3.up = new THREE.Vector3(0, 1, 0);
  R3.ok = true; cvs.style.display = 'none'; c3.style.display = 'block';
}
function windowTex() {
  const a = document.createElement('canvas'), e = document.createElement('canvas'); a.width = e.width = 64; a.height = e.height = 128;
  const ga = a.getContext('2d'), ge = e.getContext('2d');
  ga.fillStyle = '#8a8a96'; ga.fillRect(0, 0, 64, 128); ge.fillStyle = '#000'; ge.fillRect(0, 0, 64, 128);
  for (let y = 6; y < 124; y += 14) for (let x = 5; x < 60; x += 14) {
    ga.fillStyle = '#3a3a48'; ga.fillRect(x, y, 9, 8);
    const r = Math.random(); if (r < .38) { ge.fillStyle = r < .1 ? '#7fe9ff' : r < .2 ? '#ff9fd0' : '#ffd890'; ge.fillRect(x, y, 9, 8); }
  }
  const m = new THREE.CanvasTexture(a), em = new THREE.CanvasTexture(e);
  return { m, em };
}
function bHeight(tx, ty) {
  const i = ty * N + tx, id = world.region.id;
  if (world.wh[i]) return 44;
  if (id === 'bra' && tileIsFavela(tx, ty)) return 20 + hash(tx, ty) % 26;
  const bx2 = Math.floor(tx / B), by2 = Math.floor(ty / B), side = (tx % B) > 5 ? 1 : 0;
  const r = hash(bx2 * 7 + side * 3, by2 * 13 + 5) / 1000;
  const [lo, hi] = id === 'usa' ? [50, 130] : id === 'ita' ? [40, 90] : id === 'col' ? [30, 70] : [36, 80];
  return lo + r * (hi - lo);
}
function build3DWorld() {
  const sc = R3.scene;
  if (R3.static) { sc.remove(R3.static); R3.static.traverse(o => { if (o.geometry && !o.geometry.parameters) o.geometry.dispose(); }); }
  const g = R3.static = new THREE.Group(); R3.world = world;
  const p = world.region.pal;
  sc.background = new THREE.Color(p.ground); sc.fog = new THREE.Fog(p.ground, 1150, 2700);
  // sol peint avec les mêmes tuiles que la version 2D
  const S = touch.on ? 24 : 32, gc = document.createElement('canvas'); gc.width = gc.height = N * S;
  const gx = gc.getContext('2d'), saved = ctx; ctx = gx; gx.setTransform(S / T, 0, 0, S / T, 0, 0);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) drawTile(x, y);
  ctx = saved;
  const tex = new THREE.CanvasTexture(gc); tex.anisotropy = Math.min(8, R3.r.capabilities.getMaxAnisotropy());
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(W, W), new THREE.MeshLambertMaterial({ map: tex }));
  ground.rotation.x = -PI / 2; ground.position.set(W / 2, 0, W / 2); ground.receiveShadow = true; g.add(ground);
  // immeubles
  const tiles = []; for (let ty = 0; ty < N; ty++) for (let tx = 0; tx < N; tx++) if (world.map[ty * N + tx] === BLD && !world.lm[ty * N + tx]) tiles.push([tx, ty]);
  const wt = R3.wt || (R3.wt = windowTex());
  const side = R3.sideMat = new THREE.MeshLambertMaterial({ map: wt.m, emissiveMap: wt.em, emissive: 0xffffff, emissiveIntensity: .85 });
  const roof = new THREE.MeshLambertMaterial({ color: 0xffffff });
  const im = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), [side, side, roof, roof, side, side], tiles.length);
  const c = new THREE.Color();
  tiles.forEach(([tx, ty], i) => {
    const h = bHeight(tx, ty), k = ty * N + tx;
    R3.v.set(tx * T + T / 2, h / 2, ty * T + T / 2); R3.s.set(T, h, T); R3.q.identity();
    R3.m4.compose(R3.v, R3.q, R3.s); im.setMatrixAt(i, R3.m4);
    const lk = world.region.look || {};
    if (world.wh[k]) c.set('#55545f');
    else if (lk.glass && h > 105) c.set(lk.glass);
    else if (lk.facades) { c.set(lk.facades[(world.bcol[k] + (hash(tx, ty) % 3 === 0 ? 1 : 0)) % lk.facades.length]); c.multiplyScalar(.72); }
    else { c.set(p.bld[(world.bcol[k] + (hash(tx, ty) & 1)) % p.bld.length]); c.offsetHSL(0, 0, .12); }
    im.setColorAt(i, c);
  });
  R3.s.set(1, 1, 1);
  im.castShadow = true; im.receiveShadow = true; g.add(im); R3.bldMesh = im;
  // néons sur les toits (bordures lumineuses autour des blocs)
  const LK = world.region.look || {};
  const neonTiles = (LK.roof === 'tile' ? [] : tiles).filter(([tx, ty]) => [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => world.map[(ty + dy) * N + tx + dx] !== BLD));
  const nm = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshBasicMaterial({ color: 0xffffff }), neonTiles.length);
  neonTiles.forEach(([tx, ty], i) => {
    const h = bHeight(tx, ty), k = ty * N + tx;
    R3.v.set(tx * T + T / 2, h - 2.2, ty * T + T / 2); R3.s.set(T + 4, 3.4, T + 4); R3.m4.compose(R3.v, R3.q, R3.s); nm.setMatrixAt(i, R3.m4);
    nm.setColorAt(i, c.set(world.wh[k] ? '#8b8a96' : p.neon[world.bcol[k] % p.neon.length]));
  });
  R3.s.set(1, 1, 1); g.add(nm);
  buildRegionDecor(g, tiles);
  // arbres (les essences dépendent du pays)
  const trees = []; for (let ty = 0; ty < N; ty++) for (let tx = 0; tx < N; tx++) { const t = world.map[ty * N + tx]; if (world.lm[ty * N + tx]) continue; if (t === TREE || (t === PARK && hash(tx, ty) % 4 === 0)) trees.push([tx, ty, t === TREE]); }
  const kindOf = (tx, ty) => { const h = hash(tx * 3, ty * 7) % 10, ts = LK.trees; return ts === 'palm' ? 'palm' : ts === 'cypress' ? (h < 7 ? 'cypress' : 'round') : ts === 'jungle' ? (h < 6 ? 'round' : 'palm') : 'cone'; };
  const groups = { palm: [], cypress: [], round: [], cone: [] };
  for (const tr of trees) groups[kindOf(tr[0], tr[1])].push(tr);
  const inst = (geo, m, list, fn) => { if (!list.length) return; const im2 = new THREE.InstancedMesh(geo, m, list.length); list.forEach((tr, i) => { fn(tr); R3.m4.compose(R3.v, R3.q, R3.s); im2.setMatrixAt(i, R3.m4); }); g.add(im2); };
  const pos = (tr, y, sx, sy, sz) => { const s2 = tr[2] ? 1 : .75; R3.v.set(tr[0] * T + 32 + (hash(tr[0], tr[1]) % 9 - 4), y * s2, tr[1] * T + 32); R3.s.set(sx * s2, sy * s2, sz * s2); };
  inst(cyl(1, 1.3, 1, 6), mat('#6b4a2a'), groups.palm, tr => pos(tr, 34, 3.5, 68, 3.5));
  inst(new THREE.ConeGeometry(1, 1, 8), mat('#2f8a3a'), groups.palm, tr => pos(tr, 66, 34, 10, 34));
  inst(new THREE.ConeGeometry(1, 1, 8), mat('#1f6a2c'), groups.palm, tr => pos(tr, 72, 16, 12, 16));
  inst(new THREE.ConeGeometry(1, 1, 7), mat('#24452c'), groups.cypress, tr => pos(tr, 38, 11, 76, 11));
  inst(cyl(1, 1.3, 1, 6), mat('#4a3424'), groups.round, tr => pos(tr, 12, 4, 24, 4));
  inst(new THREE.IcosahedronGeometry(1, 0), mat(p.tree), groups.round, tr => pos(tr, 38, 26, 22, 26));
  inst(bx(1, 1, 1), mat('#3b2a1e'), groups.cone, tr => pos(tr, 14, 6, 28, 6));
  inst(new THREE.ConeGeometry(1, 1, 7), mat(p.tree), groups.cone, tr => pos(tr, 44, 24, 50, 24));
  R3.s.set(1, 1, 1);
  // colonnes de lumière : boutique, tunnels, peinture, garages, hôpital, police
  R3.beacons = [];
  const beam = (pt, colr, h = 150) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(22, 22, h, 18, 1, true), bmat(colr, .2, true)); m.position.set(pt.x, h / 2, pt.y); g.add(m); R3.beacons.push(m); };
  world.shops.forEach(s => beam(s, '#a6ff4d')); world.tunnels.forEach(s => beam(s, '#ffb627', 110)); world.pads.forEach(s => beam(s, '#ff2e93', 110));
  world.garages.forEach(s => beam(s, '#3ee0c5', 110)); beam(world.hospital, '#a6ff4d', 90); beam(world.station, '#2e6bff', 90);
  sc.add(g);
}
// ---- décor propre à chaque pays : toits, réservoirs, bords de carte, monuments, lampadaires
function prismGeo() {
  if (geoCache.prism) return geoCache.prism;
  const g = new THREE.BufferGeometry();
  const v = [-.5, 0, -.5, .5, 0, -.5, .5, 1, 0, -.5, 1, 0, -.5, 0, .5, .5, 0, .5];
  const idx = [0, 3, 1, 1, 3, 2, 4, 5, 3, 5, 2, 3, 0, 4, 3, 1, 2, 5, 0, 1, 4, 1, 5, 4];
  g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3)); g.setIndex(idx); g.computeVertexNormals();
  return (geoCache.prism = g);
}
function buildRegionDecor(g, tiles) {
  const LK = world.region.look || {}, id = world.region.id; R3.anim = [];
  const c = new THREE.Color();
  // toits de tuiles
  if (LK.roof === 'tile') {
    const list = tiles.filter(([tx, ty]) => !world.wh[ty * N + tx]);
    const im = new THREE.InstancedMesh(prismGeo(), new THREE.MeshLambertMaterial({ color: 0xffffff, flatShading: true, side: THREE.DoubleSide }), list.length);
    list.forEach(([tx, ty], i) => { const h = bHeight(tx, ty), rot = (Math.floor(tx / B) + Math.floor(ty / B)) % 2 ? PI / 2 : 0;
      R3.v.set(tx * T + T / 2, h, ty * T + T / 2); R3.q.setFromAxisAngle(R3.up, rot); R3.s.set(T + 3, 15, T + 3); R3.m4.compose(R3.v, R3.q, R3.s); im.setMatrixAt(i, R3.m4);
      c.set(LK.roofColor); c.offsetHSL(0, 0, (hash(tx, ty) % 10 - 5) / 100); im.setColorAt(i, c); });
    R3.q.identity(); R3.s.set(1, 1, 1); g.add(im);
  }
  // réservoirs d'eau bleus sur les toits des favelas
  if (id === 'bra') {
    const list = tiles.filter(([tx, ty]) => hash(tx, ty) % 2 === 0);
    const im = new THREE.InstancedMesh(cyl(6, 6, 9, 10), mat('#2b6cb0'), list.length);
    list.forEach(([tx, ty], i) => { R3.v.set(tx * T + 20 + hash(tx, ty) % 24, bHeight(tx, ty) + 4.5, ty * T + 20 + hash(ty, tx) % 24); R3.m4.compose(R3.v, R3.q, R3.s); im.setMatrixAt(i, R3.m4); });
    g.add(im);
  }
  // sol autour de la ville, mer, plage, montagnes
  const outer = new THREE.Mesh(new THREE.PlaneGeometry(W * 4, W * 4), mat(LK.ground || '#2a2433')); outer.rotation.x = -PI / 2; outer.position.set(W / 2, -1.5, W / 2); g.add(outer);
  const water = new THREE.MeshLambertMaterial({ color: world.region.pal.water, emissive: '#0a2a44', transparent: true, opacity: .95 });
  const sand = mat('#e6d3a3');
  const E = LK.edges || {};
  const side = (k, depth, m, y) => { const pl = new THREE.Mesh(new THREE.PlaneGeometry(k === 'n' || k === 's' ? W * 3 : depth, k === 'n' || k === 's' ? depth : W * 3), m); pl.rotation.x = -PI / 2; return pl; };
  for (const [k, kind] of Object.entries(E)) {
    if (kind === 'sea' || kind === 'beach') {
      const sandW = kind === 'beach' ? 320 : 0, seaD = 2600;
      if (sandW) { const b = side(k, sandW, sand); b.position.set(k === 'e' ? W + sandW / 2 : k === 'w' ? -sandW / 2 : W / 2, -.8, k === 's' ? W + sandW / 2 : k === 'n' ? -sandW / 2 : W / 2); g.add(b); }
      const w = side(k, seaD, water); w.position.set(k === 'e' ? W + sandW + seaD / 2 : k === 'w' ? -sandW - seaD / 2 : W / 2, -.6, k === 's' ? W + sandW + seaD / 2 : k === 'n' ? -sandW - seaD / 2 : W / 2); g.add(w);
      R3.anim.push(() => { w.material.emissive.setHSL(.58, .6, .08 + .03 * Math.sin(S.time * .8)); });
      if (kind === 'beach') { // parasols
        for (let i = 0; i < 26; i++) { const along = 200 + i * (W - 400) / 25 + hash(i, 3) % 60, off = 80 + hash(i, 9) % 180;
          const px = k === 'e' ? W + off : k === 'w' ? -off : along, pz = k === 's' ? W + off : k === 'n' ? -off : along;
          const pole = new THREE.Mesh(cyl(1, 1, 30, 5), mat('#f2f2f2')); pole.position.set(px, 15, pz); g.add(pole);
          const top = new THREE.Mesh(new THREE.ConeGeometry(22, 9, 8), mat(pick(['#ff2e93', '#ffd23f', '#21e6ff', '#ffffff', '#7ac74f']))); top.position.set(px, 32, pz); g.add(top); }
      }
    } else if (kind === 'mountains') {
      const greens = ['#3f6b35', '#4f7d3a', '#5b6b3a', '#6b5e45', '#355e3b'];
      for (let i = 0; i < 9; i++) { const along = -400 + i * (W + 800) / 8 + (hash(i, k.charCodeAt(0)) % 200), dd = 700 + hash(k.charCodeAt(0), i) % 600, r = 420 + hash(i * 7, 2) % 380, h = 380 + hash(i * 5, 11) % 520;
        const m = new THREE.Mesh(new THREE.ConeGeometry(r, h, 7), new THREE.MeshLambertMaterial({ color: greens[i % greens.length], flatShading: true }));
        m.position.set(k === 'e' ? W + dd : k === 'w' ? -dd : along, h / 2 - 10, k === 's' ? W + dd : k === 'n' ? -dd : along); m.rotation.y = i; g.add(m); }
    }
  }
  // lampadaires au bord des trottoirs
  const lamps = [];
  for (let ty = 1; ty < N - 1; ty++) for (let tx = 1; tx < N - 1; tx++) { if (world.map[ty * N + tx] !== WALK || hash(tx, ty) % 3) continue;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) if (world.map[(ty + dy) * N + tx + dx] === ROAD) { lamps.push([tx * T + T / 2 + dx * 26, ty * T + T / 2 + dy * 26]); break; } }
  const poleM = new THREE.InstancedMesh(cyl(1.3, 1.8, 48, 5), mat('#2a2830'), lamps.length), bulbM = new THREE.InstancedMesh(sph(3.4, 6, 4), new THREE.MeshBasicMaterial({ color: LK.lamp || '#fff2cc' }), lamps.length);
  lamps.forEach(([x, z], i) => { R3.v.set(x, 24, z); R3.m4.compose(R3.v, R3.q, R3.s); poleM.setMatrixAt(i, R3.m4); R3.v.set(x, 49, z); R3.m4.compose(R3.v, R3.q, R3.s); bulbM.setMatrixAt(i, R3.m4); });
  g.add(poleM, bulbM);
  { const hc = document.createElement('canvas'); hc.width = hc.height = 64; const hx = hc.getContext('2d'), gr = hx.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(.3, 'rgba(255,255,255,.45)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); hx.fillStyle = gr; hx.fillRect(0, 0, 64, 64);
    const pa = new Float32Array(lamps.length * 3); lamps.forEach(([x, z], i) => { pa[i * 3] = x; pa[i * 3 + 1] = 49; pa[i * 3 + 2] = z; });
    const hg = new THREE.BufferGeometry(); hg.setAttribute('position', new THREE.BufferAttribute(pa, 3));
    R3.halos = new THREE.Points(hg, new THREE.PointsMaterial({ map: new THREE.CanvasTexture(hc), color: LK.lamp || '#fff2cc', size: 70, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: .6 })); g.add(R3.halos); }
  // monuments
  for (const L2 of world.landmarks) buildLandmark(g, L2, LK);
  buildSigns(g);
}
const SIGNS = { usa: ['MOTEL', 'PIZZA', 'CLUB', '24/7', 'BAR', 'TATTOO', 'DINER', 'ARCADE'], ita: ['PIZZERIA', 'GELATO', 'CAFFÈ', 'HOTEL', 'BAR', 'TRATTORIA'], col: ['CAFÉ', 'TIENDA', 'HOTEL', 'AREPAS', 'FARMACIA', 'BAR'], bra: ['BAR', 'AÇAÍ', 'LANCHES', 'HOTEL', 'BAILE', 'SALÃO'] };
function signMat(word, col) {
  const k = 'sign|' + word + '|' + col; if (matCache[k]) return matCache[k];
  const cv = document.createElement('canvas'); cv.width = 256; cv.height = 64; const x = cv.getContext('2d');
  x.fillStyle = 'rgba(8,6,16,.85)'; x.fillRect(0, 0, 256, 64); x.strokeStyle = col; x.lineWidth = 4; x.strokeRect(4, 4, 248, 56);
  x.font = '900 38px "Bungee", "Arial Black", sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.shadowColor = col; x.shadowBlur = 14; x.fillStyle = '#ffffff'; x.fillText(word, 128, 34); x.fillStyle = col; x.globalAlpha = .55; x.fillText(word, 128, 34);
  return (matCache[k] = new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(cv), side: THREE.DoubleSide }));
}
function buildSigns(g) {
  const words = SIGNS[world.region.id] || SIGNS.usa, neon = world.region.pal.neon; let n = 0; const flick = [];
  for (let ty = 2; ty < N - 2 && n < 70; ty++) for (let tx = 2; tx < N - 2 && n < 70; tx++) {
    const k = ty * N + tx; if (world.map[k] !== BLD || world.lm[k] || world.wh[k] || hash(tx * 5, ty * 3) % 9) continue;
    for (const [dx, dy] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
      const nt = world.map[(ty + dy) * N + tx + dx]; if (nt === BLD) continue;
      const h = bHeight(tx, ty), y = Math.min(h - 10, 26 + hash(tx, ty) % 18); if (y < 18) break;
      const w = words[hash(tx, ty) % words.length], col = neon[hash(ty, tx) % neon.length];
      const m = new THREE.Mesh(new THREE.PlaneGeometry(52, 13), signMat(w, col));
      m.position.set(tx * T + T / 2 + dx * (T / 2 + 1.5), y, ty * T + T / 2 + dy * (T / 2 + 1.5)); m.rotation.y = dx ? (dx > 0 ? PI / 2 : -PI / 2) : (dy > 0 ? 0 : PI);
      g.add(m); n++; if (hash(tx, ty) % 5 === 0) flick.push(m); break;
    }
  }
  if (flick.length) R3.anim.push(() => { for (const m of flick) m.visible = Math.sin(S.time * 7 + m.position.x) > -.85 || Math.random() < .5; });
}
function buildLandmark(g, L2, LK) {
  const add = (geo, m, x, y, z, parent = g) => { const me = new THREE.Mesh(geo, m); me.position.set(x, y, z); parent.add(me); return me; };
  const id = L2.id, x = L2.x, z = L2.y;
  if (id === 'tower') { // flèche lumineuse sur la plus haute tour
    let best = null, bh = 0; for (let ty = 2; ty < N - 2; ty++) for (let tx = 2; tx < N - 2; tx++) { const k = ty * N + tx; if (world.map[k] === BLD && !world.lm[k] && !world.wh[k]) { const h = bHeight(tx, ty); if (h > bh) { bh = h; best = [tx, ty]; } } }
    if (!best) return; const bxp = best[0] * T + T / 2, bzp = best[1] * T + T / 2;
    add(cyl(14, 22, 30, 8), mat('#2b3d63'), bxp, bh + 15, bzp); add(cyl(2, 6, 150, 6), mat('#c9d6ff'), bxp, bh + 105, bzp);
    const red = add(sph(5, 8, 6), new THREE.MeshBasicMaterial({ color: 0xff2e4d }), bxp, bh + 185, bzp);
    const ring = add(new THREE.TorusGeometry(26, 2, 6, 24), new THREE.MeshBasicMaterial({ color: 0xff2e93 }), bxp, bh + 40, bzp); ring.rotation.x = PI / 2;
    R3.anim.push(() => { red.visible = Math.sin(S.time * 3) > 0; });
  } else if (id === 'wheel') { // grande roue sur la plage
    const wx = W * .62, wz = W + 170, grp = new THREE.Group(); grp.position.set(wx, 130, wz); g.add(grp);
    const neon = new THREE.MeshBasicMaterial({ color: 0xff2e93 });
    grp.add(new THREE.Mesh(new THREE.TorusGeometry(110, 3, 6, 48), neon));
    for (let i = 0; i < 12; i++) { const sp = new THREE.Mesh(bx(220, 2, 2), mat('#d8d8e0')); sp.rotation.z = i * PI / 12; grp.add(sp); }
    for (let i = 0; i < 16; i++) { const a = i / 16 * TAU, cab = new THREE.Mesh(bx(14, 14, 14), mat(['#21e6ff', '#ffd23f', '#ff2e93', '#a6ff4d'][i % 4])); cab.position.set(Math.cos(a) * 110, Math.sin(a) * 110, 0); grp.add(cab); }
    for (const s2 of [-1, 1]) { const leg = add(bx(6, 140, 6), mat('#9aa0b5'), wx + s2 * 40, 65, wz); leg.rotation.z = s2 * .3; }
    R3.anim.push(dt => { grp.rotation.z += dt * .12; neon.color.setHSL((S.time * .05) % 1, 1, .6); });
  } else if (id === 'stadium') {
    add(new THREE.CylinderGeometry(118, 108, 42, 28, 1, true), new THREE.MeshLambertMaterial({ color: '#c9c9d4', side: THREE.DoubleSide }), x, 21, z);
    const f = add(new THREE.PlaneGeometry(170, 110), mat('#3fa34d')); f.rotation.x = -PI / 2; f.position.y = 1;
    for (const [dx, dz] of [[-110, -110], [110, -110], [-110, 110], [110, 110]]) { add(cyl(2, 2, 90, 5), mat('#55555f'), x + dx, 45, z + dz); add(bx(16, 8, 4), new THREE.MeshBasicMaterial({ color: 0xffffff }), x + dx, 92, z + dz); }
  } else if (id === 'campanile') {
    add(bx(46, 170, 46), mat('#d9a28b'), x, 85, z);
    for (const [dx, dz] of [[23.5, 0], [-23.5, 0], [0, 23.5], [0, -23.5]]) add(bx(dx ? 1 : 18, 26, dx ? 18 : 1), mat('#2a1a14'), x + dx, 150, z + dz);
    add(new THREE.ConeGeometry(36, 44, 4), mat(LK.roofColor || '#b5562f'), x, 192, z).rotation.y = PI / 4;
  } else if (id === 'dome') {
    add(bx(230, 62, 230), mat('#efe3c8'), x, 31, z);
    add(cyl(78, 78, 34, 20), mat('#e3d2ad'), x, 79, z);
    add(sph(80, 20, 12, true), mat('#6fa58a'), x, 96, z);
    add(cyl(10, 12, 26, 10), mat('#efe3c8'), x, 186, z); add(new THREE.ConeGeometry(12, 16, 10), mat('#6fa58a'), x, 207, z);
  } else if (id === 'church') {
    add(bx(200, 70, 130), mat('#f4f1ea'), x + 20, 35, z);
    const roof = add(prismGeo(), new THREE.MeshLambertMaterial({ color: LK.roofColor || '#a8432a', side: THREE.DoubleSide }), x + 20, 70, z); roof.scale.set(204, 32, 134);
    for (const dz of [-50, 50]) { add(bx(54, 150, 54), mat('#f4f1ea'), x - 92, 75, z + dz); add(new THREE.ConeGeometry(34, 46, 4), mat(LK.roofColor || '#a8432a'), x - 92, 173, z + dz).rotation.y = PI / 4; add(bx(2, 26, 16), mat('#2a1a14'), x - 64.5, 125, z + dz); }
  } else if (id === 'plantation') {
    const list = []; for (let r = 0; r < 7; r++) for (let q = 0; q < 9; q++) list.push([x - 112 + q * 28, z - 96 + r * 32]);
    const im = new THREE.InstancedMesh(sph(11, 7, 5), mat('#2f6b2a'), list.length);
    list.forEach(([px, pz], i) => { R3.v.set(px, 9, pz); R3.m4.compose(R3.v, R3.q, R3.s); im.setMatrixAt(i, R3.m4); }); g.add(im);
  } else if (id === 'rock') { // grand rocher au-dessus de la ville
    const r1 = add(sph(1, 14, 10), new THREE.MeshLambertMaterial({ color: '#6b5e55', flatShading: true }), W * .38, 260, -900); r1.scale.set(330, 560, 300);
    const r2 = add(sph(1, 12, 8), new THREE.MeshLambertMaterial({ color: '#5e544c', flatShading: true }), W * .72, 150, -760); r2.scale.set(260, 320, 240);
    const cap = add(sph(1, 12, 8, true), mat('#3f6b35'), W * .38, -2, -900); cap.scale.set(420, 170, 380);
  } else if (id === 'cablecar') { // téléphérique entre le rocher et la ville
    const pts = [new THREE.Vector3(W * .38, 520, -760), new THREE.Vector3(W * .4, 300, W * .15), new THREE.Vector3(W * .45, 220, W * .45)];
    for (let i = 1; i < pts.length; i++) { const a = pts[i - 1], b = pts[i], mid = a.clone().add(b).multiplyScalar(.5), len = a.distanceTo(b);
      const cable = add(cyl(1.2, 1.2, len, 4), mat('#222228'), mid.x, mid.y, mid.z); cable.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize()); }
    for (const pnt of pts.slice(1)) add(bx(14, pnt.y, 14), mat('#8a8f9e'), pnt.x, pnt.y / 2, pnt.z);
    const gondolas = []; for (let i = 0; i < 5; i++) { const gd = add(bx(22, 18, 16), mat(i % 2 ? '#e8402e' : '#ffd23f'), 0, 0, 0); gondolas.push(gd); }
    R3.anim.push(() => { gondolas.forEach((gd, i) => { const u = ((S.time * .03 + i / 5) % 1) * (pts.length - 1), k = Math.min(pts.length - 2, Math.floor(u)), f = u - k; gd.position.lerpVectors(pts[k], pts[k + 1], f); gd.position.y -= 14; }); });
  } else if (id === 'pitch') {
    const cv = document.createElement('canvas'); cv.width = 220; cv.height = 140; const cx = cv.getContext('2d');
    cx.fillStyle = '#2f8a3a'; cx.fillRect(0, 0, 220, 140); for (let i = 0; i < 11; i++) { cx.fillStyle = i % 2 ? '#2f8a3a' : '#349a40'; cx.fillRect(i * 20, 0, 20, 140); }
    cx.strokeStyle = '#ffffff'; cx.lineWidth = 2; cx.strokeRect(6, 6, 208, 128); cx.beginPath(); cx.moveTo(110, 6); cx.lineTo(110, 134); cx.stroke(); cx.beginPath(); cx.arc(110, 70, 18, 0, TAU); cx.stroke(); cx.strokeRect(6, 40, 26, 60); cx.strokeRect(188, 40, 26, 60);
    const f = add(new THREE.PlaneGeometry(220, 140), new THREE.MeshLambertMaterial({ map: new THREE.CanvasTexture(cv) }), x, 1, z); f.rotation.x = -PI / 2;
    for (const sx of [-1, 1]) { add(bx(2, 16, 2), mat('#ffffff'), x + sx * 104, 8, z - 14); add(bx(2, 16, 2), mat('#ffffff'), x + sx * 104, 8, z + 14); add(bx(2, 2, 30), mat('#ffffff'), x + sx * 104, 16, z); }
  }
}
// ---- personnages en blocs
function cyl(rt, rb, h, seg = 7) { const k = 'c' + rt + '|' + rb + '|' + h + '|' + seg; return geoCache[k] || (geoCache[k] = new THREE.CylinderGeometry(rt, rb, h, seg)); }
function sph(r, ws = 9, hs = 7, half) { const k = 's' + r + '|' + ws + '|' + hs + '|' + (half || 0); return geoCache[k] || (geoCache[k] = half ? new THREE.SphereGeometry(r, ws, hs, 0, PI * 2, 0, PI / 2) : new THREE.SphereGeometry(r, ws, hs)); }
// Personnage humain low-poly : hanches, genoux, épaules, coudes, cou, visage. Face au +x.
// ---- armes en 3D (un modèle par arme, peinture au choix), construites le long de +x, poignée à l'origine
const SKINS = [['black', 'Noir mat', 0, '#16161c'], ['chrome', 'Chrome', 800, '#cfd3dc'], ['camo', 'Camouflage', 1200, '#4b5320'], ['neon', 'Rose néon', 2000, '#ff2e93'], ['cyan', 'Cyan néon', 2000, '#21e6ff'], ['gold', 'Or', 6000, '#d4a017']];
function makeGun(id, skin) {
  const g = new THREE.Group(), sk = (SKINS.find(s => s[0] === skin) || SKINS[0])[3];
  const body = mat(sk, skin === 'neon' || skin === 'cyan' ? sk : skin === 'gold' ? '#4a3500' : null), dark = mat('#0c0c10'), wood = mat('#6b4a2a');
  const add = (geo, m, x, y, z, rz = 0) => { const me = new THREE.Mesh(geo, m); me.position.set(x, y, z); me.rotation.z = rz; g.add(me); return me; };
  const barrel = (len, r, x, y = 0) => { const b = add(cyl(r, r, len, 8), dark, x, y, 0); b.rotation.z = PI / 2; return b; };
  switch (id) {
    case 'pistol': add(bx(8, 2.2, 1.5), body, 3, 1.2, 0); add(bx(2, 4, 1.4), dark, 0, -1, 0, .25); barrel(1.5, .5, 7.6, 1.2); break;
    case 'uzi': add(bx(9, 3, 1.8), body, 2.5, 1.2, 0); add(bx(1.5, 6, 1.3), dark, 1.5, -2.4, 0, .1); add(bx(2, 3.5, 1.3), dark, -1, -1, 0, .3); barrel(3, .6, 8, 1.4); break;
    case 'shotgun': barrel(18, .75, 10, 1.4); add(bx(7, 1.8, 1.8), wood, 6, .2, 0); add(bx(6, 2.6, 1.6), body, 0, 1, 0); add(bx(7, 3, 1.4), wood, -6, .3, 0, -.12); add(bx(1.8, 3.4, 1.2), dark, -1, -1.4, 0, .3); break;
    case 'rifle': add(bx(12, 3, 1.8), body, 2, 1.2, 0); barrel(9, .55, 12, 1.5); add(bx(1.6, 5.5, 1.2), dark, 3, -2, 0, -.25); add(bx(6, 2.6, 1.4), body, -6, .8, 0, -.08); add(bx(1.8, 3.4, 1.2), dark, -.5, -1.3, 0, .3); add(bx(4, 1, 1), dark, 2, 3.2, 0); break;
    case 'sniper': add(bx(13, 2.6, 1.6), body, 1.5, 1, 0); barrel(18, .5, 16, 1.3); add(cyl(1.2, 1.2, 8, 10), dark, 2, 3.8, 0, PI / 2); add(bx(7, 3, 1.4), body, -7, .4, 0, -.1); add(bx(1.8, 3.4, 1.2), dark, -1, -1.4, 0, .3); add(bx(1.4, 4, 1.2), dark, 4, -1.4, 0); break;
    case 'rocket': { const t = add(cyl(2.3, 2.3, 26, 12), body, 6, 2.5, 0); t.rotation.z = PI / 2; add(cyl(2.8, 2.3, 3, 12), dark, 19.5, 2.5, 0, PI / 2); add(bx(2, 4, 1.4), dark, 0, -.8, 0, .2); add(bx(3, 2, 1.2), dark, 4, 5.4, 0); break; }
    case 'minigun': for (let k = 0; k < 6; k++) { const a = k / 6 * TAU, b = barrel(16, .45, 12, 1.4 + Math.sin(a) * 1.4); b.position.z = Math.cos(a) * 1.4; } add(bx(8, 4.5, 4), body, 1, 1.4, 0); add(cyl(2.6, 2.6, 1.5, 10), dark, 5, 1.4, 0, PI / 2); add(bx(2, 4, 1.4), dark, -2, -1.6, 0, .2); add(bx(5, 1.2, 1.2), dark, 1, 4.6, 0); break;
    default: return null;
  }
  g.userData.twoHand = ['shotgun', 'rifle', 'sniper', 'rocket', 'minigun', 'uzi'].includes(id);
  return g;
}
// ---- personnages articulés : bassin, taille, cou, épaules, coudes, poignets, hanches, genoux, chevilles
function makeChar(o) {
  const g = new THREE.Group(), F = !!o.female, detail = [];
  const add = (geo, m, x, y, z, parent = g) => { const me = new THREE.Mesh(geo, m); me.position.set(x, y, z); parent.add(me); return me; };
  const joint = (parent, x, y, z) => { const p = new THREE.Group(); p.position.set(x, y, z); parent.add(p); return p; };
  const pants = mat(o.pants || '#1d1a2e'), shirt = mat(o.shirt), sleeve = mat(o.sleeve || o.shirt), skin = mat(o.skin), shoes = mat(o.shoes || '#0c0b12'), dark = mat('#0b0a12');
  const root = joint(g, 0, 0, 0);                       // tout le corps (chute, sursaut)
  const pelvis = joint(root, 0, 15.5, 0);
  // jambes
  const legs = [];
  for (const side of [-1, 1]) {
    const hip = joint(pelvis, 0, 0, side * (F ? 2.3 : 2.5));
    add(cyl(F ? 2.5 : 2.6, 2.1, 8), pants, 0, -4, 0, hip);
    const knee = joint(hip, 0, -8, 0);
    add(sph(2.05, 7, 5), o.skirt || o.shorts ? skin : pants, 0, 0, 0, knee);
    add(cyl(2.05, 1.6, 7.2), o.skirt || o.shorts ? skin : pants, 0, -3.6, 0, knee);
    const ankle = joint(knee, 0, -7.4, 0);
    add(bx(5.4, 1.9, 3.4), shoes, 1.1, -.3, 0, ankle); add(bx(5.6, .5, 3.6), mat('#e8e8ee'), 1.1, -1.2, 0, ankle);
    legs.push({ hip, knee, ankle });
  }
  add(cyl(F ? 4.6 : 4.3, F ? 4.9 : 4.4, 3.2, 10), pants, 0, .9, 0, pelvis).scale.set(.75, 1, 1);
  add(cyl(F ? 4.5 : 4.4, F ? 4.5 : 4.4, .9, 10), mat('#1a1410'), 0, 2.2, 0, pelvis).scale.set(.77, 1, 1);  // ceinture
  if (o.skirt) add(cyl(4.6, 6.4, 6, 10), mat(o.skirt), 0, -1.9, 0, pelvis).scale.set(.85, 1, 1);
  // buste articulé à la taille
  const chest = joint(pelvis, 0, 2.4, 0);
  const torso = add(cyl(F ? 4.7 : 5.4, F ? 3.9 : 4.3, 11, 10), shirt, 0, 5.6, 0, chest); torso.scale.set(.66, 1, 1);
  if (F) { add(sph(1.9, 7, 5), shirt, 2.2, 7.4, -1.7, chest); add(sph(1.9, 7, 5), shirt, 2.2, 7.4, 1.7, chest); }
  if (o.jacket) { const jm = mat(o.jacket); const j = add(cyl(F ? 5 : 5.7, F ? 4.3 : 4.7, 10.6, 10), jm, -.35, 5.8, 0, chest); j.scale.set(.68, 1, 1.02);
    add(bx(.5, 9, 1.4), jm, 3.5, 6, -1.8, chest).rotation.x = .12; add(bx(.5, 9, 1.4), jm, 3.5, 6, 1.8, chest).rotation.x = -.12; }
  add(new THREE.TorusGeometry(1.9, .45, 5, 12), o.jacket ? mat(o.jacket) : shirt, 0, 11.3, 0, chest).rotation.x = PI / 2;   // col
  if (o.tie) add(bx(.5, 7, 1.4), mat(o.tie), 3.65, 6.7, 0, chest);
  if (o.chain) { const c = add(new THREE.TorusGeometry(3.3, .45, 5, 12), mat('#ffd700', '#7a5a00'), 1.2, 9.8, 0, chest); c.rotation.y = PI / 2; c.rotation.x = .25; }
  const neck = joint(chest, 0, 11.4, 0);
  add(cyl(1.5, 1.7, 2.4, 8), skin, 0, .6, 0, neck);
  // tête
  const headJ = joint(neck, 0, 1.6, 0);
  const head = add(sph(4.1, 12, 9), skin, 0, 3.6, 0, headJ); head.scale.set(.95, 1.08, .9);
  for (const s2 of [-1, 1]) {
    add(sph(1, 6, 5), skin, -.2, 3.6, s2 * 3.7, headJ).scale.set(.6, 1.2, .5);  // oreilles
    detail.push(add(sph(.85, 6, 4), mat('#f4f1ea'), 3.35, 4.1, s2 * 1.45, headJ));
    detail.push(add(sph(.48, 5, 4), mat('#17110c'), 4.05, 4.1, s2 * 1.45, headJ));
    detail.push(add(bx(.5, .45, 1.7), mat(o.hair || '#2a1d14'), 3.7, 5.3, s2 * 1.5, headJ));
  }
  detail.push(add(bx(1.1, 1.4, .9), skin, 4, 3.1, 0, headJ));
  detail.push(add(bx(.4, .45, 2), mat('#7a3a3a'), 3.75, 1.6, 0, headJ));
  const hs = o.hairStyle || (o.hair ? (F ? 'long' : 'short') : 'none');
  if (o.hair && hs !== 'none' && !o.hat) {
    const hm = mat(o.hair);
    const cap = add(sph(4.45, 12, 7, true), hm, -.35, 4.4, 0, headJ); cap.scale.set(1, 1.05, .95);
    if (hs === 'long') add(bx(2.6, 7.5, 8), hm, -3.2, 1.2, 0, headJ);
    else if (hs === 'ponytail') { add(sph(1.8, 6, 5), hm, -4.6, 3.8, 0, headJ); add(cyl(1.2, .7, 5, 6), hm, -5.2, 1.4, 0, headJ); }
    else if (hs === 'afro') add(sph(5.3, 10, 8), hm, -.6, 5.2, 0, headJ);
  }
  if (o.hat) {
    const hm = mat(o.hat), ht = o.hatType || 'cap';
    if (ht === 'fedora') { add(cyl(6.4, 6.4, .6, 14), hm, 0, 6.6, 0, headJ); add(cyl(3.6, 4.3, 3.6, 12), hm, 0, 8.6, 0, headJ); add(cyl(4.35, 4.35, .9, 12), mat('#111111'), 0, 7.2, 0, headJ); }
    else if (ht === 'straw') { add(cyl(7.6, 7.6, .5, 16), hm, 0, 6.8, 0, headJ); add(cyl(3.8, 4.4, 3, 12), hm, 0, 8.4, 0, headJ); add(cyl(4.45, 4.45, .8, 12), mat('#2a1d14'), 0, 7.3, 0, headJ); }
    else if (ht === 'beanie') add(sph(4.6, 10, 6, true), hm, -.2, 5.2, 0, headJ).scale.set(1, 1.15, 1);
    else { add(cyl(4.5, 4.6, 2.6, 10), hm, -.3, 7.6, 0, headJ); add(bx(4.5, .8, 7.5), hm, 3.6, 6.5, 0, headJ); }
  }
  if (o.bandana) add(cyl(4.35, 4.35, 1.8, 10), mat(o.bandana, o.bandana), 0, 5.6, 0, headJ);
  // bras : épaule, coude, poignet, main avec pouce
  const arms = [];
  for (const side of [-1, 1]) {
    const sh = joint(chest, 0, 9.6, side * (F ? 5 : 5.8));
    add(sph(1.9, 7, 5), sleeve, 0, 0, 0, sh);
    add(cyl(1.65, 1.4, 6.6), sleeve, 0, -3.3, 0, sh);
    const el = joint(sh, 0, -6.6, 0);
    add(cyl(1.35, 1.15, 6, 8), o.longSleeve === false ? skin : sleeve, 0, -3, 0, el);
    const wr = joint(el, 0, -6, 0);
    detail.push(add(bx(1.6, 2.6, 2.2), skin, .3, -1.3, 0, wr)); detail.push(add(bx(1, 1.4, .8), skin, 1.2, -.6, side * .9, wr));
    arms.push({ sh, el, wr });
  }
  let gunMesh = null;
  if (o.gun) { gunMesh = makeGun(o.gunId || 'pistol', o.gunSkin) || makeGun('pistol'); gunMesh.rotation.z = -PI / 2; gunMesh.position.set(.6, -1.6, 0); arms[1].wr.add(gunMesh); }
  if (o.glow) { const r = new THREE.Mesh(new THREE.RingGeometry(10, 12.5, 20), bmat(o.glow, .75, true)); r.rotation.x = -PI / 2; r.position.y = .6; g.add(r); }
  const shd = new THREE.Mesh(new THREE.CircleGeometry(9, 14), bmat('#000000', .35)); shd.rotation.x = -PI / 2; shd.position.y = .3; g.add(shd);
  g.scale.setScalar((o.scale || 1) * 1.5 * (o.height || 1));
  g.userData = { root, pelvis, chest, neck, legs, arms, body: chest, headJ, detail, gun: !!o.gun, gunMesh, gunId: o.gunId || 'pistol', gunSkin: o.gunSkin, ls: -1, ph: Math.random() * 6, spd: 0, amt: 0, fall: 0, recoil: 0, hurt: 0 };
  return g;
}
function makeGlbChar(md) {
  const g = new THREE.Group(); g.add(md.scene); md.scene.scale.setScalar(md.scale); md.scene.rotation.y = PI / 2;
  const shd = new THREE.Mesh(new THREE.CircleGeometry(10, 14), bmat('#000000', .35)); shd.rotation.x = -PI / 2; shd.position.y = .3; g.add(shd);
  let gunMesh = null; if (md.hand) { gunMesh = makeGun(save.weapon === 'fists' ? 'pistol' : save.weapon, wup(save.weapon).skin || 'black'); if (gunMesh) { gunMesh.scale.setScalar(1 / md.scale * 1.4); gunMesh.rotation.set(0, 0, -PI / 2); md.hand.add(gunMesh); } }
  g.userData = { glb: md, gunMesh, gunId: save.weapon === 'fists' ? 'pistol' : save.weapon, gunSkin: wup(save.weapon).skin || 'black', ls: -1, spd: 0, cur: null, detail: [] };
  return g;
}
function poseGlb(m, x, y, a, step, ko, punching) {
  const u = m.userData, md = u.glb; m.position.set(x, 0, y); m.rotation.set(0, -a, 0);
  const ds = step - (u.ls < 0 ? step : u.ls); u.ls = step; u.spd += (Math.min(8, Math.abs(ds) * 60) - u.spd) * .2;
  const want = ko ? 'death' : punching ? 'punch' : u.spd > 4.5 ? 'run' : u.spd > .6 ? 'walk' : 'idle';
  const act = md.acts[want] || md.acts.idle;
  if (act && u.cur !== act) { if (u.cur) u.cur.fadeOut(.2); act.reset().fadeIn(.2).play(); u.cur = act; }
  md.mixer.update(Math.min(.05, R3.dt || .016));
}
function poseChar(m, x, y, a, step, ko, aim, fx) {
  const u = m.userData; fx = fx || {};
  if (u.glb) return poseGlb(m, x, y, a, step, ko, S.time - (P.lastShot || -9) < .3 && save.weapon === 'fists');
  const ds = step - (u.ls < 0 ? step : u.ls); u.ls = step;
  u.spd += (Math.min(8, Math.abs(ds) * 60) - u.spd) * .2;
  const moving = Math.abs(ds) > .0001; u.amt += ((moving ? 1 : 0) - u.amt) * .25;
  const A = u.amt, run = clamp((u.spd - 2.5) / 3, 0, 1), t = step * 1.1;
  // chute au sol (K.O.)
  u.fall += ((ko ? 1 : 0) - u.fall) * (ko ? .12 : .3);
  m.position.set(x, 0, y); m.rotation.set(0, -a, 0);
  u.root.rotation.z = -u.fall * PI / 2; u.root.position.y = u.fall * 4;
  if (fx.recoil) u.recoil = Math.max(u.recoil, fx.recoil); u.recoil *= .8;
  if (fx.hurt) u.hurt = Math.max(u.hurt, fx.hurt); u.hurt *= .85;
  const sw = Math.sin(t) * (.55 + .35 * run) * A;
  const [L, R] = u.legs;
  L.hip.rotation.z = sw; R.hip.rotation.z = -sw;
  L.knee.rotation.z = -Math.max(0, -Math.sin(t)) * (1 + .5 * run) * A - .05; R.knee.rotation.z = -Math.max(0, Math.sin(t)) * (1 + .5 * run) * A - .05;
  L.ankle.rotation.z = Math.max(0, Math.sin(t)) * .3 * A; R.ankle.rotation.z = Math.max(0, -Math.sin(t)) * .3 * A;
  u.pelvis.position.y = 15.5 + Math.abs(Math.sin(t)) * (.7 + .8 * run) * A;
  u.chest.rotation.z = -.14 * run * A + u.recoil * .1 - u.hurt * .3;
  u.chest.rotation.y = Math.sin(t) * .12 * A;
  const breath = Math.sin(S.time * 2.2 + u.ph) * .015; u.chest.scale.set(1, 1 + breath, 1);
  u.headJ.rotation.y = A < .3 ? Math.sin(S.time * .5 + u.ph) * .35 : -Math.sin(t) * .1 * A; u.headJ.rotation.z = u.hurt * .25;
  const [aL, aR] = u.arms;
  if (u.gun && aim) {
    const two = u.gunMesh && u.gunMesh.userData.twoHand;
    aR.sh.rotation.set(0, 0, PI / 2 - u.recoil * .35); aR.el.rotation.z = .05; aR.wr.rotation.z = 0;
    if (two) { aL.sh.rotation.set(-.75, 0, PI / 2.15); aL.el.rotation.z = .55; aL.wr.rotation.z = .2; }
    else { aL.sh.rotation.set(-.08, 0, -sw * .5); aL.el.rotation.z = .3; aL.wr.rotation.z = 0; }
  } else {
    const amp = .85 + .5 * run;
    aL.sh.rotation.set(-.08, 0, -sw * amp); aR.sh.rotation.set(.08, 0, sw * amp);
    aL.el.rotation.z = .25 + run * .9 + Math.max(0, sw) * .5; aR.el.rotation.z = .25 + run * .9 + Math.max(0, -sw) * .5;
    aL.wr.rotation.z = aR.wr.rotation.z = .1;
  }
  if (u.detail.length) { const far = Math.abs(x - cam.x) + Math.abs(y - cam.y) > Q.lod; if (far !== u.far) { u.far = far; for (const d of u.detail) d.visible = !far; } }
}
// ---- voitures
function makeCar3(c) {
  const g = new THREE.Group(), paint = [];
  const add = (geo, m, x, y, z) => { const me = new THREE.Mesh(geo, m); me.position.set(x, y, z); g.add(me); return me; };
  const P2 = (geo, x, y, z) => { const me = add(geo, mat(c.color), x, y, z); paint.push(me); return me; };
  const glass = mat('#121022'), tyre = mat('#08080c'), chrome = mat('#cfd3dc');
  const type = c.kind === 'police' || c.kind === 'gang' ? 'sedan' : (c.type || 'sedan');
  add(bx(46, .5, 24), bmat('#000000', .35), 1, .3, 0);
  const wheels = (fx, rx, w = 22) => { add(bx(9, 9, w), tyre, fx, 5, 0); add(bx(9, 9, w), tyre, rx, 5, 0); };
  const lights = (fx, rx, y = 10, wd = 15) => { add(bx(1, 3, wd), mat('#fff6cc', '#fff2b0'), fx, y, 0); add(bx(1, 3, wd), mat('#ff2e4d', '#ff2e4d'), rx, y, 0); };
  let front = 21;
  if (type === 'scooter') {
    P2(bx(24, 7, 7), 0, 9, 0); add(cyl(4.5, 4.5, 3, 10), tyre, 10, 4.5, 0).rotation.x = PI / 2; add(cyl(4.5, 4.5, 3, 10), tyre, -10, 4.5, 0).rotation.x = PI / 2;
    add(bx(3, 12, 3), chrome, 11, 16, 0); add(bx(2, 2, 14), chrome, 11, 22, 0); add(bx(10, 2.5, 6), mat('#1a1a1a'), -3, 14, 0);
    add(bx(1, 3, 4), mat('#fff6cc', '#fff2b0'), 12.6, 15, 0); front = 12;
    if (c.ai === 'traffic' || c.ai === 'convoy') { const r = makeChar({ shirt: pick(['#ffd23f', '#21e6ff', '#ffffff', '#ff2e93']), skin: pick(PEDC), hat: '#111118', hatType: 'beanie' }); r.scale.setScalar(1); r.position.set(-3, 5, 0); r.userData.legs.forEach(l => { l.hip.rotation.z = 1.2; l.knee.rotation.z = -1.4; }); r.userData.arms.forEach(a2 => a2.sh.rotation.z = 1.1); g.add(r); }
  } else if (type === 'van') {
    P2(bx(44, 20, 21), 0, 14, 0); add(bx(8, 8, 21.4), glass, 16, 18, 0); add(bx(30, 6, 21.4), glass, -4, 19, 0); wheels(14, -14); lights(22.2, -22.2, 9);
    front = 22;
  } else if (type === 'bus') {
    P2(bx(58, 22, 22), 0, 16, 0); add(bx(46, 7, 22.4), glass, 2, 20, 0);
    for (const [y2, col] of [[8, '#ff006e'], [11, '#3a86ff'], [26.5, '#8ac926']]) add(bx(58.4, 2, 22.4), mat(col), 0, y2, 0);
    add(bx(40, 2, 18), mat('#4a3424'), 0, 28, 0); wheels(19, -19); lights(29.2, -29.2, 9); front = 29;
  } else if (type === 'pickup') {
    P2(bx(42, 8, 20), 0, 9, 0); P2(bx(16, 9, 19), 6, 17.5, 0); add(bx(14, 7, 19.4), glass, 6, 18, 0);
    add(bx(18, 1, 19), mat('#2a2830'), -11, 13.5, 0); P2(bx(18, 5, 1.5), -11, 15.5, 9.5); P2(bx(18, 5, 1.5), -11, 15.5, -9.5); P2(bx(1.5, 5, 19), -20, 15.5, 0);
    wheels(13, -13); lights(21.2, -21.2);
  } else if (type === 'jeep') {
    P2(bx(38, 12, 21), 0, 11, 0); add(bx(3, 9, 19), glass, 8, 21, 0);
    for (const dz of [-9, 9]) { add(bx(2, 12, 2), mat('#1a1a1a'), -10, 23, dz); add(bx(20, 2, 2), mat('#1a1a1a'), -1, 29, dz); }
    add(cyl(6, 6, 4, 10), tyre, -21.5, 13, 0).rotation.z = PI / 2; wheels(12, -12, 23); lights(19.2, -19.2, 12); front = 19;
  } else if (type === 'convertible') {
    P2(bx(42, 8, 20), 0, 8.5, 0); P2(bx(10, 2, 19), 15, 13, 0); add(bx(1.2, 6, 18), mat('#9fd6ff', '#203040'), 9, 15.5, 0);
    add(bx(6, 6, 7), mat('#1a1a1a'), 1, 15, -5); add(bx(6, 6, 7), mat('#1a1a1a'), 1, 15, 5); add(bx(6, 5, 16), mat('#1a1a1a'), -9, 14, 0);
    wheels(13, -13); lights(21.2, -21.2);
  } else if (type === 'muscle') {
    P2(bx(46, 8, 21), 0, 8.5, 0); P2(bx(14, 2.5, 20), 15, 13, 0); add(bx(18, 7.5, 18), glass, -6, 16, 0); P2(bx(14, 1.5, 17), -7, 20.4, 0);
    for (const dz of [-3, 3]) add(bx(36, .3, 2), mat('#ffffff'), 3, 14.4, dz); add(bx(3, 4, 20), mat('#111111'), -22, 15, 0);
    wheels(15, -15); lights(23.2, -23.2, 9); front = 23;
  } else if (type === 'small') {
    P2(bx(34, 9, 18), 0, 9, 0); add(bx(17, 9, 16.5), glass, -2, 17.5, 0); P2(bx(14, 1.6, 15), -2, 22.6, 0);
    wheels(11, -11, 20); lights(17.2, -17.2, 10, 13); front = 17;
  } else {
    P2(bx(42, 9, 20), 0, 9, 0); P2(bx(10, 2, 19), 15, 14, 0); add(bx(21, 9, 17.5), glass, -3, 18, 0); P2(bx(17, 1.6, 16), -4, 23.2, 0);
    wheels(13, -13); lights(21.2, -21.2);
    if (type === 'taxi') { add(bx(8, 4, 12), mat('#ffd23f', '#806000'), -4, 26, 0); add(bx(42.2, 2, 20.2), mat('#111111'), 0, 11, 0); }
  }
  const u = { paint, color: c.color, wreck: false };
  if (c.kind === 'police') {
    add(bx(12, 9.2, 20.4), mat('#1b1f4a'), -2, 9, 0);
    u.r = add(bx(4, 3, 7), mat('#ff2e4d'), -4, 25.5, -4); u.b = add(bx(4, 3, 7), mat('#2e6bff'), -4, 25.5, 4);
    u.glow = add(new THREE.CircleGeometry(48, 20), bmat('#ff2e4d', .18, true), 0, .8, 0); u.glow.rotation.x = -PI / 2;
  }
  const cone = new THREE.Mesh(new THREE.CircleGeometry(150, 14, -.33, .66), R3.coneMat || (R3.coneMat = bmat('#fff0c0', .1, true).clone()));
  cone.rotation.x = -PI / 2; cone.position.set(front - 3, .7, 0); g.add(cone); u.cone = cone;
  if (c.mark) { u.mk = new THREE.Mesh(new THREE.ConeGeometry(7, 14, 4), new THREE.MeshBasicMaterial({ color: c.convoy ? 0xff4d5e : 0xffd700, depthTest: false })); u.mk.rotation.z = PI; u.mk.renderOrder = 9; g.add(u.mk); }
  g.scale.setScalar(1.15);
  g.userData = u;
  return g;
}
function poseCar(m, c) {
  const u = m.userData;
  m.position.set(c.x, 0, c.y); m.rotation.y = -c.a;
  if (c.wreck && !u.wreck) { u.wreck = true; for (const pm of u.paint) pm.material = mat('#26222e'); u.cone.visible = false; if (u.glow) u.glow.visible = false; if (u.mk) u.mk.visible = false; }
  if (!c.wreck && u.color !== c.color) { u.color = c.color; for (const pm of u.paint) pm.material = mat(c.color); }
  if (u.r && !c.wreck) { const f = Math.sin((S.time + c.flash) * 14) > 0; u.r.material = f ? mat('#ff2e4d', '#ff2e4d') : mat('#401018'); u.b.material = f ? mat('#10183a') : mat('#2e6bff', '#2e6bff'); u.glow.material = bmat(f ? '#ff2e4d' : '#2e6bff', .2, true); }
  if (u.mk) { u.mk.visible = c.mark && !c.wreck; u.mk.position.set(0, 40 + Math.sin(S.time * 5) * 4, 0); }
}
// ---- objets simples
function makeProp(kind) {
  const g = new THREE.Group();
  if (kind === 'ammo') { const m = new THREE.Mesh(bx(13, 8, 9), mat('#3d4a2a', '#1a2a0a')); m.position.y = 5; g.add(m); const l = new THREE.Mesh(bx(13.4, 2, 9.4), mat('#ffd23f', '#6a5000')); l.position.y = 7; g.add(l); }
  else if (kind === 'cash') { const m = new THREE.Mesh(bx(14, 4, 9), mat('#a6ff4d', '#3a7a10')); m.position.y = 6; g.add(m); }
  else if (kind === 'case') { const m = new THREE.Mesh(bx(16, 11, 6), mat('#c98a2b', '#4a2a00')); m.position.y = 8; g.add(m); const h = new THREE.Mesh(bx(6, 3, 2), mat('#3a2410')); h.position.y = 15; g.add(h);
    const b = new THREE.Mesh(new THREE.CylinderGeometry(10, 10, 80, 12, 1, true), bmat('#ffb627', .18, true)); b.position.y = 40; g.add(b); }
  return g;
}
function makeHeli() {
  const g = new THREE.Group(), add = (geo, m, x, y, z) => { const me = new THREE.Mesh(geo, m); me.position.set(x, y, z); g.add(me); return me; };
  const body = add(sph(14, 12, 8), mat('#1b1f4a'), 0, 0, 0); body.scale.set(1.7, 1, 1.05);
  add(sph(9, 10, 6), mat('#9fd6ff', '#204060'), 13, 2, 0).scale.set(1, .8, 1);
  add(bx(40, 2.2, 22), mat('#f2f4ff'), 0, -3, 0).scale.set(1, 1, .98);
  const boom = add(cyl(3, 1.6, 44, 6), mat('#1b1f4a'), -38, 3, 0); boom.rotation.z = PI / 2;
  add(bx(8, 12, 1.5), mat('#1b1f4a'), -58, 8, 0);
  add(bx(44, 1.6, 2), mat('#222230'), 0, -16, -10); add(bx(44, 1.6, 2), mat('#222230'), 0, -16, 10);
  const rotor = new THREE.Group(); rotor.position.y = 16; g.add(rotor);
  rotor.add(new THREE.Mesh(bx(110, 1, 5), mat('#15151c'))); const r2 = new THREE.Mesh(bx(5, 1, 110), mat('#15151c')); rotor.add(r2);
  const tail = new THREE.Mesh(bx(1, 18, 3), mat('#15151c')); tail.position.set(-58, 8, 2); g.add(tail);
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(6, 60, 150, 18, 1, true), bmat('#fff7c0', .12, true)); beam.position.y = -75; g.add(beam);
  const spot = new THREE.Mesh(new THREE.CircleGeometry(60, 24), bmat('#fff7c0', .22, true)); spot.rotation.x = -PI / 2; spot.position.y = -149; g.add(spot);
  const red = add(sph(2, 6, 4), mat('#ff2e4d', '#ff2e4d'), -60, 14, 0);
  g.scale.setScalar(.8);
  g.userData = { rotor, tail, red, bar: hpBar(g, 30, 50) };
  return g;
}
function poseHeli(m, h) {
  const u = m.userData;
  m.position.set(h.x, 150, h.y); m.rotation.set(0, -h.a, -.12);
  u.rotor.rotation.y = S.time * 28; u.tail.rotation.z = S.time * 40; u.red.visible = Math.sin(S.time * 8) > 0;
  setBar(u.bar, h.hp / h.max, '#2e6bff', true, h.a);
}
function showCine(sub, title, story) { document.body.classList.add('cine'); const el = $('cine'); el.querySelector('small').textContent = TR(sub); el.querySelector('b').textContent = TR(title); const sp = el.querySelector('p.story'); if (sp) { sp.textContent = story ? TR(story) : ''; sp.hidden = !story; } el.hidden = false; requestAnimationFrame(() => el.classList.add('on')); }
function hideCine() { document.body.classList.remove('cine'); const el = $('cine'); el.classList.remove('on'); setTimeout(() => { if (!S.cine) el.hidden = true; }, 400); }
function skipCine() { if (S.cine) S.cine.start = performance.now() - S.cine.dur * 1000; }
const lerpC = (a, b, t) => col3(a).clone().lerp(col3(b), t);
function envFx(dt, playing) {
  const tod = playing ? (S.tod || 0) : .95, night = (Math.cos(tod * TAU) + 1) / 2, day = 1 - night;
  const dusk = Math.exp(-Math.pow((tod - .27) / .05, 2)) + Math.exp(-Math.pow((tod - .73) / .05, 2));
  const rainK = playing && S.rain ? 1 : 0;
  const p = world.region.pal;
  let sky = lerpC(p.ground, (world.region.look || {}).sky || '#86b4e3', Math.pow(day, 1.4) * (1 - rainK * .5)); sky.lerp(col3('#ff8a5c'), Math.min(.45, dusk * .45)); if (rainK) sky.lerp(col3('#3a4250'), .35 * day);
  R3.scene.background = sky; if (R3.scene.fog) R3.scene.fog.color = sky;
  if (R3.sky) {
    const top = lerpC('#05030f', (world.region.look || {}).sky || '#4f8fd6', Math.pow(day, 1.2)).multiplyScalar(rainK ? .6 : 1), hor = sky.clone();
    if (dusk > .05) top.lerp(col3('#3a2a6a'), Math.min(.5, dusk * .5));
    const cA = R3.sky.geometry.attributes.color, pA = R3.sky.geometry.attributes.position;
    for (let i = 0; i < pA.count; i++) { const y = pA.getY(i) / 4200, k = Math.max(0, Math.min(1, y * 1.6)); const c = hor.clone().lerp(top, k); cA.setXYZ(i, c.r, c.g, c.b); }
    cA.needsUpdate = true; R3.sky.position.set(R3.cam.position.x, 0, R3.cam.position.z);
    R3.stars.position.copy(R3.sky.position); R3.stars.material.opacity = Math.max(0, night - .35) * (rainK ? .2 : 1.4);
    const ang = tod * TAU - PI / 2; R3.moonDisk.position.set(R3.sky.position.x + Math.cos(ang) * 3200, Math.max(-400, Math.sin(ang) * 2200 + 300), R3.sky.position.z - 2400);
    R3.moonDisk.material.color = night > .5 ? col3('#fff6dd') : col3('#fff1a8'); R3.moonDisk.scale.setScalar(night > .5 ? 1 : 1.5);
    if (playing && P.car && !P.car.wreck) { R3.glow.visible = true; R3.glow.position.set(P.car.x, .9, P.car.y); R3.glow.rotation.z = -P.car.a; R3.glow.material.opacity = .15 + night * .45; R3.glow.material.color.setHSL((S.time * .08) % 1, 1, .55); } else R3.glow.visible = false;
  }
  R3.hemi.intensity = .6 + day * .8 - rainK * .15; R3.hemi.color = lerpC('#a7b0ff', '#ffffff', day); R3.hemi.groundColor = lerpC('#241838', '#6a6070', day);
  R3.moon.intensity = .45 + day * .7; R3.moon.color = lerpC('#9fb0ff', '#fff2dd', day).lerp(col3('#ffb070'), Math.min(.6, dusk));
  if (R3.sideMat) R3.sideMat.emissiveIntensity = .12 + night * .85;
  if (R3.anim) for (const f of R3.anim) f(dt, night);
  if (R3.beacons) { const cx = R3.cam.position.x, cz = R3.cam.position.z, px = P.car ? P.car.x : P.x, pz = P.car ? P.car.y : P.y; for (const m of R3.beacons) { const dc = Math.hypot(m.position.x - cx, m.position.z - cz), dp = Math.hypot(m.position.x - px, m.position.z - pz); m.visible = dc > 140 && dp > 90; } }
  if (R3.coneMat) R3.coneMat.opacity = .02 + night * .1;
  // éclair des tirs et explosions
  if (S.flash && !Q.fx) { S.flash = null; R3.flash.intensity = 0; }
  if (S.flash) { R3.flash.position.set(S.flash.x, 30, S.flash.y); R3.flash.intensity = S.flash.i; S.flash.i -= dt * 18; if (S.flash.i <= 0) { S.flash = null; R3.flash.intensity = 0; } }
  // phares de la voiture du joueur
  if (R3.halos) R3.halos.material.opacity = Math.max(0, night - .2) * .75;
  if (R3.shadow) { const px = P.car ? P.car.x : P.x, pz = P.car ? P.car.y : P.y; R3.moon.position.set(px - 320, 900, pz + 260); R3.moon.target.position.set(px, 0, pz); }
  if (playing && P.car && !P.car.wreck && Q.fx) { const c = P.car; R3.head.intensity = .3 + night * 2.4; R3.head.position.set(c.x + Math.cos(c.a) * 20, 22, c.y + Math.sin(c.a) * 20); R3.head.target.position.set(c.x + Math.cos(c.a) * 260, 0, c.y + Math.sin(c.a) * 260); }
  else R3.head.intensity = 0;
  // débris
  if (S.debris && S.debris.length) { for (const d of S.debris) for (let k = 0; k < (Q.fx ? 7 : 2); k++) { const m = new THREE.Mesh(bx(rnd(4, 9), rnd(2, 5), rnd(4, 9)), mat(k % 2 ? d.col : '#2a2633')); m.position.set(d.x, 12, d.y); m.userData = { vx: rnd(-160, 160), vy: rnd(120, 260), vz: rnd(-160, 160), life: 2.2, rx: rnd(-8, 8), rz: rnd(-8, 8) }; R3.scene.add(m); R3.debris.push(m); } S.debris = []; }
  for (const m of R3.debris) { const u = m.userData; u.life -= dt; u.vy -= 520 * dt; m.position.x += u.vx * dt; m.position.y = Math.max(1.5, m.position.y + u.vy * dt); m.position.z += u.vz * dt; if (m.position.y <= 1.5) { u.vx *= .9; u.vz *= .9; u.vy = Math.abs(u.vy) * .25; } m.rotation.x += u.rx * dt; m.rotation.z += u.rz * dt; if (u.life <= 0) R3.scene.remove(m); }
  R3.debris = R3.debris.filter(m => m.userData.life > 0);
  // pluie autour de la caméra
  R3.rain.visible = !!rainK;
  if (rainK) {
    const a = R3.rain.geometry.attributes.position, cx = cam.x, cz = cam.y;
    for (let i = 0; i < R3.NR; i++) { const d = R3.drops[i]; d.y -= 900 * dt; if (d.y < 0) { d.y = 400; d.x = rnd(-700, 700); d.z = rnd(-700, 700); }
      const x = cx + d.x, z = cz + d.z; a.setXYZ(i * 2, x, d.y, z); a.setXYZ(i * 2 + 1, x + 4, d.y + 26, z + 2); }
    a.needsUpdate = true;
  }
}
function cineCamera(playing) {
  if (!S.cine || !playing) return;
  const c = S.cine, k = clamp(c.t / c.dur, 0, 1), cam3 = R3.cam;
  const fwd = new THREE.Vector3(); cam3.getWorldDirection(fwd);
  const normPos = cam3.position.clone(), normTgt = normPos.clone().add(fwd.multiplyScalar(300));
  let pos, tgt, e;
  if (c.type === 'intro') {
    const px = P.car ? P.car.x : P.x, pz = P.car ? P.car.y : P.y;
    if (c.dur > 5) { // plan large, travelling de rue, puis approche du héros
      if (k < .4) { const a2 = k / .4 * 1.2; pos = new THREE.Vector3(px + Math.cos(a2) * 900, 640, pz + Math.sin(a2) * 900); tgt = new THREE.Vector3(px, 0, pz); }
      else if (k < .75) { const f = (k - .4) / .35; pos = new THREE.Vector3(px - 520 + f * 360, 46, pz + 150); tgt = new THREE.Vector3(px + 200, 30, pz - 40); }
      else { const f = (k - .75) / .25; pos = new THREE.Vector3(px + 90 - f * 30, 40 + f * 30, pz + 90); tgt = new THREE.Vector3(px, 28, pz); }
      e = k < .88 ? 0 : (k - .88) / .12;
    } else { const ang = k * 1.6; pos = new THREE.Vector3(px + Math.cos(ang) * 520, 420 - k * 120, pz + Math.sin(ang) * 520); tgt = new THREE.Vector3(px, 10, pz); e = k < .7 ? 0 : (k - .7) / .3; }
    e = e * e * (3 - 2 * e);
  } else {
    const b = c.focus, a = Math.atan2(P.y - b.y, P.x - b.x);
    pos = new THREE.Vector3(b.x + Math.cos(a) * 95, 48, b.y + Math.sin(a) * 95); tgt = new THREE.Vector3(b.x, 34, b.y);
    e = k < .15 ? 1 - k / .15 : k > .8 ? (k - .8) / .2 : 0;
  }
  cam3.position.copy(pos.lerp(normPos, e)); cam3.lookAt(tgt.lerp(normTgt, e));
}
// le joueur reste visible à travers les immeubles
function xray(m) {
  R3.xf = (R3.xf || 0) + 1;
  if (R3.xf % 5 === 0 && R3.bldMesh) {
    const tgt = new THREE.Vector3(P.x, 30, P.y), from = R3.cam.position.clone(), dir = tgt.clone().sub(from), len = dir.length();
    R3.ray.set(from, dir.normalize()); R3.ray.far = len - 8;
    let hid = false; try { hid = R3.ray.intersectObject(R3.bldMesh, false).length > 0; } catch (e) {}
    const inside = tileAt(P.x, P.y) === BLD; R3.ray.far = Infinity;
    R3.hidden = hid || inside;
  }
  const h = !!R3.hidden;
  if (m.userData.xr !== h) { m.userData.xr = h; m.traverse(o => { if (o.isMesh && o.material && !o.material.isMeshBasicMaterial) { o.material.depthTest = !h; o.material.transparent = h; o.material.opacity = h ? .85 : 1; o.renderOrder = h ? 20 : 0; o.material.needsUpdate = true; } }); }
}
function hpBar(parent, y, w) {
  const bg = new THREE.Mesh(new THREE.PlaneGeometry(w, 3.5), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: .6, depthTest: false }));
  const fg = new THREE.Mesh(new THREE.PlaneGeometry(w, 3.5), new THREE.MeshBasicMaterial({ color: 0xffffff, depthTest: false }));
  bg.renderOrder = 12; fg.renderOrder = 13; bg.rotation.x = fg.rotation.x = -1.1; fg.position.z = .1;
  const holder = new THREE.Group(); holder.position.y = y; holder.add(bg, fg); parent.add(holder);
  return { bg, fg, w, holder };
}
function setBar(b, v, colr, show, a) { b.bg.visible = b.fg.visible = show; if (!show) return; b.holder.rotation.y = a || 0; v = clamp(v, 0, 1); b.fg.scale.x = Math.max(.001, v); b.fg.position.x = -(1 - v) * b.w / 2; b.fg.material.color.set(colr); }
function sync(e, make, pose) {
  let m = e._m;
  if (!m) { m = e._m = make(e); if (R3.shadow) m.traverse(o => { if (o.isMesh && o.material && o.material.isMeshLambertMaterial) o.castShadow = true; }); }
  if (m.parent !== R3.dyn) R3.dyn.add(m);
  R3.seen.add(m); pose(m, e);
}
function resize3D() { if (R3.w === VW && R3.h === VH) return; R3.w = VW; R3.h = VH; R3.r.setSize(VW, VH, false); R3.cam.aspect = VW / VH; R3.cam.updateProjectionMatrix(); if (R3.composer) { R3.composer.setPixelRatio(R3.r.getPixelRatio()); R3.composer.setSize(VW, VH); } }
// rendu filmique : étalonnage ACES + halos lumineux (bloom) en qualité haute
function setupPost() {
  R3.r.toneMapping = THREE.ACESFilmicToneMapping; R3.r.toneMappingExposure = 1.25;
  if (!THREE.EffectComposer || !THREE.UnrealBloomPass || qLevel !== 'high') { R3.composer = null; return; }
  try { const c = new THREE.EffectComposer(R3.r); c.addPass(new THREE.RenderPass(R3.scene, R3.cam)); const bl = new THREE.UnrealBloomPass(new THREE.Vector2(VW || 1280, VH || 720), .8, .45, .72); c.addPass(bl); R3.composer = c; R3.bloom = bl; R3.w = 0; } catch (e) { R3.composer = null; }
}
function render3D(dt) {
  R3.dt = dt;
  if (R3.world !== world) build3DWorld();
  resize3D();
  const playing = S.mode !== 'menu' && L;
  const mode = playing ? (save.cam || 'top') : 'top';
  const head = P.car ? P.car.a : P.a;
  if (mode === 'top') R3.yaw = -PI / 2;
  else { if (R3.mode !== mode || R3.yaw === undefined) R3.yaw = head; R3.yaw += angDiff(head, R3.yaw) * Math.min(1, dt * (P.car ? 3.2 : 1.7)); }
  if (R3.mode !== mode) { R3.mode = mode; R3.cam.fov = mode === 'top' ? 46 : mode === 'chase' ? 62 : 72; R3.cam.updateProjectionMatrix(); R3.cp = null; }
  const fogN = mode === 'top' ? 1150 : 520, fogF = mode === 'top' ? 2700 : 1750;
  if (R3.scene.fog) { R3.scene.fog.near = fogN; R3.scene.fog.far = fogF; }
  const sp = P.car && playing ? Math.abs(P.car.v) : 0;
  const sx = shake ? rnd(-shake, shake) : 0, sy = shake ? rnd(-shake, shake) : 0; shake = Math.max(0, shake - dt * 30);
  let ccx, ccz;
  if (mode === 'top') {
    let tx, ty;
    if (!playing) { R3.orbit = (R3.orbit || 0) + dt * .04; tx = W / 2 + Math.cos(R3.orbit) * 1100; ty = W / 2 + Math.sin(R3.orbit) * 1100; }
    else { tx = P.car ? P.car.x + Math.cos(P.car.a) * P.car.v * .3 : P.x; ty = P.car ? P.car.y + Math.sin(P.car.a) * P.car.v * .3 : P.y; }
    const k = Math.min(1, dt * 4); cam.x += (tx - cam.x) * k; cam.y += (ty - cam.y) * k;
    let d = 350 + sp * .3; if (VW < VH) d *= 1.35; if (!playing) d = 760;
    cam.z += (d - cam.z) * Math.min(1, dt * 2); if (cam.z < 100) cam.z = d;
    R3.cam.position.set(cam.x + sx, cam.z, cam.y + cam.z * (playing ? .3 : .5) + sy); R3.cam.lookAt(cam.x, 0, cam.y);
    ccx = cam.x; ccz = cam.y;
  } else {
    const fx = Math.cos(R3.yaw), fz = Math.sin(R3.yaw), rx = -fz, rz = fx;
    const px = P.car ? P.car.x : P.x, pz = P.car ? P.car.y : P.y;
    let back, h, look, lh, side = 0;
    if (mode === 'chase') { back = P.car ? 150 + sp * .1 : 110; h = P.car ? 82 : 72; look = P.car ? 140 : 80; lh = P.car ? 14 : 30; }
    else if (P.car) { back = -16; h = 22; look = 320; lh = 16; }
    else { back = 50; h = 54; look = 140; lh = 42; side = 16; }
    if (VW < VH && mode === 'chase') { back *= 1.15; h *= 1.1; }
    let b = back;
    for (let k = 0; k < 8 && b > 12; k++) { if (!solid(px - fx * b + rx * side, pz - fz * b + rz * side)) break; b *= .7; }
    const tx = px - fx * b + rx * side, tz = pz - fz * b + rz * side;
    const attached = mode === 'car' && P.car;
    if (!R3.cp || attached) R3.cp = { x: tx, z: tz, h };
    else { const kk = Math.min(1, dt * 9); R3.cp.x += (tx - R3.cp.x) * kk; R3.cp.z += (tz - R3.cp.z) * kk; R3.cp.h += (h - R3.cp.h) * kk; }
    { const base = mode === 'chase' ? 62 : 72, f2 = base + Math.min(14, sp / 40) + (P.nitro > 0 ? 8 : 0); if (Math.abs(R3.cam.fov - f2) > .2) { R3.cam.fov += (f2 - R3.cam.fov) * Math.min(1, dt * 3); R3.cam.updateProjectionMatrix(); } }
    R3.cam.position.set(R3.cp.x + sx * .4 + (sp > 380 ? rnd(-.6, .6) : 0), R3.cp.h, R3.cp.z + sy * .4);
    R3.cam.lookAt(px + fx * look + rx * side * .4, lh, pz + fz * look + rz * side * .4);
    cam.x = px; cam.y = pz; cam.z = 400;
    ccx = px + fx * 420; ccz = pz + fz * 420;
  }
  const near = (x, y) => Math.abs(x - ccx) < 1150 && Math.abs(y - ccz) < 1150;
  const hideOwn = mode === 'car' && P.car;
  R3.seen.clear();
  for (const c of cars) if (near(c.x, c.y)) { sync(c, makeCar3, poseCar); c._m.visible = !(hideOwn && c === P.car); }
  for (const p of peds) if (near(p.x, p.y)) sync(p, e => { if (e.look) return makeChar(e.look); const f = Math.random() < .5; return makeChar({ female: f, shirt: e.shirt, skin: e.skin, hair: pick(['#1a120c', '#3b2414', '#0c0c0c', '#6b4a2a', '#d8b46a', '#8a3b1c']), hairStyle: f ? pick(['long', 'ponytail', 'afro', 'short']) : pick(['short', 'short', 'afro', 'none']), pants: pick(['#1d1a2e', '#2a3a5a', '#3a2a22', '#26262e', '#4a4f5a']), skirt: f && Math.random() < .35 ? pick(['#2a3a5a', '#7a2a4a', '#1d1a2e']) : null, jacket: Math.random() < .3 ? pick(['#2b2b33', '#5a3a22', '#1f3a5a']) : null, longSleeve: Math.random() < .5, height: rnd(.92, 1.06), shoes: pick(['#0c0b12', '#ffffff', '#5a3a22']) }); }, (m, e) => poseChar(m, e.x, e.y, e.a, e.step, e.state === 'ko'));
  for (const e of enemies) if (near(e.x, e.y)) sync(e, e2 => { const lk = e2.look || {}; const m = makeChar(Object.assign({ shirt: '#17131f', sleeve: '#17131f', skin: pick(((world.region.look || {}).peds || {}).skins || ['#c68b59', '#8d5a3b', '#e0b48c']), bandana: e2.boss ? null : e2.color, hat: e2.boss ? e2.color : null, chain: !!e2.boss, hair: '#1a120c' }, lk, { sleeve: lk.jacket || lk.shirt || '#17131f', longSleeve: !!lk.jacket, gun: true, gunId: e2.boss ? (lvl() > 12 ? 'minigun' : 'shotgun') : lvl() < 4 ? 'pistol' : lvl() < 10 ? 'uzi' : 'rifle', gunSkin: e2.boss ? 'gold' : 'black', glow: e2.color, scale: e2.boss ? 1.45 : 1 }, e2.boss ? { chain: true, hat: lk.hat || e2.color } : {})); m.userData.bar = hpBar(m, 30, 16); return m; },
    (m, e2) => { poseChar(m, e2.x, e2.y, e2.a, e2.step, e2.hp <= 0, e2.alert, { recoil: S.time - (e2.firedT || -9) < .08 ? .8 : 0, hurt: S.time - (e2.hitT || -9) < .08 ? 1 : 0 }); setBar(m.userData.bar, e2.hp / e2.max, e2.color, e2.hp > 0 && (e2.alert || e2.boss), e2.a); });
  if (agent && !agent.paid && near(agent.x, agent.y)) sync(agent, () => makeChar({ shirt: '#2e6bff', pants: '#14183a', skin: '#f2d3b3', hat: '#14183a', glow: '#ffb627' }), (m, a) => poseChar(m, a.x, a.y, S.time * .6, 0, false));
  if (vip && vip.hp > 0 && !vip.inCar && !vip.done && near(vip.x, vip.y)) sync(vip, () => { const m = makeChar({ shirt: '#ffd700', sleeve: '#1a1a1a', pants: '#1a1a1a', skin: '#8d5a3b', hat: '#ffffff', chain: true, glow: '#ffd700' }); m.userData.bar = hpBar(m, 30, 18); return m; }, (m, v) => { poseChar(m, v.x, v.y, v.a, v.step, false); setBar(m.userData.bar, v.hp / v.max, '#ffd700', true, v.a); });
  if (playing && !P.car && P._m && (P._m.userData.gunId !== (save.weapon === 'fists' ? 'pistol' : save.weapon) || P._m.userData.gunSkin !== (wup(save.weapon).skin || 'black'))) P._m = null;
  if (playing && !P.car && P._m && !!P._m.userData.glb !== (save.outfit.body === 'robot' && !!R3.models.robot)) P._m = null;
  if (playing && !P.car) sync(P, () => { if (save.outfit.body === 'robot' && R3.models.robot) return makeGlbChar(R3.models.robot); const m = makeChar(Object.assign(playerLook(), { gunId: save.weapon === 'fists' ? 'pistol' : save.weapon, gunSkin: wup(save.weapon).skin || 'black' })); m.traverse(o => { if (o.isMesh && o.material) o.material = o.material.clone(); }); return m; }, m => { xray(m); const u = m.userData; if (u.gunMesh) u.gunMesh.visible = save.weapon !== 'fists'; poseChar(m, P.x, P.y, P.a, P.step, false, !!P.lock || S.time - (P.lastShot || -9) < (save.weapon === 'fists' ? .25 : 1.2), { recoil: S.time - (P.lastShot || -9) < .06 ? (WBASE(save.weapon).explosive ? 1.4 : .7) : 0, hurt: S.time - (P.hitT || -9) < .08 ? 1 : 0 }); });
  for (const p of picks) if (near(p.x, p.y)) sync(p, () => makeProp(p.ammo ? 'ammo' : 'cash'), (m, e) => { m.position.set(e.x, Math.sin(S.time * 4 + e.x) * 2, e.y); m.rotation.y = S.time * 2; });
  if (heli && near(heli.x, heli.y)) sync(heli, makeHeli, poseHeli);
  if (playing) { const got = (save.tagsFound || {})[world.region.id] || []; world.tags.forEach((tg, i) => { if (got.includes(i) || !near(tg.x, tg.y)) return; sync(tg, () => { const g2 = new THREE.Group(); const col = world.region.pal.neon[i % world.region.pal.neon.length]; const d = new THREE.Mesh(new THREE.OctahedronGeometry(9, 0), new THREE.MeshBasicMaterial({ color: col })); d.position.y = 22; g2.add(d); const h2 = new THREE.Mesh(new THREE.CircleGeometry(18, 18), bmat(col, .35, true)); h2.rotation.x = -PI / 2; h2.position.y = .8; g2.add(h2); g2.userData.d = d; return g2; }, (m, e) => { m.position.set(e.x, 0, e.y); m.userData.d.rotation.y = S.time * 2.5; m.userData.d.position.y = 22 + Math.sin(S.time * 3 + e.x) * 3; }); }); }
  for (const c of cases) if (!c.got && near(c.x, c.y)) sync(c, () => makeProp('case'), (m, e) => { m.position.set(e.x, Math.sin(S.time * 4 + e.x) * 2, e.y); m.rotation.y = S.time; });
  for (const m of R3.dyn.children.slice()) if (!R3.seen.has(m)) R3.dyn.remove(m);
  // balles
  let nb = 0, ne = 0;
  for (const b of bullets) {
    const enemy = b.from === 'enemy', im = enemy ? R3.bulE : R3.bul, i = enemy ? ne++ : nb++;
    if (i >= 300) continue;
    R3.v.set(b.x, 15, b.y); R3.q.setFromAxisAngle(R3.up, -Math.atan2(b.vy, b.vx)); R3.s.set(b.explosive ? 2.5 : 1, b.explosive ? 3 : 1, b.explosive ? 3 : 1);
    R3.m4.compose(R3.v, R3.q, R3.s); im.setMatrixAt(i, R3.m4);
  }
  R3.s.set(1, 1, 1);
  if (!R3.skid) { R3.skid = new THREE.InstancedMesh(new THREE.PlaneGeometry(9, 3.4), new THREE.MeshBasicMaterial({ color: 0x08080c, transparent: true, opacity: .55, depthWrite: false }), 400); R3.skid.frustumCulled = false; R3.skid.instanceMatrix.setUsage(THREE.DynamicDrawUsage); R3.scene.add(R3.skid); }
  { let ns2 = 0; for (const sk of skids) { if (!sk) continue; R3.v.set(sk.x, .45, sk.y); R3.q.setFromEuler(new THREE.Euler(-PI / 2, 0, -sk.a, 'YXZ')); R3.q.setFromAxisAngle(R3.up, -sk.a); const q2 = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), -PI / 2); R3.q.multiply(q2); R3.s.set(1, 1, 1); R3.m4.compose(R3.v, R3.q, R3.s); R3.skid.setMatrixAt(ns2++, R3.m4); } R3.q.identity(); R3.skid.count = ns2; R3.skid.instanceMatrix.needsUpdate = true; }
  if (!R3.gren) { R3.gren = []; }
  while (R3.gren.length < grenades.length) { const gg = new THREE.Group(); gg.add(new THREE.Mesh(sph(3.4, 8, 6), mat('#2f3a24'))); const ring = new THREE.Mesh(new THREE.RingGeometry(70, 84, 32), new THREE.MeshBasicMaterial({ color: 0xff2e4d, transparent: true, opacity: .6, depthWrite: false, side: THREE.DoubleSide })); ring.rotation.x = -PI / 2; gg.add(ring); gg.userData.ring = ring; R3.scene.add(gg); R3.gren.push(gg); }
  R3.gren.forEach((gg, i) => { const g2 = grenades[i]; gg.visible = !!g2; if (!g2) return; gg.children[0].position.set(g2.x, (g2.h || 0) + 4, g2.y); const ring = gg.userData.ring; ring.position.set(g2.tx, .9, g2.ty); ring.material.opacity = .25 + .45 * (Math.sin(S.time * 18) > 0 ? 1 : 0); });
  R3.bul.count = Math.min(nb, 300); R3.bulE.count = Math.min(ne, 300); R3.bul.instanceMatrix.needsUpdate = true; R3.bulE.instanceMatrix.needsUpdate = true;
  // particules
  const pos = R3.pts.geometry.attributes.position, colA = R3.pts.geometry.attributes.color; let n = 0;
  const spos = R3.smoke.geometry.attributes.position, scol = R3.smoke.geometry.attributes.color; let ns = 0;
  for (const p of parts) { if (p.grow) { if (ns < R3.MS) { const f = 1 - p.life / p.max, a = clamp(p.life / p.max, 0, 1), cc = col3(p.col); spos.setXYZ(ns, p.x, 14 + f * 50, p.y); scol.setXYZ(ns, cc.r * a + .1, cc.g * a + .1, cc.b * a + .12); ns++; } continue; }
    if (n >= R3.MAXP) break; const f = 1 - p.life / p.max; const cc = col3(p.col); const a = clamp(p.life / p.max, 0, 1);
    pos.setXYZ(n, p.x, p.grow ? 12 + f * 40 : 8 + (p.r > 6 ? f * 30 : 4), p.y); colA.setXYZ(n, cc.r * a, cc.g * a, cc.b * a); n++; }
  R3.pts.geometry.setDrawRange(0, n); pos.needsUpdate = true; colA.needsUpdate = true;
  R3.smoke.geometry.setDrawRange(0, ns); spos.needsUpdate = true; scol.needsUpdate = true;
  envFx(dt, playing);
  // cible de mission
  const st = playing && L.step, target = st ? stepTarget(st) : null;
  gpsUpdate(playing ? target : null, dt);
  if (!R3.gpsM) { R3.gpsM = new THREE.InstancedMesh(new THREE.ConeGeometry(7, 16, 3).rotateZ(-PI / 2), new THREE.MeshBasicMaterial({ color: 0xffd23f, transparent: true, opacity: .85, depthWrite: false }), 260); R3.gpsM.frustumCulled = false; R3.gpsM.instanceMatrix.setUsage(THREE.DynamicDrawUsage); R3.scene.add(R3.gpsM); }
  { let n2 = 0; const path = gps.path, off = (S.time * 90) % 46, qx = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), -PI / 2), qflat = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), -PI / 2);
    let acc = 0;
    for (let i = 1; i < path.length && n2 < 260; i++) { const a2 = path[i - 1], b2 = path[i], L2 = dist(a2.x, a2.y, b2.x, b2.y), ang = Math.atan2(b2.y - a2.y, b2.x - a2.x);
      for (let d2 = (off - acc % 46 + 46) % 46; d2 < L2 && n2 < 260; d2 += 46) { const x = a2.x + Math.cos(ang) * d2, y = a2.y + Math.sin(ang) * d2; if (dist(x, y, P.x, P.y) < 40) continue;
        R3.v.set(x, 2, y); R3.q.setFromAxisAngle(R3.up, -ang); R3.s.set(1, .25, 1); R3.m4.compose(R3.v, R3.q, R3.s); R3.gpsM.setMatrixAt(n2++, R3.m4); }
      acc += L2; }
    R3.q.identity(); R3.s.set(1, 1, 1); R3.gpsM.count = n2; R3.gpsM.instanceMatrix.needsUpdate = true;
    const urgent = st && st.time !== null && !st.survive && gps.len / (P.car ? 300 : 150) > st.time * .8; R3.gpsM.material.color.set(urgent ? 0xff4d5e : 0xffd23f); }
  R3.ring.visible = R3.beam.visible = !!target; if (target && Math.hypot(target.x - R3.cam.position.x, target.y - R3.cam.position.z) < 150) R3.beam.visible = false; R3.beam.material.opacity = (save.cam || 'top') === 'top' ? .16 : .06;
  if (target) { const pu = 1 + .12 * Math.sin(S.time * 4); R3.ring.position.set(target.x, 2, target.y); R3.ring.scale.setScalar(pu); R3.beam.position.set(target.x, 150, target.y); }
  R3.arrow.visible = !!(target && dist(P.x, P.y, target.x, target.y) > 200 && gps.path.length < 2);
  if (R3.arrow.visible) { const a = Math.atan2(target.y - P.y, target.x - P.x), r = P.car ? 58 : 42; R3.arrow.position.set(P.x + Math.cos(a) * r, 6, P.y + Math.sin(a) * r); R3.arrow.rotation.y = -a; }
  if (!R3.lockRet) { const grp = new THREE.Group(), m2 = new THREE.MeshBasicMaterial({ color: 0xff2e4d, depthTest: false, transparent: true }); for (let k = 0; k < 4; k++) { const c2 = new THREE.Group(); c2.rotation.y = k * PI / 2; const b1 = new THREE.Mesh(bx(10, 1.6, 1.6), m2); b1.position.set(16, 0, 11); const b2 = new THREE.Mesh(bx(1.6, 1.6, 10), m2); b2.position.set(21, 0, 6); c2.add(b1, b2); grp.add(c2); } const dot = new THREE.Mesh(new THREE.RingGeometry(3, 4.2, 16), new THREE.MeshBasicMaterial({ color: 0xff2e4d, depthTest: false, side: THREE.DoubleSide })); dot.rotation.x = -PI / 2; grp.add(dot); grp.traverse(o2 => o2.renderOrder = 30); R3.scene.add(grp); R3.lockRet = grp; }
  { const lt = playing && P.lock && lockAlive(P.lock) ? P.lock : null; R3.lockRet.visible = !!lt; if (lt) { const k2 = Math.min(1, (S.time - (P.lockT || 0)) * 4), sc = 2.2 - 1.2 * k2, hy = lt === heli ? 150 : lt.hp === undefined ? 14 : 30; R3.lockRet.position.set(lt.x, hy, lt.y); R3.lockRet.scale.setScalar(sc * (lt === heli ? 2 : lt.hp === undefined ? 1.6 : 1)); R3.lockRet.rotation.y = S.time * 1.5; } }
  R3.me.visible = !!playing && (mode === 'top' || R3.hidden); if (playing) R3.me.position.set(P.x, 1, P.y);
  // visée souris : on projette le pointeur sur le sol
  R3.ndc.set(mouse.sx / VW * 2 - 1, -(mouse.sy / VH) * 2 + 1); R3.ray.setFromCamera(R3.ndc, R3.cam);
  if (R3.ray.ray.intersectPlane(R3.plane, R3.hit)) { mouse.wx = R3.hit.x; mouse.wy = R3.hit.z; }
  cineCamera(playing);
  { const nn = (Math.cos((playing ? S.tod || 0 : .95) * TAU) + 1) / 2; R3.r.toneMappingExposure = .82 + nn * .43; }
  if (R3.composer && qLevel === 'high') { const night = (Math.cos((playing ? S.tod || 0 : .95) * TAU) + 1) / 2; R3.bloom.strength = .12 + night * .95; R3.bloom.threshold = .9 - night * .2; R3.composer.render(); } else R3.r.render(R3.scene, R3.cam);
  if (playing) drawMini(target);
}

// ---------- écrans ----------
const screenEl = $('screen');
let shopReturn = null;
function showScreen(name, data) {
  S.screen = name;
  const hudOn = !name || name === 'pause';
  document.body.classList.toggle('playing', !name);
  touchEl.hidden = !(touch.on && !name);
  if (!name) { screenEl.hidden = true; screenEl.innerHTML = ''; return; }
  screenEl.hidden = false;
  screenEl.innerHTML = SCREENS[name](data || {});
  if (I18) I18.dom(screenEl);
  screenEl.scrollTop = 0;
  const f = screenEl.querySelector('[autofocus],.btn.primary'); if (f) setTimeout(() => f.focus({ preventScroll: true }), 30);
  void hudOn;
}
const money = () => `<span class="pill money">${fmt(save.money)}</span>`;
const SCREENS = {
  home: () => {
    const done = Object.keys(save.done).length;
    return `<div class="wrap home">
      <h1 class="logo">NÉON<br><span>BAY</span></h1>
      <p class="lead">De Néon Bay aux favelas de Morro Azul : 30 niveaux, 4 pays, 300 étapes. Monte ton équipement, soudoie les agents, passe par les tunnels et fais tomber les chefs des gangs.</p>
      <div class="row center">
        <button class="btn primary" data-go="map">${done ? 'Continuer' : 'Jouer'}</button>
        <button class="btn" data-go="shop">Boutique</button>
        <button class="btn" data-go="trophies">Succès</button>
        ${save.premium || PORTAL ? '' : `<button class="btn gold" data-go="unlock">Jeu complet${priceLabel() ? ' · ' + priceLabel() : ''}</button>`}
        ${canFull() ? '<button class="btn" data-full="1">Plein écran</button>' : ''}
      </div><div class="row center">${AU ? `<button class="btn small" data-snd="music">Musique : ${AU.prefs.music ? 'oui' : 'non'}</button><button class="btn small" data-snd="sfx">Bruitages : ${AU.prefs.sfx ? 'oui' : 'non'}</button>` : ''}<button class="btn small" data-camset="1">Caméra : ${(CAMS.find(c => c[0] === (save.cam || 'top')) || CAMS[0])[1]}</button>${canVib() ? `<button class="btn small" data-vib="1">Vibrations : ${save.vib === false ? 'non' : 'oui'}</button>` : ''}<button class="btn small" data-qual="1">Qualité : ${qualityLabel()}</button><button class="btn small" data-ghost="1">Traverser les immeubles : ${save.ghost === false ? 'non' : 'oui'}</button>
      </div>
      <div class="row center langs">${I18 ? I18.LANGS.map(l => `<button class="btn small ${I18.lang === l ? 'on' : ''}" data-lang="${l}">${I18.NAMES[l]}</button>`).join('') : ''}</div>
      ${dailyHtml()}
      <div class="stats"><span>${done}/30 niveaux</span><span>${Object.keys(save.ach || {}).length}/${ACH.length} succès</span><span>${Object.values(save.tagsFound || {}).reduce((a, v) => a + v.length, 0)}/48 tags secrets</span><span>${fmt(save.money)}</span><span>${save.premium ? 'Version complète' : 'Niveau 1 gratuit'}</span></div>
      <div class="keys">
        <b>ZQSD / flèches</b><span>Marcher, conduire</span>
        <b>E</b><span>Voiture, boutique, tunnel, payer un agent</span>
        <b>Espace / clic</b><span>Tirer · frein à main en voiture</span>
        <b>Q / molette / 1-8 · R</b><span>Changer d'arme · recharger</span>
        <b>B</b><span>Soudoyer la police</span>
        <b>H · N / Maj</b><span>Trousse de soins · nitro</span>
        <b>C</b><span>Changer de caméra (dessus, poursuite, embarquée)</span>
        <b>Tab / clic droit</b><span>Verrouiller une cible, puis la suivante</span>
        <b>T</b><span>Changer de station de radio</span>
      </div>
      <p class="legal">Jeu original. Lieux, gangs et personnages sont inventés.</p>
    </div>`;
  },
  map: () => {
    return `<div class="wrap">
      <div class="top"><button class="btn small" data-go="home">← Menu</button><h2>Carte des niveaux</h2><div class="row">${money()}<button class="btn small" data-go="shop">Boutique</button></div></div>
      ${D.REGIONS.map(r => `<section class="region" style="--acc:${r.accent}">
        <div class="rhead"><h3>${r.name}</h3><span>${r.country} · niveaux ${r.from}–${r.to}</span><p>${r.tagline}</p></div>
        <div class="grid">${D.LEVELS.slice(r.from - 1, r.to).map((l, i) => { const n = r.from + i; const ok = save.done[n], open = n <= save.maxLevel, paid = n > 1 && !save.premium && !PORTAL;
          const cls = ok ? 'done' : open ? (paid ? 'paid' : 'open') : 'locked';
          const tag = ok ? '✓ Terminé' : paid ? 'Version complète' : open ? 'Disponible' : 'Verrouillé';
          return `<button class="lvl ${cls}" data-lvl="${n}"><span class="num">${n}</span><span class="lt">${esc(l.t)}</span><span class="tag">${tag}</span><span class="st">${save.stars && save.stars[n] ? starStr(save.stars[n]) : ''}</span><span class="rw">+${fmt(levelBonus(n) + stepReward(n) * 10)}</span></button>`; }).join('')}</div>
      </section>`).join('')}
    </div>`;
  },
  trophies: () => {
    const st = save.stats || {}, got = save.ach || {};
    return `<div class="wrap narrow">
      <div class="top"><button class="btn small" data-go="home">← Menu</button><h2>Succès</h2>${money()}</div>
      ${dailyHtml()}
      <div class="ach">${ACH.map(a => { const v = Math.min(a.goal, st[a.key] || 0), ok = !!got[a.id]; return `<div class="a ${ok ? 'ok' : ''}"><div><b>${esc(a.name)}</b><span>${STAT_LABEL[a.key].replace('{n}', a.goal.toLocaleString('fr-FR'))}</span><div class="pbar"><i style="width:${Math.round(v / a.goal * 100)}%"></i></div></div><em>${ok ? '✓' : '+' + fmt(a.r)}</em></div>`; }).join('')}</div>
    </div>`;
  },
  brief: ({ n }) => {
    const l = D.LEVELS[n - 1], r = regionOf(n);
    const recW = D.WEAPONS.filter(w => w.lvl <= n && w.price > 0).slice(-1)[0];
    return `<div class="wrap narrow" style="--acc:${r.accent}">
      <div class="top"><button class="btn small" data-go="map">← Carte</button>${money()}</div>
      <p class="eyebrow">${r.name} · ${r.country} · Niveau ${n}/30</p>
      <h2 class="title">${esc(l.t)}</h2>
      <p class="lead">${esc(l.s)}</p>
      <ol class="steps">${l.steps.map(s => `<li>${D.STEP_LABEL[s]}</li>`).join('')}</ol>
      <div class="info"><span>Récompense : <b>${fmt(levelBonus(n))}</b> + ${fmt(stepReward(n))} par étape</span>${save.fails && save.fails[n] >= 2 ? '<span class="assist">Aide activée : plus de temps et ennemis moins dangereux</span>' : ''}${l.boss ? `<span>Chef à abattre : <b>${esc(l.boss)}</b></span>` : ''}${recW && !save.owned[recW.id] ? `<span>Conseillé : ${recW.name}</span>` : ''}</div>
      <div class="row"><button class="btn primary" data-start="${n}">Commencer</button><button class="btn" data-go="shop" data-ret="brief:${n}">Boutique</button></div>
    </div>`;
  },
  shop: ({ inGame, tab = 'w' }) => {
    const n = Math.max(save.maxLevel, 1);
    const card = (it, isW) => {
      const owned = isW ? save.owned[it.id] : it.kind === 'armor' ? save.armor >= it.value : it.kind === 'perk' ? save.perks[it.id] : false;
      const locked = it.lvl > n;
      let btn;
      if (locked) btn = `<span class="lock">Niveau ${it.lvl}</span>`;
      else if (isW && owned) btn = save.weapon === it.id ? `<span class="eq">Équipée</span>` : `<button class="btn small" data-equip="${it.id}">Équiper</button>`;
      else if (owned) btn = `<span class="eq">Acheté</span>`;
      else { const cnt = it.kind === 'medkit' ? ` (${save.medkits}/${it.max})` : it.kind === 'nitro' ? ` (${save.nitro}/${it.max})` : ''; btn = `<button class="btn small ${save.money >= it.price ? 'primary' : ''}" data-buy="${it.id}">${fmt(it.price)}${cnt}</button>`; }
      const stat = isW ? `<div class="stat"><i style="width:${Math.min(100, it.dmg * it.pellets / 1.4)}%"></i></div><div class="stat r"><i style="width:${Math.min(100, 8 / it.rate)}%"></i></div>` : '';
      return `<div class="item ${locked ? 'is-locked' : ''}"><div><h4>${it.name}</h4><p>${it.desc}</p>${stat}</div>${btn}</div>`;
    };
    return `<div class="wrap">
      <div class="top"><button class="btn small" data-back="1">${inGame ? '← Reprendre' : '← Retour'}</button><h2>Boutique</h2>${money()}</div>
      <div class="tabs"><button class="${tab === 'w' ? 'on' : ''}" data-tab="w">Armes</button><button class="${tab === 'g' ? 'on' : ''}" data-tab="g">Équipement</button><button class="${tab === 'a' ? 'on' : ''}" data-tab="a">Atelier</button><button class="${tab === 'o' ? 'on' : ''}" data-tab="o">Tenues</button></div>
      ${tab === 'a' ? armoryHtml() : tab === 'o' ? outfitHtml() : `<div class="items">${(tab === 'w' ? D.WEAPONS.filter(w => !w.melee) : D.GEAR).map(it => card(it, tab === 'w')).join('')}</div>`}
      ${tab === 'w' ? '<p class="legend"><span class="k1"></span>Dégâts <span class="k2"></span>Cadence</p>' : ''}
    </div>`;
  },
  break: ({ h }) => `<div class="wrap narrow center-col">
      <p class="eyebrow">Pause conseillée</p><h2 class="title">Ça fait ${h} heure${h > 1 ? 's' : ''} que tu joues</h2>
      <p class="lead">Comme au volant : une pause toutes les heures, c'est mieux. Lève-toi, bois un verre d'eau, repose tes yeux quelques minutes. Ta partie t'attend.</p>
      <div class="col"><button class="btn primary" data-quit="1">Faire une pause</button><button class="btn" data-resume="1">Continuer encore un peu</button></div>
    </div>`,
  pause: () => `<div class="wrap narrow center-col">
      <h2 class="title">Pause</h2>
      <p class="lead">Niveau ${L.n} · ${esc(L.def.t)} · étape ${L.idx + 1}/10</p>
      <div class="col"><button class="btn primary" data-resume="1">Reprendre</button><button class="btn" data-start="${L.n}">Recommencer le niveau</button><button class="btn" data-photo="1">Photo à partager</button><button class="btn" data-quit="1">Quitter vers la carte</button>${canFull() ? '<button class="btn" data-full="1">Plein écran</button>' : ''}<div class="row center">${AU ? `<button class="btn small" data-snd="music">Musique : ${AU.prefs.music ? 'oui' : 'non'}</button><button class="btn small" data-snd="sfx">Bruitages : ${AU.prefs.sfx ? 'oui' : 'non'}</button>` : ''}<button class="btn small" data-camset="1">Caméra : ${(CAMS.find(c => c[0] === (save.cam || 'top')) || CAMS[0])[1]}</button>${canVib() ? `<button class="btn small" data-vib="1">Vibrations : ${save.vib === false ? 'non' : 'oui'}</button>` : ''}<button class="btn small" data-qual="1">Qualité : ${qualityLabel()}</button><button class="btn small" data-ghost="1">Traverser les immeubles : ${save.ghost === false ? 'non' : 'oui'}</button></div></div>
    </div>`,
  result: d => {
    const r = regionOf(d.n);
    if (d.ok) {
      const next = d.n + 1;
      return `<div class="wrap narrow center-col" style="--acc:${r.accent}">
        <p class="eyebrow">Niveau ${d.n} terminé</p><h2 class="title big">MISSION RÉUSSIE</h2>
        <div class="bigstars" aria-label="${d.sc.stars} étoiles sur 3">${starStr(d.sc.stars)}</div>
        <ul class="crit"><li class="${'ok'}">Mission accomplie</li><li class="${d.sc.fast ? 'ok' : ''}">Rapide : moins de ${Math.floor(parTime(d.n) / 60)} min ${String(parTime(d.n) % 60).padStart(2, '0')}</li><li class="${d.sc.clean ? 'ok' : ''}">Propre : santé ≥ 60 % et 3 passants K.O. maximum (${d.kos})</li></ul>
        <div class="info"><span>Bonus de fin : <b>${fmt(d.bonus)}</b></span><span>Total gagné : <b>${fmt(d.earned)}</b></span><span>Temps : <b>${Math.floor(d.time / 60)} min ${String(Math.floor(d.time % 60)).padStart(2, '0')}</b></span></div>
        ${PORTAL ? `<button class="btn gold" data-rewarded="${d.bonus}">Doubler le bonus (vidéo) · +${fmt(d.bonus)}</button>` : ''}
        ${!save.premium && !PORTAL && d.n === 1 ? `<div class="offer"><b>Tu as aimé ? La suite t'attend.</b><span>29 niveaux de plus en Italie, en Colombie et au Brésil, 7 chefs de gang, le lance-roquettes et le minigun.</span><button class="btn gold" data-go="unlock">Débloquer le jeu complet${priceLabel() ? ' · ' + priceLabel() : ''}</button></div>` : ''}
        ${d.unlocks.length ? `<p class="lead">Nouveau dans la boutique : ${d.unlocks.map(u => u.name).join(', ')}</p>` : ''}
        ${next > 30 ? '<p class="lead">Tu as terminé les 30 niveaux. Morro Azul est à toi.</p>' : ''}
        <div class="col">${next <= 30 ? `<button class="btn primary" data-lvl="${next}">Niveau suivant</button>` : ''}<button class="btn" data-go="shop" data-ret="map">Boutique</button><button class="btn" data-go="map">Carte</button></div>
      </div>`;
    }
    return `<div class="wrap narrow center-col" style="--acc:${r.accent}">
      <p class="eyebrow">Niveau ${d.n}</p><h2 class="title big fail">ÉCHEC</h2>
      <p class="lead">${esc(d.reason)}. L'argent gagné pendant la tentative est conservé (${fmt(d.earned)}).</p>
      <div class="col"><button class="btn primary" data-start="${d.n}">Réessayer</button><button class="btn" data-go="shop" data-ret="brief:${d.n}">Boutique</button><button class="btn" data-go="map">Carte</button></div>
    </div>`;
  },
  unlock: ({ msg: m }) => {
    const url = D.SHOP_CONFIG.buyUrl;
    return `<div class="wrap narrow">
      <div class="top"><button class="btn small" data-go="map">← Carte</button></div>
      <p class="eyebrow">Version complète</p><h2 class="title">Débloque les 29 niveaux</h2>
      <ul class="feat"><li>Italie, Colombie et favelas du Brésil</li><li>290 étapes de plus et 7 chefs de gang</li><li>Lance-roquettes, minigun, armure tactique</li><li>Paiement unique, sans abonnement</li></ul>
      ${isPlay() ? `
      ${ST.state.price ? `<div class="price">${esc(ST.state.price)}</div>` : ''}
      <button class="btn primary" data-playbuy="1">Acheter le jeu complet</button>
      <button class="btn small" data-restore="1">Restaurer mes achats</button>
      ${ST.state.error ? `<p class="note bad">${esc(ST.state.error)}</p>` : ''}` : `
      <div class="price">${D.SHOP_CONFIG.price}</div>
      ${url ? `<a class="btn primary" href="${esc(url)}" target="_blank" rel="noopener">Acheter le jeu complet</a>` : `<p class="note">Le lien de paiement n'est pas encore configuré (SHOP_CONFIG.buyUrl dans js/data.js).</p>`}`}
      <label class="lab" for="code">Tu as déjà un code ?</label>
      <div class="row"><input id="code" placeholder="NBAY-XXXX-XXXX-XXXX" autocomplete="off" spellcheck="false"><button class="btn" data-code="1">Valider</button></div>
      ${m ? `<p class="note ${m.ok ? 'ok' : 'bad'}">${esc(m.t)}</p>` : ''}
    </div>`;
  },
};
function armoryHtml() {
  const owned = D.WEAPONS.filter(w => !w.melee && save.owned[w.id]);
  if (!shopState.aw || !save.owned[shopState.aw] || WBASE(shopState.aw).melee) shopState.aw = save.weapon !== 'fists' ? save.weapon : 'pistol';
  const id = shopState.aw, b = WBASE(id), w = wepDef(id), u = wup(id);
  const bar = (v, max, col) => `<div class="stat2"><i style="width:${Math.min(100, v / max * 100)}%;background:${col}"></i></div>`;
  const rows = [['dmg', 'Dégâts', b.dmg * b.pellets, w.dmg * w.pellets, 140, '#ff2e93'], ['mag', 'Chargeur', b.mag || 0, w.mag || 0, 200, '#ffb627'], ['rate', 'Cadence', 1 / b.rate, 1 / w.rate, 25, '#21e6ff'], ['acc', 'Précision', 1 - b.spread, 1 - w.spread, 1, '#a6ff4d']];
  return `<div class="armory"><div class="wlist">${owned.map(o => `<button class="chip ${o.id === id ? 'on' : ''}" data-aw="${o.id}">${esc(o.name)}</button>`).join('')}</div>
    <div class="wview"><div id="gunViewSlot"></div><h3>${esc(b.name)}</h3><p>${esc(b.desc)}</p></div>
    <div class="wups">${rows.map(([k, label, bv, nv, max, col]) => { const l = u[k] || 0, maxed = l >= 3 || (k === 'mag' && !b.mag) || (k === 'acc' && !b.spread);
      return `<div class="wup"><div class="wh"><b>${label}</b><span>${'■'.repeat(l)}${'□'.repeat(3 - l)}</span></div>${bar(nv, max, col)}${maxed ? `<span class="eq">${l >= 3 ? 'Maximum' : '—'}</span>` : `<button class="btn small ${save.money >= upPrice(id, k) ? 'primary' : ''}" data-up="${k}">Améliorer · ${fmt(upPrice(id, k))}</button>`}</div>`; }).join('')}
      <div class="wup"><div class="wh"><b>Peinture</b></div><div class="chips">${SKINS.map(([sid, name, price, col]) => { const own = !price || (save.skinsOwned || {})[sid], on = (u.skin || 'black') === sid; return `<button class="chip ${on ? 'on' : ''}" data-skin="${sid}"><i style="background:${col}"></i>${esc(name)}${own ? '' : `<small>${fmt(price)}</small>`}</button>`; }).join('')}</div></div>
    </div></div>`;
}
let gunView = null;
function mountGunView() {
  const slot = document.getElementById('gunViewSlot'); if (!slot || !R3.ok) return;
  if (!gunView) {
    const cv = document.createElement('canvas'); cv.width = 520; cv.height = 300; cv.className = 'gunview';
    let r; try { r = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: true }); } catch (e) { return; }
    const sc = new THREE.Scene(), cam2 = new THREE.PerspectiveCamera(32, 520 / 300, 1, 400); cam2.position.set(0, 10, 62); cam2.lookAt(0, 0, 0);
    sc.add(new THREE.HemisphereLight(0xffffff, 0x302040, 1.1)); const dl = new THREE.DirectionalLight(0xffffff, .8); dl.position.set(20, 40, 30); sc.add(dl);
    const pivot = new THREE.Group(); sc.add(pivot);
    const ring = new THREE.Mesh(new THREE.RingGeometry(18, 19.5, 48), new THREE.MeshBasicMaterial({ color: 0x21e6ff, transparent: true, opacity: .5, side: THREE.DoubleSide })); ring.rotation.x = -PI / 2; ring.position.y = -9; sc.add(ring);
    gunView = { cv, r, sc, cam2, pivot, key: '' };
    const loop = () => { if (gunView.cv.isConnected) { gunView.pivot.rotation.y += .012; gunView.r.render(gunView.sc, gunView.cam2); } requestAnimationFrame(loop); }; loop();
  }
  slot.appendChild(gunView.cv);
  const id = shopState.aw, key = id + '|' + (wup(id).skin || 'black');
  if (gunView.key !== key) { gunView.key = key; while (gunView.pivot.children.length) gunView.pivot.remove(gunView.pivot.children[0]); const gm = makeGun(id, wup(id).skin || 'black'); if (gm) { const box = new THREE.Box3().setFromObject(gm), c = box.getCenter(new THREE.Vector3()), sz = box.getSize(new THREE.Vector3()); gm.position.sub(c); const k = 34 / Math.max(sz.x, sz.y, sz.z); const holder = new THREE.Group(); holder.add(gm); holder.scale.setScalar(k); gunView.pivot.add(holder); } }
}
function outfitHtml() {
  return `<div class="wardrobe"><canvas id="outfitPrev" width="180" height="250" aria-label="Aperçu de ton personnage"></canvas><div class="cats">${Object.entries(D.OUTFITS).map(([cat, c]) => `<div class="cat"><b>${c.label}</b><div class="chips">${c.items.map(([id, name, price, val]) => {
    const owned = !price || save.wardrobe[cat + ':' + id], on = save.outfit[cat] === id;
    const sw = cat === 'hair' ? outfitVal('hairColor') : cat === 'chain' ? (val ? '#ffd700' : 'transparent') : (val || 'transparent');
    return `<button class="chip ${on ? 'on' : ''}" data-outfit="${cat}:${id}"><i style="background:${sw}"></i>${esc(name)}${owned ? '' : `<small>${fmt(price)}</small>`}</button>`; }).join('')}</div></div>`).join('')}</div></div>`;
}
function drawOutfitPreview() {
  const cv = document.getElementById('outfitPrev'); if (!cv) return;
  const x = cv.getContext('2d'), L2 = playerLook(); x.clearRect(0, 0, 180, 250);
  const rect = (c, a, b, w, h, r = 4) => { if (!c) return; x.fillStyle = c; x.beginPath(); x.roundRect ? x.roundRect(a, b, w, h, r) : x.rect(a, b, w, h); x.fill(); };
  x.fillStyle = 'rgba(0,0,0,.35)'; x.beginPath(); x.ellipse(90, 238, 44, 8, 0, 0, TAU); x.fill();
  rect(L2.pants, 66, 150, 21, 78, 6); rect(L2.pants, 93, 150, 21, 78, 6);
  rect(L2.shoes, 60, 222, 28, 12, 5); rect(L2.shoes, 92, 222, 28, 12, 5);
  rect(L2.shirt, 58, 86, 64, 72, 12);
  if (L2.jacket) { rect(L2.jacket, 56, 86, 22, 72, 10); rect(L2.jacket, 102, 86, 22, 72, 10); rect(L2.jacket, 56, 86, 68, 16, 10); }
  rect(L2.sleeve, 40, 90, 16, 54, 7); rect(L2.sleeve, 124, 90, 16, 54, 7);
  rect(L2.skin, 41, 140, 14, 14, 7); rect(L2.skin, 125, 140, 14, 14, 7);
  if (L2.chain) { x.strokeStyle = '#ffd700'; x.lineWidth = 3; x.beginPath(); x.arc(90, 92, 16, .2, PI - .2); x.stroke(); }
  rect(L2.skin, 82, 72, 16, 16, 4);
  x.fillStyle = L2.skin; x.beginPath(); x.ellipse(90, 52, 24, 27, 0, 0, TAU); x.fill();
  const hs = L2.hairStyle;
  if (!L2.hat && hs !== 'none') { x.fillStyle = L2.hair; if (hs === 'afro') { x.beginPath(); x.arc(90, 38, 32, 0, TAU); x.fill(); } else { x.beginPath(); x.ellipse(90, 36, 25, 16, 0, PI, 0); x.fill(); if (hs === 'long') rect(L2.hair, 64, 36, 52, 52, 10); if (hs === 'ponytail') { x.beginPath(); x.arc(118, 46, 9, 0, TAU); x.fill(); } } x.fillStyle = L2.skin; x.beginPath(); x.ellipse(90, 56, 20, 21, 0, 0, TAU); x.fill(); }
  if (L2.hat) { rect(L2.hat, 64, 22, 52, 18, 9); rect(L2.hat, 86, 34, 40, 7, 3); }
  x.fillStyle = '#fff'; x.beginPath(); x.ellipse(81, 54, 4.5, 3.5, 0, 0, TAU); x.ellipse(99, 54, 4.5, 3.5, 0, 0, TAU); x.fill();
  x.fillStyle = '#17110c'; x.beginPath(); x.arc(81, 54, 2.2, 0, TAU); x.arc(99, 54, 2.2, 0, TAU); x.fill();
  x.fillStyle = '#7a3a3a'; x.fillRect(84, 66, 12, 2.5);
}
function dailyHtml() {
  const d = ensureDaily();
  return `<div class="daily"><div class="dh"><b>Défis du jour</b><span>${save.streak ? 'Série : ' + save.streak + ' jour' + (save.streak > 1 ? 's' : '') + ' · ' : ''}+${fmt(dailyReward())} chacun</span></div>${d.items.map(it => `<div class="dl ${it.done ? 'ok' : ''}"><span>${STAT_LABEL[it.key].replace('{n}', it.goal)}</span><div class="pbar"><i style="width:${Math.round(it.prog / it.goal * 100)}%"></i></div><em>${it.done ? '✓' : it.prog + '/' + it.goal}</em></div>`).join('')}</div>`;
}
function takePhoto() {
  if (!R3.ok) return;
  screenEl.hidden = true; R3.r.render(R3.scene, R3.cam);
  const src = $('game3d'), cv = document.createElement('canvas'); cv.width = src.width; cv.height = src.height; const x = cv.getContext('2d');
  x.drawImage(src, 0, 0);
  const fs = Math.round(cv.height * .05); x.font = `900 ${fs}px Bungee, "Arial Black", sans-serif`; x.textAlign = 'right'; x.shadowColor = '#ff2e93'; x.shadowBlur = fs * .5; x.fillStyle = '#ffffff';
  x.fillText('NÉON BAY', cv.width - fs * .6, cv.height - fs * .7); x.shadowBlur = 0; x.font = `700 ${Math.round(fs * .4)}px "Chakra Petch", sans-serif`; x.fillStyle = '#ffb627'; x.fillText(TR('Niveau') + ' ' + (L ? L.n : 1) + ' · ' + world.region.name, cv.width - fs * .6, cv.height - fs * .2);
  screenEl.hidden = false;
  cv.toBlob(async blob => {
    if (!blob) return; const file = new File([blob], 'neon-bay.png', { type: 'image/png' });
    try { if (navigator.canShare && navigator.canShare({ files: [file] })) { await navigator.share({ files: [file], title: 'Néon Bay', text: TR('Regarde ma partie de Néon Bay !') }); return; } } catch (e) {}
    try { const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'neon-bay.png'; document.body.appendChild(a); a.click(); a.remove(); flashNote('Photo enregistrée'); } catch (e) { flashNote('Photo impossible ici'); }
  }, 'image/png');
}
function canFull() { return !!(document.fullscreenEnabled || document.webkitFullscreenEnabled); }
function toggleFull() {
  try {
    const d = document, el = d.documentElement;
    if (d.fullscreenElement || d.webkitFullscreenElement) { (d.exitFullscreen || d.webkitExitFullscreen).call(d); return; }
    const r = (el.requestFullscreen || el.webkitRequestFullscreen).call(el);
    if (r && r.then) r.then(() => { try { screen.orientation && screen.orientation.lock && screen.orientation.lock('landscape').catch(() => {}); } catch (e) {} }).catch(() => flashNote('Plein écran indisponible ici'));
  } catch (e) { flashNote('Plein écran indisponible ici'); }
}
let shopState = { inGame: false, tab: 'w', ret: 'home' };
function openShop(inGame, ret) { shopState = { inGame, tab: 'w', ret: ret || (S.screen || 'home') }; if (inGame) { S.mode = 'shop'; if (L) L.bought = true; } showScreen('shop', shopState); }
function buy(id) {
  const w = D.WEAPONS.find(x => x.id === id), g = D.GEAR.find(x => x.id === id), it = w || g;
  if (!it || save.money < it.price) { au('deny'); flashNote('Pas assez d’argent'); return; }
  au('buy');
  if (g && g.kind === 'medkit' && save.medkits >= g.max) return;
  if (g && g.kind === 'nitro' && save.nitro >= g.max) return;
  save.money -= it.price;
  if (w) { save.owned[id] = true; save.weapon = id; }
  else if (g.kind === 'armor') { save.armor = Math.max(save.armor, g.value); if (S.mode === 'shop') P.armor = save.armor; }
  else if (g.kind === 'medkit') save.medkits++;
  else if (g.kind === 'nitro') save.nitro = Math.min(g.max, save.nitro + 3);
  else save.perks[id] = true;
  if (L && S.mode === 'shop') L.bought = true;
  persist(); showScreen('shop', shopState);
}
function flashNote(t) { const n = document.createElement('div'); n.className = 'flash'; n.textContent = TR(t); screenEl.appendChild(n); setTimeout(() => n.remove(), 1500); }
function pauseGame() { if (S.mode !== 'play') return; $('rotate').hidden = true; S.rot = false; if (PORTAL) PORTAL.stop(); S.mode = 'pause'; au('duck', true); showScreen('pause'); }
function resumeGame() { if (PORTAL) PORTAL.start(); S.mode = 'play'; au('duck', false); showScreen(null); lastT = performance.now(); }
function goLevel(n) { if (n > 1 && !save.premium && !PORTAL) { showScreen('unlock'); return; } if (n > save.maxLevel) { flashNote('Termine le niveau ' + (n - 1) + ' d’abord'); return; } showScreen('brief', { n }); }
screenEl.addEventListener('click', e => {
  const b = e.target.closest('button,a'); if (!b) return;
  const ds = b.dataset;
  if (AU) { AU.init(); au('click'); if (!L || S.mode === 'menu') au('setMusic', 'menu'); }
  if (ds.lang) { I18.set(ds.lang); save.lang = ds.lang; persist(); last.ln = last.sn = last.sd = last.m = last.w = last.inv = null; for (const k in last) last[k] = undefined; if (R3.ok) R3.world = null; I18.dom(document.getElementById('touch')); showScreen(S.screen); return; }
  if (ds.photo) { takePhoto(); return; }
  if (ds.ghost) { save.ghost = save.ghost === false; persist(); showScreen(S.screen); return; }
  if (ds.camset) { const i = CAMS.findIndex(c => c[0] === (save.cam || 'top')); save.cam = CAMS[(i + 1) % CAMS.length][0]; persist(); showScreen(S.screen); return; }
  if (ds.qual) { const opts = ['auto', 'high', 'medium', 'low'], i = opts.indexOf(save.quality || 'auto'); save.quality = opts[(i + 1) % opts.length]; persist(); setQuality(save.quality === 'auto' ? (touch.on ? 'medium' : 'high') : save.quality); showScreen(S.screen); return; }
  if (ds.vib) { save.vib = save.vib === false; persist(); if (save.vib) vib(60); showScreen(S.screen); return; }
  if (ds.snd) { AU && AU.toggle(ds.snd); showScreen(S.screen === 'pause' ? 'pause' : S.screen); return; }
  if (ds.go === 'shop') { openShop(false, ds.ret || S.screen); return; }
  if (ds.go) { if (ds.go === 'map') { S.mode = 'menu'; L = null; au('setMusic', 'menu'); } showScreen(ds.go); return; }
  if (ds.lvl) { goLevel(+ds.lvl); return; }
  if (ds.start) { const n = +ds.start; if (canPlay(n)) { if (PORTAL && S.levelsStarted) PORTAL.breakAd().then(() => startLevel(n)); else startLevel(n); } else goLevel(n); return; }
  if (ds.rewarded) { b.disabled = true; PORTAL.rewarded().then(ok => { if (ok) { save.money += +ds.rewarded; persist(); au('cash'); flashNote('+' + fmt(+ds.rewarded)); b.remove(); } else b.disabled = false; }); return; }
  if (ds.tab) { shopState.tab = ds.tab; showScreen('shop', shopState); if (ds.tab === 'o') drawOutfitPreview(); if (ds.tab === 'a') mountGunView(); return; }
  if (ds.aw) { shopState.aw = ds.aw; showScreen('shop', shopState); mountGunView(); return; }
  if (ds.up) { const id = shopState.aw, pr = upPrice(id, ds.up); if (save.money < pr) { au('deny'); flashNote('Pas assez d\u2019argent'); return; } save.money -= pr; save.wup = save.wup || {}; save.wup[id] = Object.assign({}, save.wup[id]); save.wup[id][ds.up] = (save.wup[id][ds.up] || 0) + 1; if (P.ammo && P.ammo[id] && ds.up === 'mag') P.ammo[id].mag = wepDef(id).mag; au('buy'); persist(); showScreen('shop', shopState); mountGunView(); return; }
  if (ds.skin) { const sk = SKINS.find(x => x[0] === ds.skin); save.skinsOwned = save.skinsOwned || {}; if (sk[2] && !save.skinsOwned[sk[0]]) { if (save.money < sk[2]) { au('deny'); flashNote('Pas assez d\u2019argent'); return; } save.money -= sk[2]; save.skinsOwned[sk[0]] = 1; au('buy'); } save.wup = save.wup || {}; save.wup[shopState.aw] = Object.assign({}, save.wup[shopState.aw], { skin: sk[0] }); persist(); showScreen('shop', shopState); mountGunView(); return; }
  if (ds.outfit) {
    const [cat, id] = ds.outfit.split(':'), it = D.OUTFITS[cat].items.find(i => i[0] === id), price = it[2];
    if (price && !save.wardrobe[cat + ':' + id]) { if (save.money < price) { au('deny'); flashNote('Pas assez d\u2019argent'); return; } save.money -= price; save.wardrobe[cat + ':' + id] = 1; au('buy'); }
    save.outfit[cat] = id; P._m = null; persist(); showScreen('shop', shopState); drawOutfitPreview(); return;
  }
  if (ds.buy) { buy(ds.buy); return; }
  if (ds.equip) { save.weapon = ds.equip; persist(); showScreen('shop', shopState); return; }
  if (ds.back) { if (shopState.inGame) { resumeGame(); return; } const r = shopState.ret || 'home'; if (r.startsWith('brief:')) showScreen('brief', { n: +r.split(':')[1] }); else showScreen(r === 'shop' ? 'home' : r); return; }
  if (ds.full) { toggleFull(); return; }
  if (ds.resume) { resumeGame(); return; }
  if (ds.quit) { S.mode = 'menu'; L = null; au('duck', false); au('setMusic', 'menu'); showScreen('map'); return; }
  if (ds.playbuy) {
    b.disabled = true;
    ST.buy().then(r => {
      if (r.ok) { save.premium = true; persist(); au('win'); showScreen('unlock', { msg: { ok: true, t: 'Merci ! Les 30 niveaux sont débloqués.' } }); setTimeout(() => { if (S.screen === 'unlock') showScreen('map'); }, 1400); }
      else showScreen('unlock', r.cancelled ? {} : { msg: { ok: false, t: 'Achat non abouti : ' + (r.error || 'erreur inconnue') } });
    });
    return;
  }
  if (ds.restore) {
    ST.restore().then(ok => {
      if (ok) { save.premium = true; persist(); showScreen('unlock', { msg: { ok: true, t: 'Achat retrouvé : les 30 niveaux sont débloqués.' } }); setTimeout(() => { if (S.screen === 'unlock') showScreen('map'); }, 1400); }
      else showScreen('unlock', { msg: { ok: false, t: 'Aucun achat trouvé sur ce compte Google.' } });
    });
    return;
  }
  if (ds.code) {
    const v = $('code').value;
    if (validCode(v)) { save.premium = true; persist(); showScreen('unlock', { msg: { ok: true, t: 'Code accepté : les 30 niveaux sont débloqués !' } }); setTimeout(() => { if (S.screen === 'unlock') showScreen('map'); }, 1400); }
    else showScreen('unlock', { msg: { ok: false, t: 'Ce code n’est pas valide. Vérifie les lettres et les tirets.' } });
  }
});
screenEl.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.id === 'code') screenEl.querySelector('[data-code]').click(); });

// ---------- boucle ----------
let lastT = performance.now();
function frame(t) {
  if (S.manual) { lastT = t; requestAnimationFrame(frame); return; }
  const dt = Math.min(.05, (t - lastT) / 1000); lastT = t;
  tick(dt);
  requestAnimationFrame(frame);
}
function tick(dt) {
  try { tickInner(dt); } catch (err) { S.errs = (S.errs || 0) + 1; if (S.errs < 4) console.error(err); if (S.errs === 3) toast('Petit souci technique, la partie continue'); }
}
function tickInner(dt) {
  if (S.mode === 'play') {
    let gdt = dt;
    if (S.cine) { S.cine.t = S.cine.start ? (performance.now() - S.cine.start) / 1000 : (S.cine.start = performance.now(), 0); gdt = S.cine.type === 'intro' ? 0 : dt * .18; if (S.cine.t >= S.cine.dur) { S.cine = null; hideCine(); } }
    S.tod = ((S.tod || 0) + gdt / 480) % 1;
    const rot = touch.on && innerHeight > innerWidth && !save.portraitOk; if (!!S.rot !== rot) { S.rot = rot; $('rotate').hidden = !rot; if (rot && save.cam) {} }
    if (rot) gdt = 0;
    if (gdt > 0 && !S.cine) { S.session = (S.session || 0) + dt; const td = today(); if (!save.playDay || save.playDay.d !== td) save.playDay = { d: td, s: 0 }; save.playDay.s += dt;
      if (!S.nextBreak) S.nextBreak = 3600; if (S.session >= S.nextBreak) { S.nextBreak += 3600; S.mode = 'pause'; if (PORTAL) PORTAL.stop(); au('duck', true); showScreen('break', { h: Math.round(S.session / 3600) }); persist(); } }
    if (gdt > 0) update(gdt); updHud(dt); updTips(gdt); monitorFps(dt);
  }
  if (AU && AU.ready) { let sd = 1e9; if (S.mode === 'play') for (const c of cars) if (c.kind === 'police' && c.ai === 'police') sd = Math.min(sd, dist(c.x, c.y, P.x, P.y)); var hd = heli ? dist(heli.x, heli.y, P.x, P.y) : 1e9; au('setIntensity', S.mode === 'play' && stars() > 0 ? 1 : 0); AU.update({ playing: S.mode === 'play', inCar: !!P.car, speed: P.car ? P.car.v : 0, nitro: P.nitro > 0, drift: !!(P.car && P.car.drift > .18), sirenDist: sd, heliDist: hd, rain: !!S.rain }, dt); }
  else if (S.mode === 'result') { for (const p of parts) { p.life -= dt; } }
  render(dt);
}
// décor du menu : la ville du premier pays
world = buildWorld(D.REGIONS[0]); P.x = cam.x = W / 2; P.y = cam.y = W / 2;
for (let i = 0; i < 60; i++) { const t = randWalk(0, W * 2, 0, 0); parkedCar(t.x, t.y); }
if (I18) { I18.set(I18.lang); I18.dom(document.getElementById('touch')); I18.dom(document.getElementById('cine')); I18.dom(document.getElementById('rotate')); }
init3D();
if (R3.ok) setupPost();
// modèles .glb animés (optionnels)
R3.models = {};
if (R3.ok && THREE.GLTFLoader && D.MODELS) for (const [k, url] of Object.entries(D.MODELS)) {
  const onGl = gl => { const scene = gl.scene; scene.traverse(o => { if (o.isMesh) { o.castShadow = !!R3.shadow; o.frustumCulled = false; } });
    const mixer = new THREE.AnimationMixer(scene), find = re => { const c = gl.animations.find(a => re.test(a.name)); return c ? mixer.clipAction(c) : null; };
    const acts = { idle: find(/idle/i), walk: find(/walk(?!jump)/i), run: find(/run/i), punch: find(/punch|attack/i), death: find(/death|die/i) };
    if (acts.death) { acts.death.setLoop(THREE.LoopOnce); acts.death.clampWhenFinished = true; }
    let hand = null; scene.traverse(o => { if (!hand && o.isBone && /hand/i.test(o.name) && /(r$|right|\.r|_r)/i.test(o.name)) hand = o; });
    const box = new THREE.Box3().setFromObject(scene), h = box.getSize(new THREE.Vector3()).y || 1;
    R3.models[k] = { scene, mixer, acts, hand, scale: 55 / h }; P._m = null; };
  // secours : si le .glb ne peut pas être servi, on charge sa copie en JavaScript (base64)
  const fallback = () => { const sc3 = document.createElement('script'); sc3.src = url + '.js'; sc3.onload = () => { try { const b64 = (window.NB_MODEL_DATA || {})[k]; if (!b64) return; const bin = atob(b64), buf = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i); new THREE.GLTFLoader().parse(buf.buffer, '', onGl, () => {}); } catch (e) {} }; document.head.appendChild(sc3); };
  try { new THREE.GLTFLoader().load(url, onGl, undefined, fallback); } catch (e) { fallback(); }
}
setQuality((save.quality || 'auto') === 'auto' ? (touch.on ? 'medium' : 'high') : save.quality);
if (PORTAL) PORTAL.loaded();
if (ST) ST.init().then(st => { if (st.owned && !save.premium) { save.premium = true; persist(); } if (['home', 'unlock', 'map'].includes(S.screen)) showScreen(S.screen); });
showScreen('home');
requestAnimationFrame(frame);
window.__nb = { step: dt => tick(dt), failLevel: r => failLevel(r), S, P, save, toggleCar, contextAction, fire: () => fire(), get P2() { return P; }, get lock() { return P.lock; }, get heli() { return heli; }, get peds() { return peds; }, hitEnemy, damageCar, get vip() { return vip; }, get agent() { return agent; }, get world() { return world; }, showScreen, get L() { return L; }, startLevel, nextStep, get enemies() { return enemies; }, get cars() { return cars; }, validCode, codeCheck, buy, D };
})();
