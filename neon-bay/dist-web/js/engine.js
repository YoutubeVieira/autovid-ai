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
const fmt = n => Math.round(n).toLocaleString('fr-FR') + ' $';
const AU = window.NB_AUDIO || null;
const au = (fn, ...a) => { try { if (AU && AU.ready) AU[fn](...a); } catch (e) {} };
const spatial = (x, y) => { const d = Math.hypot(x - P.x, y - P.y); return [Math.max(-1, Math.min(1, (x - P.x) / 600)), Math.max(0, 1 - d / 1000)]; };
const ST = window.NB_STORE || null;
const isPlay = () => !!(ST && ST.isPlay);
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
const fresh = () => ({ money: 500, owned: { pistol: true }, weapon: 'pistol', armor: 0, medkits: 1, nitro: 0, perks: {}, done: {}, maxLevel: 1, premium: false });
let save = (() => { try { const s = JSON.parse(lsGet(SAVE_KEY)); if (s && s.owned) return Object.assign(fresh(), s); } catch (e) {} return fresh(); })();
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
  // minicarte
  const mm = document.createElement('canvas'); mm.width = mm.height = N * 2;
  const m = mm.getContext('2d'), p = region.pal;
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const t = map[y * N + x];
    m.fillStyle = t === ROAD ? '#4a4078' : t === BLD ? '#120e22' : t === PARK || t === TREE ? p.park : t === WATER ? '#1f6f9a' : '#2a2346';
    m.fillRect(x * 2, y * 2, 2, 2);
  }
  return { region, map, bcol, wh, pads, shops, garages, tunnels, hospital, station, mm };
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
const stars = () => Math.floor(S.heat);
const wepDef = id => D.WEAPONS.find(w => w.id === id) || D.WEAPONS[0];
const armorMax = () => save.armor || 0;
const bribeDiscount = () => save.perks.contacts ? .6 : 1;

function mkCar(x, y, a, kind) { return { x, y, a, v: 0, hp: kind === 'police' ? 150 + lvl() * 4 : 100, kind, color: kind === 'police' ? '#eef0ff' : pick(CIV), ai: null, dir: 0, wreck: false, stuck: 0, rev: 0, lock: -1, flash: rnd(1), panic: 0 }; }
function mkPed(x, y) { return { x, y, a: rnd(TAU), state: 'walk', t: rnd(3), skin: pick(PEDC), shirt: pick(SHIRT), cash: Math.random() < .6 ? (10 + rnd(60)) | 0 : 0, ko: 0, step: rnd(6) }; }

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
  c.v -= c.v * .85 * dt; if (thr === 0 && Math.abs(c.v) < 10) c.v = 0;
  if (hb) c.v -= c.v * 2.2 * dt;
  c.v = clamp(c.v, -180, maxV);
  const sp = clamp(Math.abs(c.v) / 200, 0, 1);
  const na = c.a + st * (hb ? 4.2 : 2.8) * sp * dt * (c.v < 0 ? -1 : 1);
  if (!carHits(c.x, c.y, na) || carHits(c.x, c.y, c.a)) c.a = na;
  if (boost) parts.push({ x: c.x - Math.cos(c.a) * 22, y: c.y - Math.sin(c.a) * 22, vx: -Math.cos(c.a) * 120 + rnd(-30, 30), vy: -Math.sin(c.a) * 120 + rnd(-30, 30), life: .25, max: .25, r: 5, col: pick(['#21e6ff', '#ffffff', '#9d7bff']) });
  moveCar(c, dt);
}
function moveCar(c, dt) {
  const nx = c.x + Math.cos(c.a) * c.v * dt, ny = c.y + Math.sin(c.a) * c.v * dt;
  if (!carHits(nx, ny, c.a)) { c.x = nx; c.y = ny; return; }
  const hard = Math.abs(c.v) > 170;
  if (!hard && !carHits(nx, c.y, c.a)) { c.x = nx; c.v *= .95; return; }
  if (!hard && !carHits(c.x, ny, c.a)) { c.y = ny; c.v *= .95; return; }
  if (Math.abs(c.v) > 130) { { const [pn, vl] = spatial(c.x, c.y); if (vl > .1) au('crash', vl * Math.min(1, Math.abs(c.v) / 300), pn); } damageCar(c, Math.abs(c.v) * .05); sparks(c.x + Math.cos(c.a) * 20, c.y + Math.sin(c.a) * 20, 8); if (c === P.car) shake = Math.min(12, Math.abs(c.v) / 40); }
  c.v = -c.v * .3;
}
function damageCar(c, n) { if (c.wreck) return; if (c === P.car && save.perks.carArmor) n *= .5; c.hp -= n; if (c.hp <= 0) explode(c); }
function explosionAt(x, y, r, dmg, byPlayer) {
  shake = Math.max(shake, 14); { const [pn, vl] = spatial(x, y); if (vl > 0) au('boom', pn, vl); }
  for (let i = 0; i < 34; i++) parts.push({ x, y, vx: rnd(-260, 260), vy: rnd(-260, 260), life: rnd(.4, 1), max: 1, r: rnd(4, 12), col: pick(['#ffb627', '#ff6b3d', '#ff2e93', '#fff2a8']) });
  for (let i = 0; i < 10; i++) puff(x + rnd(-20, 20), y + rnd(-20, 20), '#3b3550', 1.6);
  for (const p of peds) if (p.state !== 'ko' && dist(p.x, p.y, x, y) < r) koPed(p, byPlayer);
  for (const e of enemies) if (e.hp > 0 && dist(e.x, e.y, x, y) < r) hitEnemy(e, dmg);
  for (const o of cars) if (!o.wreck && dist(o.x, o.y, x, y) < r) setTimeout(() => damageCar(o, dmg * .7), 100);
  if (vip && !vip.inCar && vip.hp > 0 && dist(vip.x, vip.y, x, y) < r) hurtVip(dmg * .5);
  if (!P.car && dist(P.x, P.y, x, y) < r) hurt(dmg * .5);
}
function explode(c) {
  c.wreck = true; c.v = 0; c.ai = null; c.hp = 0;
  const wasPlayer = c === P.car;
  if (wasPlayer) { P.car = null; P.x = c.x + 30; P.y = c.y; if (solid(P.x, P.y)) P.x = c.x - 30; hurt(30); toast('Voiture détruite !'); }
  if (vip && vip.inCar === c) { vip.inCar = null; vip.x = c.x; vip.y = c.y + 26; hurtVip(30); }
  explosionAt(c.x, c.y, 85, 45, false);
  if (c.kind === 'police') addHeat(1);
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
  const want = Math.atan2(ty - c.y, tx - c.x), diff = angDiff(want, c.a);
  let thr = d < 70 ? (P.car ? .6 : -.3) : 1, st = clamp(diff * 2.6, -1, 1);
  if (c.rev > 0) { c.rev -= dt; thr = -1; st = -st; }
  else if (Math.abs(c.v) < 30 && d > 90) { c.stuck += dt; if (c.stuck > .7) { c.rev = .7; c.stuck = 0; } } else c.stuck = 0;
  if (c.rev <= 0 && Math.abs(diff) > 2.2 && d > 90) thr = .45;
  drive(c, dt, thr, st, false);
}

// ---------- piétons ----------
function koPed(p, byPlayer) {
  if (p.state === 'ko') return;
  p.state = 'ko'; p.ko = 9; { const [pn, vl] = spatial(p.x, p.y); if (vl > .2) au('ko', pn); }
  for (let i = 0; i < 6; i++) parts.push({ x: p.x, y: p.y, vx: rnd(-90, 90), vy: rnd(-90, 90), life: .5, max: .5, r: 3, col: '#fff2a8' });
  if (p.cash) picks.push({ x: p.x + rnd(-8, 8), y: p.y + rnd(-8, 8), amt: p.cash, t: 30 });
  if (byPlayer) addHeat(.6);
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
  const hp = boss ? 380 + n * 55 : 38 + n * 5;
  return { x, y, a: rnd(TAU), hp, max: hp, color: faction.color, boss: boss || null, group, alert: false, cd: rnd(1, 2), strafe: Math.random() < .5 ? 1 : -1, step: 0, st: rnd(2) };
}
function hitEnemy(e, dmg) {
  if (e.hp <= 0) return;
  e.hp -= dmg; e.alert = true; au('hit', spatial(e.x, e.y)[0]);
  for (let i = 0; i < 4; i++) parts.push({ x: e.x, y: e.y, vx: rnd(-80, 80), vy: rnd(-80, 80), life: .3, max: .3, r: 2.5, col: '#ff4d5e' });
  if (e.hp <= 0) {
    for (const o of enemies) if (o.group === e.group && dist(o.x, o.y, e.x, e.y) < 600) o.alert = true;
    if (Math.random() < .5) picks.push({ x: e.x, y: e.y, amt: (20 + lvl() * 8 + rnd(30)) | 0, t: 30 });
    if (e.boss) { toast(e.boss + ' est tombé !'); for (let i = 0; i < 3; i++) picks.push({ x: e.x + rnd(-20, 20), y: e.y + rnd(-20, 20), amt: 200 + lvl() * 40, t: 40 }); }
  }
}
function updEnemy(e, dt) {
  if (e.hp <= 0) return;
  const n = lvl();
  let tx = P.x, ty = P.y;
  if (vip && vip.hp > 0 && !vip.inCar && dist(e.x, e.y, vip.x, vip.y) < dist(e.x, e.y, P.x, P.y) * .8) { tx = vip.x; ty = vip.y; }
  const d = dist(e.x, e.y, tx, ty);
  if (!e.alert && d < 460 && los(e.x, e.y, tx, ty)) e.alert = true;
  if (!e.alert) { e.st -= dt; if (e.st < 0) { e.a = rnd(TAU); e.st = rnd(1, 3); } moveBody(e, Math.cos(e.a) * 25 * dt, Math.sin(e.a) * 25 * dt); return; }
  e.a = Math.atan2(ty - e.y, tx - e.x);
  const sp = (e.boss ? 70 : 95) + n * 1.5;
  let mx = 0, my = 0;
  if (d > 230) { mx = Math.cos(e.a); my = Math.sin(e.a); }
  else if (d < 120) { mx = -Math.cos(e.a); my = -Math.sin(e.a); }
  mx += -Math.sin(e.a) * e.strafe * .6; my += Math.cos(e.a) * e.strafe * .6;
  if (Math.random() < dt * .4) e.strafe *= -1;
  moveBody(e, mx * sp * dt, my * sp * dt); e.step += sp * dt * .25;
  e.cd -= dt;
  if (e.cd <= 0 && d < 520 && shootersNow < 4 && los(e.x, e.y, tx, ty)) {
    shootersNow++;
    const spread = Math.max(.05, .32 - n * .009), a = e.a + rnd(-spread, spread);
    const dmg = (4 + n * .35) * (e.boss ? 1.4 : 1);
    const shots = e.boss && n >= 15 ? 3 : 1;
    { const [pn, vl] = spatial(e.x, e.y); if (vl > .05) au('shot', 'enemy', pn, vl * .8); }
    for (let k = 0; k < shots; k++) { const aa = a + (k - (shots - 1) / 2) * .12; bullets.push({ x: e.x + Math.cos(aa) * 12, y: e.y + Math.sin(aa) * 12, vx: Math.cos(aa) * 560, vy: Math.sin(aa) * 560, life: 1, dmg, from: 'enemy' }); }
    e.cd = Math.max(.8, 2.4 - n * .04) * rnd(.75, 1.35) * (e.boss ? .6 : 1);
  }
}
function moveBody(o, vx, vy) { if (!solid(o.x + vx + Math.sign(vx) * 8, o.y)) o.x += vx; if (!solid(o.x, o.y + vy + Math.sign(vy) * 8)) o.y += vy; }

// ---------- joueur ----------
function hurt(n) {
  if (S.dead > 0 || S.mode !== 'play') return;
  if (P.armor > 0) { const a = Math.min(P.armor, n * .7); P.armor -= a; n -= a; }
  S.hp -= n; shake = Math.max(shake, 5); if (n > 2 && (S.hurtSnd || 0) < S.time) { au('hurt'); S.hurtSnd = S.time + .35; }
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
  au('cash'); save.money -= c; S.heat = 0; S.unseen = 0; policeLeave(); toast('Agents soudoyés (−' + fmt(c) + ')');
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
    if (S.heat >= 1) { S.heat = Math.max(0, stars() - 1); if (S.heat < 1) { S.heat = 0; policeLeave(); } for (const c of cars) if (c.kind === 'police') { c.x += 2000 * Math.sign(c.x - P.x || 1); } }
    if (L) L.tunneled = true;
    toast('Sortie du tunnel');
  }, 700);
}
function toggleCar() {
  if (P.car) {
    const c = P.car, px = -Math.sin(c.a), py = Math.cos(c.a);
    const opts = [[px * -30, py * -30], [px * 30, py * 30], [-Math.cos(c.a) * 36, -Math.sin(c.a) * 36], [Math.cos(c.a) * 36, Math.sin(c.a) * 36]];
    for (const [ox, oy] of opts) { if (!solid(c.x + ox, c.y + oy)) { P.x = c.x + ox; P.y = c.y + oy; break; } }
    c.ai = null; P.car = null; au('door');
    if (vip && vip.inCar === c) { vip.inCar = null; vip.x = c.x - (P.x - c.x); vip.y = c.y - (P.y - c.y); if (solid(vip.x, vip.y)) { vip.x = P.x + 12; vip.y = P.y; } }
    return;
  }
  let best = null, bd = 48;
  for (const c of cars) { if (c.wreck) continue; const d = dist(c.x, c.y, P.x, P.y); if (d < bd) { bd = d; best = c; } }
  if (!best) { msg('Aucune voiture à portée'); return; }
  if (best.ai === 'traffic' || best.ai === 'convoy') { const d = mkPed(best.x - Math.sin(best.a) * 24, best.y + Math.cos(best.a) * 24); d.state = 'flee'; d.t = 6; peds.push(d); if (Math.random() < .3) addHeat(.4); }
  if (best.kind === 'police') { S.heat = Math.max(S.heat, 2); S.unseen = 0; toast('Voiture de police volée !'); }
  best.ai = null; best.v = Math.min(best.v, 40); P.car = best; au('door');
}
function fire() {
  const w = wepDef(save.weapon);
  let a = P.a;
  if (mouse.aim > 0) { a = Math.atan2(mouse.wy - P.y, mouse.wx - P.x); P.a = a; }
  else if (!touch.on || touch.autoAim) { // visée auto vers l'ennemi le plus proche devant
    let best = null, bd = 520;
    for (const e of enemies) { if (e.hp <= 0) continue; const d = dist(P.x, P.y, e.x, e.y); if (d < bd && Math.abs(angDiff(Math.atan2(e.y - P.y, e.x - P.x), P.a)) < (touch.on ? 1.9 : .9) && los(P.x, P.y, e.x, e.y)) { bd = d; best = e; } }
    if (best) a = Math.atan2(best.y - P.y, best.x - P.x);
  }
  for (let k = 0; k < w.pellets; k++) {
    const aa = a + rnd(-w.spread, w.spread);
    bullets.push({ x: P.x + Math.cos(aa) * 12, y: P.y + Math.sin(aa) * 12, vx: Math.cos(aa) * w.speed, vy: Math.sin(aa) * w.speed, life: w.life, dmg: w.dmg, from: 'player', explosive: w.explosive });
  }
  parts.push({ x: P.x + Math.cos(a) * 14, y: P.y + Math.sin(a) * 14, vx: 0, vy: 0, life: .06, max: .06, r: w.explosive ? 10 : 7, col: '#fff2a8' });
  P.cd = w.rate; panic(P.x, P.y, 380); au('shot', w.id, 0, 1);
}
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
      const guards = Math.floor(n / 4); if (guards) spawnGroup(c.x, c.y, guards, f, g);
      st.desc = () => 'Récupère les valises près de ' + st.pl + ' (' + st.items.filter(i => i.got).length + '/' + count + ')'; st.pl = place();
      st.dyn = () => { const r = st.items.filter(i => !i.got); return r.length ? nearestOf(r) : null; };
      st.check = () => st.items.every(i => i.got); break;
    }
    case 'elim': case 'boss': {
      const c = randWalk(1000, 1900, P.x, P.y);
      const count = type === 'boss' ? Math.min(10, 2 + Math.floor(n / 3)) : Math.min(14, 3 + Math.floor(n / 2.5));
      const boss = spawnGroup(c.x, c.y, count, f, g, type === 'boss' ? (L.def.boss || 'le chef') : null);
      st.center = c; st.boss = boss;
      st.desc = () => type === 'boss' ? 'Élimine ' + boss.boss + ', chef de ' + f.name : 'Neutralise ' + f.name + ' (' + enemies.filter(e => e.group === g && e.hp > 0).length + ' restants)';
      st.dyn = () => { const al = enemies.filter(e => e.group === g && e.hp > 0); if (!al.length) return null; if (dist(P.x, P.y, c.x, c.y) > 500 && !al.some(e => e.alert)) return c; return type === 'boss' && boss.hp > 0 && dist(P.x, P.y, boss.x, boss.y) < 600 ? boss : nearestOf(al); };
      st.check = () => type === 'boss' ? boss.hp <= 0 : !enemies.some(e => e.group === g && e.hp > 0); break;
    }
    case 'escape': {
      S.heat = Math.max(S.heat, Math.min(5, 2 + Math.floor(n / 8))); S.unseen = 0; st.time = 150; st.grace = 2;
      st.desc = 'La police te traque : sème-la (tunnel, atelier de peinture ou pot-de-vin)';
      st.check = dt => { st.grace -= dt; return st.grace <= 0 && stars() === 0; }; break;
    }
    case 'survive': {
      S.heat = Math.max(S.heat, Math.min(5, 3 + Math.floor(n / 10))); S.unseen = 0; st.time = 30 + Math.round(n * 1.2); st.survive = true; st.lock = true;
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
          const mx = (vip.x + st.dest.x) / 2, my = (vip.y + st.dest.y) / 2; spawnGroup(mx, my, 2 + Math.floor(n / 5), f, g);
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
function canPlay(n) { return n <= save.maxLevel && (n === 1 || save.premium); }
function startLevel(n) {
  const region = regionOf(n); au('init'); au('setMusic', region.id); au('setIntensity', 0);
  if (!world || world.region !== region) world = buildWorld(region);
  cars = []; peds = []; bullets = []; parts = []; picks = []; enemies = []; cases = []; vip = null; agent = null;
  S.heat = 0; S.unseen = 0; S.bust = 0; S.hp = 100; S.dead = 0; S.tunnelCd = 0; S.spawnPol = 0;
  P.car = null; P.x = world.hospital.x; P.y = world.hospital.y + 20; P.a = PI / 2; P.armor = armorMax(); P.nitro = 0; P.cd = 0;
  if (!save.owned[save.weapon]) save.weapon = 'pistol';
  cam.x = P.x; cam.y = P.y;
  for (let i = 0; i < 90; i++) { const t = randWalk(0, W * 2, 0, 0); parkedCar(t.x, t.y); }
  for (let k = 0; k < 3; k++) { const p = freeNear(P.x + 60, P.y + 40, 80); parkedCar(p.x, p.y); }
  for (let i = 0; i < 25; i++) spawnPed();
  for (let i = 0; i < 14; i++) spawnTraffic();
  L = { n, def: D.LEVELS[n - 1], region, idx: -1, earned: 0, time: 0, step: null };
  S.mode = 'play'; showScreen(null);
  toast('Niveau ' + n + ' : ' + L.def.t);
  nextStep();
}
function nextStep() {
  if (L.step) { if (L.idx < 9) au('step'); const r = stepReward(L.n); save.money += r; L.earned += r; if (L.idx >= 0) toast('Étape ' + (L.idx + 1) + '/10 réussie · +' + fmt(r)); }
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
  if (st.time !== null) {
    st.time -= dt;
    if (st.time <= 0) { if (st.survive) { nextStep(); return; } failLevel('Temps écoulé'); return; }
  }
  if (st.fail) { const r = st.fail(); if (r) { failLevel(r); return; } }
  if (st.needCar && !P.car && st.target && dist(P.x, P.y, st.target.x, st.target.y) < 70) msg('Il faut arriver en voiture');
  if (st.check(dt)) nextStep();
}
function completeLevel() {
  const n = L.n, bonus = levelBonus(n);
  save.money += bonus; L.earned += bonus; au('win'); au('setMusic', 'menu');
  const first = !save.done[n];
  save.done[n] = true; save.maxLevel = Math.max(save.maxLevel, Math.min(30, n + 1)); persist();
  S.mode = 'result';
  const unlockW = D.WEAPONS.filter(w => w.lvl === n + 1).concat(D.GEAR.filter(g => g.lvl === n + 1));
  showScreen('result', { ok: true, n, earned: L.earned, bonus, time: L.time, first, unlocks: unlockW });
}
function failLevel(reason) {
  if (S.mode !== 'play') return;
  S.mode = 'result'; persist(); au('fail'); au('setMusic', null);
  showBanner(reason.includes('K.O') ? 'K.O.' : reason.includes('Arrêté') ? 'ARRÊTÉ' : 'ÉCHEC');
  setTimeout(() => showScreen('result', { ok: false, n: L.n, reason, earned: L.earned }), 1100);
}

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
    else if (/^Digit[1-7]$/.test(e.code)) { const w = D.WEAPONS[+e.code.slice(5) - 1]; if (w && save.owned[w.id]) { save.weapon = w.id; msg(w.name); } }
    else if (e.code === 'Escape' || e.code === 'KeyP') pauseGame();
  } else if (S.mode === 'pause' && (e.code === 'Escape' || e.code === 'KeyP')) resumeGame();
});
addEventListener('keyup', e => { keys[e.code] = false; });
addEventListener('blur', () => { for (const k in keys) keys[k] = false; if (S.mode === 'play') pauseGame(); });
const cvs = document.getElementById('game'); let ctx = cvs.getContext('2d');
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
['pointerdown', 'keydown'].forEach(ev => addEventListener(ev, () => { if (AU) { AU.init(); if (S.mode === 'menu' && !L) au('setMusic', 'menu'); } }, { passive: true }));
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
const tb = (id, fn) => $(id).addEventListener('pointerdown', e => { e.preventDefault(); fn(); });
$('bShoot').addEventListener('pointerdown', e => { e.preventDefault(); touch.shoot = true; });
['pointerup', 'pointercancel', 'pointerleave'].forEach(t => $('bShoot').addEventListener(t, () => { touch.shoot = false; }));
tb('bAct', contextAction); tb('bWep', () => cycleWeapon(1)); tb('bMed', useMedkit); tb('bBribe', bribePolice); tb('bNitro', useNitro); tb('bPause', pauseGame);

// ---------- HUD ----------
const hud = { money: $('money'), stars: $('stars'), hp: $('hp'), armor: $('armor'), wep: $('wep'), inv: $('inv'), step: $('step'), sN: $('sN'), sD: $('sD'), sC: $('sC'), dots: $('dots'), lvlName: $('lvlName'), toast: $('toast'), banner: $('banner'), prompt: $('prompt'), vipBar: $('vipBar'), vipHp: $('vipHp'), fade: $('fade') };
const starEls = [...hud.stars.children];
const last = {};
let toastT = 0, msgT = 0;
function toast(t) { hud.toast.textContent = t; hud.toast.style.opacity = 1; toastT = 2.4; }
function msg(t) { if (S.msgCd > 0 && last.msg === t) return; last.msg = t; S.msgCd = 1.5; hud.prompt.textContent = t; hud.prompt.hidden = false; msgT = 1.6; }
function showBanner(t) { hud.banner.textContent = t; hud.banner.style.opacity = 1; setTimeout(() => { hud.banner.style.opacity = 0; }, 1500); }
function fade(t) { hud.fade.textContent = t; hud.fade.style.opacity = 1; setTimeout(() => { hud.fade.style.opacity = 0; }, 1300); }
function setText(el, k, v) { if (last[k] !== v) { last[k] = v; el.textContent = v; } }
function setW(el, k, v) { if (last[k] !== v) { last[k] = v; el.style.width = v + '%'; } }
function updHud(dt) {
  setText(hud.money, 'm', fmt(save.money));
  const s = stars(); if (last.s !== s) { last.s = s; starEls.forEach((e, i) => e.classList.toggle('on', i < s)); }
  const seen = s > 0 && S.unseen < .5; if (last.seen !== seen) { last.seen = seen; hud.stars.classList.toggle('blink', seen); }
  setW(hud.hp, 'hp', Math.max(0, Math.round(S.hp)));
  setW(hud.armor, 'ar', armorMax() ? Math.round(P.armor / 150 * 100) : 0);
  setText(hud.wep, 'w', wepDef(save.weapon).name);
  setText(hud.inv, 'inv', 'Soins ' + save.medkits + ' · Nitro ' + save.nitro);
  if (L && L.step) {
    const st = L.step;
    setText(hud.lvlName, 'ln', 'Niveau ' + L.n + ' · ' + L.def.t);
    setText(hud.sN, 'sn', 'Étape ' + (L.idx + 1) + '/10 · ' + st.label);
    setText(hud.sD, 'sd', st.needCar && !P.car ? stepDesc(st) + ' (monte dans une voiture : E)' : stepDesc(st));
    const t = st.time !== null ? Math.max(0, Math.ceil(st.time)) : null;
    setText(hud.sC, 'sc', t === null ? '' : `${(t / 60) | 0}:${String(t % 60).padStart(2, '0')}`);
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
  const showN = !!P.car; if (last.bn !== showN) { last.bn = showN; bn.hidden = !showN; $('bShoot').textContent = showN ? 'FREIN' : 'TIRER'; }
  if (toastT > 0) { toastT -= dt; if (toastT <= 0) hud.toast.style.opacity = 0; }
}

// ---------- boucle de jeu ----------
const PCOUNT = [0, 1, 2, 3, 5, 7];
function update(dt) {
  S.time += dt; S.msgCd -= dt; mouse.aim -= dt; S.tunnelCd -= dt;
  if (P.nitro > 0) P.nitro -= dt;
  if (peds.length < (touch.on ? 24 : 36) && Math.random() < .5) spawnPed();
  if (cars.filter(c => c.ai === 'traffic').length < 18 && Math.random() < .3) spawnTraffic();
  const want = Math.round(PCOUNT[stars()] * (save.perks.radio ? .6 : 1) + (stars() >= 3 ? Math.floor(lvl() / 12) : 0));
  const cops = cars.filter(c => c.kind === 'police' && c.ai === 'police');
  S.spawnPol -= dt; if (cops.length < want && S.spawnPol <= 0) { spawnPolice(); S.spawnPol = save.perks.radio ? 2 : 1.2; }
  const Lk = keys.KeyA || keys.ArrowLeft, Rk = keys.KeyD || keys.ArrowRight, U = keys.KeyW || keys.ArrowUp, Dn = keys.KeyS || keys.ArrowDown;
  const act = keys.Space || mouse.down || touch.shoot;
  if (S.dead <= 0) {
    if (P.car) {
      const c = P.car; let thr = (U ? 1 : 0) - (Dn ? 1 : 0), st = (Rk ? 1 : 0) - (Lk ? 1 : 0);
      if (touch.mag > .2) { const ja = Math.atan2(touch.jy, touch.jx), d = angDiff(ja, c.a); if (Math.abs(d) > 2.5) { thr = -touch.mag; st = 0; } else { thr = touch.mag; st = clamp(d * 2.2, -1, 1); } }
      if ((keys.ShiftLeft || keys.ShiftRight) && P.nitro <= 0 && save.nitro > 0 && thr > 0 && !last.shiftN) { useNitro(); }
      last.shiftN = keys.ShiftLeft || keys.ShiftRight;
      drive(c, dt, thr, st, act);
      P.x = c.x; P.y = c.y; P.a = c.a;
    } else {
      let mx = (Rk ? 1 : 0) - (Lk ? 1 : 0), my = (Dn ? 1 : 0) - (U ? 1 : 0);
      if (touch.mag > .15) { mx = touch.jx; my = touch.jy; }
      const m = Math.hypot(mx, my);
      if (m > .1) { const sp = (keys.ShiftLeft || keys.ShiftRight || touch.mag > .9 ? 230 : 150) * Math.min(1, m); P.a = Math.atan2(my, mx); moveBody(P, Math.cos(P.a) * sp * dt, Math.sin(P.a) * sp * dt); P.step += sp * dt * .25; }
      P.cd -= dt; if (act && P.cd <= 0) fire();
    }
  }
  for (const c of cars) {
    if (c === P.car || c.wreck) { if (c.wreck && Math.random() < dt * 3) puff(c.x, c.y, '#2d283f', 1.4); continue; }
    if (c.ai === 'traffic' || c.ai === 'convoy') updTraffic(c, dt); else if (c.kind === 'police' && c.ai) updPolice(c, dt); else drive(c, dt, 0, 0, false);
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
        if (a === P.car || b === P.car) { shake = Math.min(10, rel / 40); const o = a === P.car ? b : a; if (o.kind === 'police' && o.ai) addHeat(.15); if (o.ai === 'traffic' || o.ai === 'convoy') o.panic = 3; }
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
  P.hurt -= dt;
  for (const p of peds) updPed(p, dt);
  shootersNow = Math.max(0, shootersNow - dt * 6);
  for (const e of enemies) updEnemy(e, dt);
  updVip(dt);
  // balles
  for (const b of bullets) {
    b.life -= dt; const nx = b.x + b.vx * dt, ny = b.y + b.vy * dt;
    if (blocksShot(nx, ny)) { b.life = 0; sparks(b.x, b.y, 3); if (b.explosive) explosionAt(b.x, b.y, 95, b.dmg, true); continue; }
    b.x = nx; b.y = ny;
    if (b.from === 'player') {
      let hit = false;
      for (const e of enemies) if (e.hp > 0 && dist(b.x, b.y, e.x, e.y) < (e.boss ? 16 : 12)) { hitEnemy(e, b.dmg); hit = true; break; }
      if (!hit) for (const p of peds) if (p.state !== 'ko' && dist(b.x, b.y, p.x, p.y) < 11) { koPed(p, true); hit = true; break; }
      if (!hit) for (const c of cars) if (c !== P.car && !c.wreck && dist(b.x, b.y, c.x, c.y) < 20) { damageCar(c, b.dmg * .7); sparks(b.x, b.y, 4); hit = true; if (c.kind === 'police') addHeat(.35); else if (c.ai) c.panic = 4; break; }
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
  for (const k of picks) { k.t -= dt; if (dist(P.x, P.y, k.x, k.y) < 30) { save.money += k.amt; if (L) L.earned += k.amt; au('cash'); msg('+' + fmt(k.amt)); k.t = 0; } }
  picks = picks.filter(k => k.t > 0);
  for (const c of cases) if (!c.got && dist(P.x, P.y, c.x, c.y) < 32) { c.got = true; au('pickup'); msg('Valise récupérée'); sparks(c.x, c.y, 10); }
  // atelier de peinture
  if (P.car && tileAt(P.car.x, P.car.y) === PAD && stars() > 0 && !(L && L.step && L.step.lock)) {
    const cost = 200 + lvl() * 60;
    if (save.money >= cost) { save.money -= cost; S.heat = 0; P.car.color = pick(CIV); P.car.hp = Math.max(P.car.hp, 100); toast('Voiture repeinte · police semée (−' + fmt(cost) + ')'); policeLeave(); }
    else msg('Il faut ' + fmt(cost) + ' pour repeindre');
  }
  // police
  const s = stars();
  if (s > 0) {
    if (cars.some(c => c.kind === 'police' && c.ai === 'police' && dist(c.x, c.y, P.x, P.y) < 430)) S.unseen = 0; else S.unseen += dt;
    const lose = (save.perks.radio ? 5 : 7) + lvl() * .04;
    if (S.unseen > lose && !(L && L.step && L.step.lock)) { S.heat = Math.max(0, s - 1); S.unseen = 0; if (S.heat < 1) { S.heat = 0; msg('Police semée'); policeLeave(); } }
    let near = false; for (const c of cars) if (c.kind === 'police' && c.ai === 'police' && !c.wreck && dist(c.x, c.y, P.x, P.y) < (P.car ? 62 : 56) && Math.abs(c.v) < 90) { near = true; break; }
    if (near && (!P.car || Math.abs(P.car.v) < 30)) S.bust += dt * (P.car ? .6 : 1); else S.bust = Math.max(0, S.bust - dt);
    if (S.bust > 1.6) failLevel('Arrêté par la police');
  } else { S.bust = 0; if (S.hp < 100) S.hp = Math.min(100, S.hp + dt * 1.5); }
  // nettoyage
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
  ctx.fillStyle = t === PLAZA ? p.plaza : p.walk; ctx.fillRect(x, y, T, T);
  ctx.strokeStyle = p.line; ctx.lineWidth = 1; ctx.strokeRect(x + .5, y + .5, T - 1, T - 1);
  if (t === PLAZA) { ctx.strokeRect(x + 16.5, y + 16.5, 31, 31); }
  ctx.fillStyle = p.curb;
  if (tileAt(x - 1, y + 1) === ROAD) ctx.fillRect(x, y, 3, T); if (tileAt(x + T + 1, y + 1) === ROAD) ctx.fillRect(x + T - 3, y, 3, T);
  if (tileAt(x + 1, y - 1) === ROAD) ctx.fillRect(x, y, T, 3); if (tileAt(x + 1, y + T + 1) === ROAD) ctx.fillRect(x, y + T - 3, T, 3);
  const pad = (col, a, b) => { ctx.fillStyle = col + '33'; ctx.fillRect(x + 4, y + 4, T - 8, T - 8); ctx.strokeStyle = col; ctx.lineWidth = 3; ctx.strokeRect(x + 5, y + 5, T - 10, T - 10); ctx.fillStyle = col; ctx.font = '700 10px "Chakra Petch",sans-serif'; ctx.textAlign = 'center'; ctx.fillText(a, x + T / 2, y + T / 2 + 2); if (b) ctx.fillText(b, x + T / 2, y + T / 2 + 14); };
  if (t === PAD) pad('#ff2e93', 'PEINTURE', fmt(200 + lvl() * 60));
  else if (t === SHOP) { pad('#a6ff4d', 'BOUTIQUE', 'armes'); }
  else if (t === GARAGE) { pad('#3ee0c5', 'GARAGE', ''); }
  else if (t === TUNNEL) {
    ctx.fillStyle = '#05040a'; ctx.beginPath(); ctx.arc(x + T / 2, y + T / 2, 22, 0, TAU); ctx.fill();
    ctx.strokeStyle = '#ffb627'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(x + T / 2, y + T / 2, 22, 0, TAU); ctx.stroke();
    ctx.fillStyle = '#ffb627'; ctx.font = '700 10px "Chakra Petch",sans-serif'; ctx.textAlign = 'center'; ctx.fillText('TUNNEL', x + T / 2, y + T / 2 + 4);
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
function drawMini(target) {
  const s = mini.width / W; mctx.drawImage(world.mm, 0, 0, mini.width, mini.height);
  const dot = (x, y, c, r) => { mctx.fillStyle = c; mctx.beginPath(); mctx.arc(x * s, y * s, r, 0, TAU); mctx.fill(); };
  for (const p of world.pads) dot(p.x, p.y, '#ff2e93', 2.5);
  for (const p of world.shops) dot(p.x, p.y, '#a6ff4d', 3);
  for (const p of world.tunnels) dot(p.x, p.y, '#ffb627', 2.5);
  for (const c of cars) if (c.kind === 'police' && c.ai === 'police') dot(c.x, c.y, Math.sin(S.time * 10) > 0 ? '#ff2e4d' : '#2e6bff', 2.5);
  for (const e of enemies) if (e.hp > 0 && e.alert) dot(e.x, e.y, '#ff4d5e', 2);
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
    r.setPixelRatio(Math.min(touch.on ? 1.5 : 1.75, devicePixelRatio || 1));
    R3.r = r;
  } catch (e) { return; }
  const sc = R3.scene = new THREE.Scene();
  R3.cam = new THREE.PerspectiveCamera(46, 1, 10, 5000);
  sc.add(new THREE.HemisphereLight(0xa7b0ff, 0x241838, .95));
  const moon = new THREE.DirectionalLight(0xfff0dd, .6); moon.position.set(-400, 900, 300); sc.add(moon);
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
  const S = touch.on ? 20 : 24, gc = document.createElement('canvas'); gc.width = gc.height = N * S;
  const gx = gc.getContext('2d'), saved = ctx; ctx = gx; gx.setTransform(S / T, 0, 0, S / T, 0, 0);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) drawTile(x, y);
  ctx = saved;
  const tex = new THREE.CanvasTexture(gc); tex.anisotropy = Math.min(8, R3.r.capabilities.getMaxAnisotropy());
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(W, W), new THREE.MeshLambertMaterial({ map: tex }));
  ground.rotation.x = -PI / 2; ground.position.set(W / 2, 0, W / 2); g.add(ground);
  // immeubles
  const tiles = []; for (let ty = 0; ty < N; ty++) for (let tx = 0; tx < N; tx++) if (world.map[ty * N + tx] === BLD) tiles.push([tx, ty]);
  const wt = R3.wt || (R3.wt = windowTex());
  const side = new THREE.MeshLambertMaterial({ map: wt.m, emissiveMap: wt.em, emissive: 0xffffff, emissiveIntensity: .85 });
  const roof = new THREE.MeshLambertMaterial({ color: 0xffffff });
  const im = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), [side, side, roof, roof, side, side], tiles.length);
  const c = new THREE.Color();
  tiles.forEach(([tx, ty], i) => {
    const h = bHeight(tx, ty), k = ty * N + tx;
    R3.v.set(tx * T + T / 2, h / 2, ty * T + T / 2); R3.s.set(T, h, T); R3.q.identity();
    R3.m4.compose(R3.v, R3.q, R3.s); im.setMatrixAt(i, R3.m4);
    c.set(world.wh[k] ? '#55545f' : p.bld[(world.bcol[k] + (hash(tx, ty) & 1)) % p.bld.length]);
    c.offsetHSL(0, 0, .12); im.setColorAt(i, c);
  });
  R3.s.set(1, 1, 1);
  g.add(im);
  // néons sur les toits (bordures lumineuses autour des blocs)
  const neonTiles = tiles.filter(([tx, ty]) => [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => world.map[(ty + dy) * N + tx + dx] !== BLD));
  const nm = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshBasicMaterial({ color: 0xffffff }), neonTiles.length);
  neonTiles.forEach(([tx, ty], i) => {
    const h = bHeight(tx, ty), k = ty * N + tx;
    R3.v.set(tx * T + T / 2, h - 2.2, ty * T + T / 2); R3.s.set(T + 4, 3.4, T + 4); R3.m4.compose(R3.v, R3.q, R3.s); nm.setMatrixAt(i, R3.m4);
    nm.setColorAt(i, c.set(world.wh[k] ? '#8b8a96' : p.neon[world.bcol[k] % p.neon.length]));
  });
  R3.s.set(1, 1, 1); g.add(nm);
  // arbres
  const trees = []; for (let ty = 0; ty < N; ty++) for (let tx = 0; tx < N; tx++) { const t = world.map[ty * N + tx]; if (t === TREE || (t === PARK && hash(tx, ty) % 4 === 0)) trees.push([tx, ty, t === TREE]); }
  const crown = new THREE.InstancedMesh(new THREE.ConeGeometry(1, 1, 7), mat(p.tree), trees.length);
  const trunk = new THREE.InstancedMesh(bx(1, 1, 1), mat('#3b2a1e'), trees.length);
  trees.forEach(([tx, ty, big], i) => {
    const s = big ? 1 : .7, x = tx * T + 32, z = ty * T + 32;
    R3.v.set(x, 14 * s, z); R3.s.set(6 * s, 28 * s, 6 * s); R3.m4.compose(R3.v, R3.q, R3.s); trunk.setMatrixAt(i, R3.m4);
    R3.v.set(x, 44 * s, z); R3.s.set(24 * s, 50 * s, 24 * s); R3.m4.compose(R3.v, R3.q, R3.s); crown.setMatrixAt(i, R3.m4);
  });
  R3.s.set(1, 1, 1); g.add(trunk, crown);
  // colonnes de lumière : boutique, tunnels, peinture, garages, hôpital, police
  const beam = (pt, colr, h = 150) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(22, 22, h, 18, 1, true), bmat(colr, .2, true)); m.position.set(pt.x, h / 2, pt.y); g.add(m); };
  world.shops.forEach(s => beam(s, '#a6ff4d')); world.tunnels.forEach(s => beam(s, '#ffb627', 110)); world.pads.forEach(s => beam(s, '#ff2e93', 110));
  world.garages.forEach(s => beam(s, '#3ee0c5', 110)); beam(world.hospital, '#a6ff4d', 90); beam(world.station, '#2e6bff', 90);
  sc.add(g);
}
// ---- personnages en blocs
function makeChar(o) {
  const g = new THREE.Group();
  const add = (geo, m, x, y, z, parent = g) => { const me = new THREE.Mesh(geo, m); me.position.set(x, y, z); parent.add(me); return me; };
  const limb = (x, y, z) => { const p = new THREE.Group(); p.position.set(x, y, z); g.add(p); return p; };
  const hipL = limb(0, 13, -3.2), hipR = limb(0, 13, 3.2);
  add(bx(5, 13, 5), mat(o.pants || '#1d1a2e'), 0, -6.5, 0, hipL); add(bx(5, 13, 5), mat(o.pants || '#1d1a2e'), 0, -6.5, 0, hipR);
  add(bx(6, 2, 5.4), mat(o.shoes || '#0c0b12'), .8, -12.5, 0, hipL); add(bx(6, 2, 5.4), mat(o.shoes || '#0c0b12'), .8, -12.5, 0, hipR);
  add(bx(7, 13, 12), mat(o.shirt), 0, 19.5, 0);
  const armL = limb(0, 25, -8), armR = limb(0, 25, 8);
  add(bx(4, 12, 4), mat(o.sleeve || o.shirt), 0, -5.5, 0, armL); add(bx(4, 12, 4), mat(o.sleeve || o.shirt), 0, -5.5, 0, armR);
  add(bx(4, 3, 4), mat(o.skin), 0, -12.5, 0, armL); add(bx(4, 3, 4), mat(o.skin), 0, -12.5, 0, armR);
  add(bx(9, 9, 9), mat(o.skin), 0, 30.5, 0);
  add(bx(.8, 2, 1.6), mat('#0b0a12'), 4.6, 31.5, -2); add(bx(.8, 2, 1.6), mat('#0b0a12'), 4.6, 31.5, 2);
  add(bx(.6, 1, 4), mat('#5a2f2f'), 4.6, 28, 0);
  if (o.hair) add(bx(9.6, 3, 9.6), mat(o.hair), -.4, 35.6, 0);
  if (o.hat) { add(bx(10, 3.4, 10), mat(o.hat), 0, 36.2, 0); add(bx(5, 1.2, 9), mat(o.hat), 6.5, 35, 0); }
  if (o.chain) add(bx(7.4, 2, 8), mat('#ffd700', '#7a5a00'), .4, 24, 0);
  if (o.bandana) add(bx(9.4, 2.4, 9.4), mat(o.bandana, o.bandana), 0, 33.5, 0);
  if (o.gun) add(bx(12, 3, 3), mat('#101014'), 5, -12, 0, armR);
  if (o.glow) { const r = new THREE.Mesh(new THREE.RingGeometry(10, 12.5, 20), bmat(o.glow, .75, true)); r.rotation.x = -PI / 2; r.position.y = .6; g.add(r); }
  const sh = new THREE.Mesh(new THREE.CircleGeometry(9, 14), bmat('#000000', .35)); sh.rotation.x = -PI / 2; sh.position.y = .3; g.add(sh);
  g.scale.setScalar((o.scale || 1) * 1.5);
  g.userData = { hipL, hipR, armL, armR, gun: !!o.gun, ls: -1 };
  return g;
}
function poseChar(m, x, y, a, step, ko, aim) {
  const u = m.userData;
  m.position.set(x, ko ? 4 : 0, y); m.rotation.set(0, -a, ko ? -PI / 2 : 0);
  const moving = step !== u.ls; u.ls = step;
  u.sw = (u.sw || 0) * .8 + (moving ? Math.sin(step * 1.1) * .8 : 0) * .2 + (moving ? 0 : 0);
  const sw = moving ? Math.sin(step * 1.1) * .75 : 0;
  u.hipL.rotation.z = sw; u.hipR.rotation.z = -sw;
  if (u.gun && aim) { u.armR.rotation.z = PI / 2; u.armL.rotation.z = PI / 2.4; u.armL.rotation.x = .5; }
  else { u.armL.rotation.z = -sw * .9; u.armR.rotation.z = sw * .9; u.armL.rotation.x = 0; }
}
// ---- voitures
function makeCar3(c) {
  const g = new THREE.Group();
  const add = (geo, m, x, y, z) => { const me = new THREE.Mesh(geo, m); me.position.set(x, y, z); g.add(me); return me; };
  const sh = add(bx(46, .5, 24), bmat('#000000', .35), 1, .3, 0);
  const body = add(bx(42, 9, 20), mat(c.color), 0, 9, 0);
  const hood = add(bx(10, 2, 19), mat(c.color), 15, 14, 0);
  add(bx(21, 9, 17.5), mat('#121022'), -3, 18, 0);
  const roof = add(bx(17, 1.6, 16), mat(c.color), -4, 23.2, 0);
  add(bx(9, 9, 22), mat('#08080c'), 13, 5, 0); add(bx(9, 9, 22), mat('#08080c'), -13, 5, 0);
  add(bx(1, 3, 15), mat('#fff6cc', '#fff2b0'), 21.2, 10, 0); add(bx(1, 3, 15), mat('#ff2e4d', '#ff2e4d'), -21.2, 10, 0);
  const u = { body, hood, roof, color: c.color, wreck: false };
  if (c.kind === 'police') {
    add(bx(12, 9.2, 20.4), mat('#1b1f4a'), -2, 9, 0);
    u.r = add(bx(4, 3, 7), mat('#ff2e4d'), -4, 25.5, -4); u.b = add(bx(4, 3, 7), mat('#2e6bff'), -4, 25.5, 4);
    u.glow = add(new THREE.CircleGeometry(48, 20), bmat('#ff2e4d', .18, true), 0, .8, 0); u.glow.rotation.x = -PI / 2;
  }
  const cone = new THREE.Mesh(new THREE.CircleGeometry(150, 14, -.33, .66), bmat('#fff0c0', .1, true));
  cone.rotation.x = -PI / 2; cone.position.set(18, .7, 0); g.add(cone); u.cone = cone;
  if (c.mark) { u.mk = new THREE.Mesh(new THREE.ConeGeometry(7, 14, 4), new THREE.MeshBasicMaterial({ color: c.convoy ? 0xff4d5e : 0xffd700, depthTest: false })); u.mk.rotation.z = PI; u.mk.renderOrder = 9; g.add(u.mk); }
  g.scale.setScalar(1.15);
  g.userData = u;
  return g;
}
function poseCar(m, c) {
  const u = m.userData;
  m.position.set(c.x, 0, c.y); m.rotation.y = -c.a;
  if (c.wreck && !u.wreck) { u.wreck = true; for (const k of ['body', 'hood', 'roof']) u[k].material = mat('#26222e'); u.cone.visible = false; if (u.glow) u.glow.visible = false; if (u.mk) u.mk.visible = false; }
  if (!c.wreck && u.color !== c.color) { u.color = c.color; for (const k of ['body', 'hood', 'roof']) u[k].material = mat(c.color); }
  if (u.r && !c.wreck) { const f = Math.sin((S.time + c.flash) * 14) > 0; u.r.material = f ? mat('#ff2e4d', '#ff2e4d') : mat('#401018'); u.b.material = f ? mat('#10183a') : mat('#2e6bff', '#2e6bff'); u.glow.material = bmat(f ? '#ff2e4d' : '#2e6bff', .2, true); }
  if (u.mk) { u.mk.visible = c.mark && !c.wreck; u.mk.position.set(0, 40 + Math.sin(S.time * 5) * 4, 0); }
}
// ---- objets simples
function makeProp(kind) {
  const g = new THREE.Group();
  if (kind === 'cash') { const m = new THREE.Mesh(bx(14, 4, 9), mat('#a6ff4d', '#3a7a10')); m.position.y = 6; g.add(m); }
  else if (kind === 'case') { const m = new THREE.Mesh(bx(16, 11, 6), mat('#c98a2b', '#4a2a00')); m.position.y = 8; g.add(m); const h = new THREE.Mesh(bx(6, 3, 2), mat('#3a2410')); h.position.y = 15; g.add(h);
    const b = new THREE.Mesh(new THREE.CylinderGeometry(10, 10, 80, 12, 1, true), bmat('#ffb627', .18, true)); b.position.y = 40; g.add(b); }
  return g;
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
  if (!m) m = e._m = make(e);
  if (m.parent !== R3.dyn) R3.dyn.add(m);
  R3.seen.add(m); pose(m, e);
}
function resize3D() { if (R3.w === VW && R3.h === VH) return; R3.w = VW; R3.h = VH; R3.r.setSize(VW, VH, false); R3.cam.aspect = VW / VH; R3.cam.updateProjectionMatrix(); }
function render3D(dt) {
  if (R3.world !== world) build3DWorld();
  resize3D();
  const playing = S.mode !== 'menu' && L;
  let tx, ty;
  if (!playing) { R3.orbit = (R3.orbit || 0) + dt * .04; tx = W / 2 + Math.cos(R3.orbit) * 1100; ty = W / 2 + Math.sin(R3.orbit) * 1100; }
  else { tx = P.car ? P.car.x + Math.cos(P.car.a) * P.car.v * .3 : P.x; ty = P.car ? P.car.y + Math.sin(P.car.a) * P.car.v * .3 : P.y; }
  const k = Math.min(1, dt * 4); cam.x += (tx - cam.x) * k; cam.y += (ty - cam.y) * k;
  const sp = P.car && playing ? Math.abs(P.car.v) : 0;
  let d = 350 + sp * .3; if (VW < VH) d *= 1.35; if (!playing) d = 760;
  cam.z += (d - cam.z) * Math.min(1, dt * 2); if (cam.z < 100) cam.z = d;
  const sx = shake ? rnd(-shake, shake) : 0, sy = shake ? rnd(-shake, shake) : 0; shake = Math.max(0, shake - dt * 30);
  R3.cam.position.set(cam.x + sx, cam.z, cam.y + cam.z * (playing ? .3 : .5) + sy); R3.cam.lookAt(cam.x, 0, cam.y);
  const near = (x, y) => Math.abs(x - cam.x) < 1250 && Math.abs(y - cam.y) < 1250;
  R3.seen.clear();
  for (const c of cars) if (near(c.x, c.y)) sync(c, makeCar3, poseCar);
  for (const p of peds) if (near(p.x, p.y)) sync(p, e => makeChar({ shirt: e.shirt, skin: e.skin, hair: pick(['#1a120c', '#3b2414', '#0c0c0c', '#6b4a2a', '#d8b46a']), pants: pick(['#1d1a2e', '#2a3a5a', '#3a2a22', '#26262e']) }), (m, e) => poseChar(m, e.x, e.y, e.a, e.step, e.state === 'ko'));
  for (const e of enemies) if (near(e.x, e.y)) sync(e, e2 => { const m = makeChar({ shirt: '#17131f', sleeve: '#17131f', skin: pick(['#c68b59', '#8d5a3b', '#e0a070']), bandana: e2.boss ? null : e2.color, hat: e2.boss ? e2.color : null, chain: !!e2.boss, gun: true, glow: e2.color, scale: e2.boss ? 1.45 : 1 }); m.userData.bar = hpBar(m, 30, 16); return m; },
    (m, e2) => { poseChar(m, e2.x, e2.y, e2.a, e2.step, e2.hp <= 0, e2.alert); setBar(m.userData.bar, e2.hp / e2.max, e2.color, e2.hp > 0 && (e2.alert || e2.boss), e2.a); });
  if (agent && !agent.paid && near(agent.x, agent.y)) sync(agent, () => makeChar({ shirt: '#2e6bff', pants: '#14183a', skin: '#f2d3b3', hat: '#14183a', glow: '#ffb627' }), (m, a) => poseChar(m, a.x, a.y, S.time * .6, 0, false));
  if (vip && vip.hp > 0 && !vip.inCar && !vip.done && near(vip.x, vip.y)) sync(vip, () => { const m = makeChar({ shirt: '#ffd700', sleeve: '#1a1a1a', pants: '#1a1a1a', skin: '#8d5a3b', hat: '#ffffff', chain: true, glow: '#ffd700' }); m.userData.bar = hpBar(m, 30, 18); return m; }, (m, v) => { poseChar(m, v.x, v.y, v.a, v.step, false); setBar(m.userData.bar, v.hp / v.max, '#ffd700', true, v.a); });
  if (playing && !P.car) sync(P, () => makeChar({ shirt: '#21e6ff', sleeve: '#0f6f86', pants: '#1a1530', skin: '#f2d3b3', hair: '#1a120c', gun: true, shoes: '#ffffff' }), m => poseChar(m, P.x, P.y, P.a, P.step, false, true));
  for (const p of picks) if (near(p.x, p.y)) sync(p, () => makeProp('cash'), (m, e) => { m.position.set(e.x, Math.sin(S.time * 4 + e.x) * 2, e.y); m.rotation.y = S.time * 2; });
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
  R3.bul.count = Math.min(nb, 300); R3.bulE.count = Math.min(ne, 300); R3.bul.instanceMatrix.needsUpdate = true; R3.bulE.instanceMatrix.needsUpdate = true;
  // particules
  const pos = R3.pts.geometry.attributes.position, colA = R3.pts.geometry.attributes.color; let n = 0;
  for (const p of parts) { if (n >= R3.MAXP) break; const f = 1 - p.life / p.max; const cc = col3(p.col); const a = clamp(p.life / p.max, 0, 1);
    pos.setXYZ(n, p.x, p.grow ? 12 + f * 40 : 8 + (p.r > 6 ? f * 30 : 4), p.y); colA.setXYZ(n, cc.r * a, cc.g * a, cc.b * a); n++; }
  R3.pts.geometry.setDrawRange(0, n); pos.needsUpdate = true; colA.needsUpdate = true;
  // cible de mission
  const st = playing && L.step, target = st ? stepTarget(st) : null;
  R3.ring.visible = R3.beam.visible = !!target;
  if (target) { const pu = 1 + .12 * Math.sin(S.time * 4); R3.ring.position.set(target.x, 2, target.y); R3.ring.scale.setScalar(pu); R3.beam.position.set(target.x, 150, target.y); }
  R3.arrow.visible = !!(target && dist(P.x, P.y, target.x, target.y) > 200);
  if (R3.arrow.visible) { const a = Math.atan2(target.y - P.y, target.x - P.x), r = P.car ? 58 : 42; R3.arrow.position.set(P.x + Math.cos(a) * r, 6, P.y + Math.sin(a) * r); R3.arrow.rotation.y = -a; }
  R3.me.visible = !!playing; if (playing) R3.me.position.set(P.x, 1, P.y);
  // visée souris : on projette le pointeur sur le sol
  R3.ndc.set(mouse.sx / VW * 2 - 1, -(mouse.sy / VH) * 2 + 1); R3.ray.setFromCamera(R3.ndc, R3.cam);
  if (R3.ray.ray.intersectPlane(R3.plane, R3.hit)) { mouse.wx = R3.hit.x; mouse.wy = R3.hit.z; }
  R3.r.render(R3.scene, R3.cam);
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
        ${save.premium ? '' : `<button class="btn gold" data-go="unlock">Jeu complet${priceLabel() ? ' · ' + priceLabel() : ''}</button>`}
        ${canFull() ? '<button class="btn" data-full="1">Plein écran</button>' : ''}
      </div><div class="row center">${AU ? `<button class="btn small" data-snd="music">Musique : ${AU.prefs.music ? 'oui' : 'non'}</button><button class="btn small" data-snd="sfx">Bruitages : ${AU.prefs.sfx ? 'oui' : 'non'}</button>` : ''}
      </div>
      <div class="stats"><span>${done}/30 niveaux</span><span>${fmt(save.money)}</span><span>${save.premium ? 'Version complète' : 'Niveau 1 gratuit'}</span></div>
      <div class="keys">
        <b>ZQSD / flèches</b><span>Marcher, conduire</span>
        <b>E</b><span>Voiture, boutique, tunnel, payer un agent</span>
        <b>Espace / clic</b><span>Tirer · frein à main en voiture</span>
        <b>Q / molette / 1-7</b><span>Changer d'arme</span>
        <b>B</b><span>Soudoyer la police</span>
        <b>H · N / Maj</b><span>Trousse de soins · nitro</span>
      </div>
      <p class="legal">Jeu original. Lieux, gangs et personnages sont inventés.</p>
    </div>`;
  },
  map: () => {
    return `<div class="wrap">
      <div class="top"><button class="btn small" data-go="home">← Menu</button><h2>Carte des niveaux</h2><div class="row">${money()}<button class="btn small" data-go="shop">Boutique</button></div></div>
      ${D.REGIONS.map(r => `<section class="region" style="--acc:${r.accent}">
        <div class="rhead"><h3>${r.name}</h3><span>${r.country} · niveaux ${r.from}–${r.to}</span><p>${r.tagline}</p></div>
        <div class="grid">${D.LEVELS.slice(r.from - 1, r.to).map((l, i) => { const n = r.from + i; const ok = save.done[n], open = n <= save.maxLevel, paid = n > 1 && !save.premium;
          const cls = ok ? 'done' : open ? (paid ? 'paid' : 'open') : 'locked';
          const tag = ok ? '✓ Terminé' : paid ? 'Version complète' : open ? 'Disponible' : 'Verrouillé';
          return `<button class="lvl ${cls}" data-lvl="${n}"><span class="num">${n}</span><span class="lt">${esc(l.t)}</span><span class="tag">${tag}</span><span class="rw">+${fmt(levelBonus(n) + stepReward(n) * 10)}</span></button>`; }).join('')}</div>
      </section>`).join('')}
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
      <div class="info"><span>Récompense : <b>${fmt(levelBonus(n))}</b> + ${fmt(stepReward(n))} par étape</span>${l.boss ? `<span>Chef à abattre : <b>${esc(l.boss)}</b></span>` : ''}${recW && !save.owned[recW.id] ? `<span>Conseillé : ${recW.name}</span>` : ''}</div>
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
      <div class="tabs"><button class="${tab === 'w' ? 'on' : ''}" data-tab="w">Armes</button><button class="${tab === 'g' ? 'on' : ''}" data-tab="g">Équipement</button></div>
      <div class="items">${(tab === 'w' ? D.WEAPONS : D.GEAR).map(it => card(it, tab === 'w')).join('')}</div>
      ${tab === 'w' ? '<p class="legend"><span class="k1"></span>Dégâts <span class="k2"></span>Cadence</p>' : ''}
    </div>`;
  },
  pause: () => `<div class="wrap narrow center-col">
      <h2 class="title">Pause</h2>
      <p class="lead">Niveau ${L.n} · ${esc(L.def.t)} · étape ${L.idx + 1}/10</p>
      <div class="col"><button class="btn primary" data-resume="1">Reprendre</button><button class="btn" data-start="${L.n}">Recommencer le niveau</button><button class="btn" data-quit="1">Quitter vers la carte</button>${canFull() ? '<button class="btn" data-full="1">Plein écran</button>' : ''}<div class="row center">${AU ? `<button class="btn small" data-snd="music">Musique : ${AU.prefs.music ? 'oui' : 'non'}</button><button class="btn small" data-snd="sfx">Bruitages : ${AU.prefs.sfx ? 'oui' : 'non'}</button>` : ''}</div></div>
    </div>`,
  result: d => {
    const r = regionOf(d.n);
    if (d.ok) {
      const next = d.n + 1;
      return `<div class="wrap narrow center-col" style="--acc:${r.accent}">
        <p class="eyebrow">Niveau ${d.n} terminé</p><h2 class="title big">MISSION RÉUSSIE</h2>
        <div class="info"><span>Bonus de fin : <b>${fmt(d.bonus)}</b></span><span>Total gagné : <b>${fmt(d.earned)}</b></span><span>Temps : <b>${Math.floor(d.time / 60)} min ${String(Math.floor(d.time % 60)).padStart(2, '0')}</b></span></div>
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
function flashNote(t) { const n = document.createElement('div'); n.className = 'flash'; n.textContent = t; screenEl.appendChild(n); setTimeout(() => n.remove(), 1500); }
function pauseGame() { if (S.mode !== 'play') return; S.mode = 'pause'; au('duck', true); showScreen('pause'); }
function resumeGame() { S.mode = 'play'; au('duck', false); showScreen(null); lastT = performance.now(); }
function goLevel(n) { if (n > 1 && !save.premium) { showScreen('unlock'); return; } if (n > save.maxLevel) { flashNote('Termine le niveau ' + (n - 1) + ' d’abord'); return; } showScreen('brief', { n }); }
screenEl.addEventListener('click', e => {
  const b = e.target.closest('button,a'); if (!b) return;
  const ds = b.dataset;
  if (AU) { AU.init(); au('click'); if (!L || S.mode === 'menu') au('setMusic', 'menu'); }
  if (ds.snd) { AU && AU.toggle(ds.snd); showScreen(S.screen === 'pause' ? 'pause' : S.screen); return; }
  if (ds.go === 'shop') { openShop(false, ds.ret || S.screen); return; }
  if (ds.go) { if (ds.go === 'map') { S.mode = 'menu'; L = null; au('setMusic', 'menu'); } showScreen(ds.go); return; }
  if (ds.lvl) { goLevel(+ds.lvl); return; }
  if (ds.start) { const n = +ds.start; if (canPlay(n)) startLevel(n); else goLevel(n); return; }
  if (ds.tab) { shopState.tab = ds.tab; showScreen('shop', shopState); return; }
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
  const dt = Math.min(.05, (t - lastT) / 1000); lastT = t;
  if (S.mode === 'play') { update(dt); updHud(dt); }
  if (AU && AU.ready) { let sd = 1e9; if (S.mode === 'play') for (const c of cars) if (c.kind === 'police' && c.ai === 'police') sd = Math.min(sd, dist(c.x, c.y, P.x, P.y)); au('setIntensity', S.mode === 'play' && stars() > 0 ? 1 : 0); AU.update({ playing: S.mode === 'play', inCar: !!P.car, speed: P.car ? P.car.v : 0, nitro: P.nitro > 0, drift: !!(keys.Space || touch.shoot), sirenDist: sd }, dt); }
  else if (S.mode === 'result') { for (const p of parts) { p.life -= dt; } }
  render(dt);
  requestAnimationFrame(frame);
}
// décor du menu : la ville du premier pays
world = buildWorld(D.REGIONS[0]); P.x = cam.x = W / 2; P.y = cam.y = W / 2;
for (let i = 0; i < 60; i++) { const t = randWalk(0, W * 2, 0, 0); parkedCar(t.x, t.y); }
init3D();
if (ST) ST.init().then(st => { if (st.owned && !save.premium) { save.premium = true; persist(); } if (['home', 'unlock', 'map'].includes(S.screen)) showScreen(S.screen); });
showScreen('home');
requestAnimationFrame(frame);
window.__nb = { S, P, save, toggleCar, contextAction, hitEnemy, damageCar, get vip() { return vip; }, get agent() { return agent; }, get world() { return world; }, showScreen, get L() { return L; }, startLevel, nextStep, get enemies() { return enemies; }, get cars() { return cars; }, validCode, codeCheck, buy, D };
})();
