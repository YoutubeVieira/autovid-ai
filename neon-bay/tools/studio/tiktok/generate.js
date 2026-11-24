#!/usr/bin/env node
// Génère 50 projets Néon Studio verticaux (9:16) pour TikTok, plus le manifeste.
//   node tools/studio/tiktok/generate.js
// Sortie : tools/studio/tiktok/projets/NN-slug.json et tools/studio/tiktok/MANIFESTE.md
// Chaque projet porte ses métadonnées dans la clé « tiktok » (musique, passages intenses, légende, hashtags) :
// render-all.sh les relit pour lancer le rendu.
'use strict';
const fs = require('fs'), path = require('path');
const HERE = __dirname, ROOT = path.join(HERE, '..', '..', '..'), OUT = path.join(HERE, 'projets');
const PI = Math.PI;

// ---------- modèles d'exemple du studio (hélicoptère, moto) : relus dans js/studio.js pour rester identiques ----------
const studioSrc = fs.readFileSync(path.join(ROOT, 'js', 'studio.js'), 'utf8');
const genEx = k => { const m = studioSrc.match(new RegExp(k + ": (\\{ name: [\\s\\S]*?\\] \\}),\\n")); return m ? Function('return ' + m[1])() : null; };
const HELICO = genEx('helico'), MOTO = genEx('moto');

// ---------- briques ----------
let uidN = 0;
const R0 = [0, 0, 0], S1 = [1, 1, 1];
const obj = (asset, x = {}) => Object.assign({ id: x.id || asset + (++uidN), asset, name: x.name || asset, color: {}, clip: 'Idle', keys: [], base: { p: [0, 0, 0], r: [0, 0, 0], s: [1, 1, 1] } }, x);
const at = (p, ry = 0, s = S1) => ({ p, r: [0, ry, 0], s });
const smooth = u => u * u * (3 - 2 * u);
// trajectoire échantillonnée : f(t) -> [x, y, z] ; l'orientation suit la direction du mouvement (avant = +X)
function track(f, t0, t1, step = .25, face = true) {
  const keys = []; let last = 0;
  for (let t = t0; t <= t1 + 1e-6; t += step) {
    const p = f(t), q = f(t + .05), dx = q[0] - p[0], dz = q[2] - p[2];
    const ry = face && Math.hypot(dx, dz) > 1e-4 ? Math.atan2(-dz, dx) : last; last = ry;
    keys.push({ t: +t.toFixed(3), p: p.map(v => +v.toFixed(3)), r: [0, +ry.toFixed(4), 0], s: S1, ease: 'linear' });
  }
  return keys;
}
// position d'un objet à l'instant t (même interpolation que le studio)
function posAt(o, t) {
  const k = o.keys; if (!k.length) return o.base.p.slice();
  if (t <= k[0].t) return k[0].p.slice(); if (t >= k[k.length - 1].t) return k[k.length - 1].p.slice();
  let i = 0; while (i < k.length - 1 && k[i + 1].t < t) i++;
  const a = k[i], b = k[i + 1], u = (t - a.t) / Math.max(1e-6, b.t - a.t), e = a.ease === 'cut' ? 0 : a.ease === 'linear' ? u : smooth(u);
  return a.p.map((v, j) => v + (b.p[j] - v) * e);
}
const add = (a, b) => a.map((v, i) => +(v + b[i]).toFixed(3));
const ln = (a, b, u) => a.map((v, i) => v + (b[i] - v) * u);
// sous la route : point invisible qui sert de cible à la caméra
const pivot = (id, p, keys) => obj('cube', { id, name: 'Repère ' + id, base: at(p, 0, [.001, .001, .001]), keys: keys || [] });

// ---------- montage : la caméra est une suite de plans séparés par des coupes franches ----------
class Edit {
  constructor() { this.t = 0; this.keys = []; this.slow = []; this.titles = []; this.flashes = []; this.hotR = []; this.plan = []; }
  // spec : from, to (ou path), tg, ty, f, f1, sh, ease, slow (vitesse de l'action pendant le plan), hot
  shot(d, s, label) {
    const t0 = +this.t.toFixed(3), t1 = +(this.t + d).toFixed(3), pts = s.path || [s.from, s.to || s.from], n = pts.length - 1;
    pts.forEach((p, i) => { const last = i === n, tt = i === 0 ? t0 + (t0 > 0 ? .001 : 0) : t0 + d * i / n;
      this.keys.push({ t: +tt.toFixed(3), p: p.map(v => +v.toFixed(3)), r: s.r || R0, s: S1, f: +((s.f || 50) + ((s.f1 || s.f || 50) - (s.f || 50)) * i / Math.max(1, n)).toFixed(1), tg: s.tg, ty: s.ty != null ? s.ty : 1, sh: s.sh || 0, ease: last ? 'cut' : (s.ease || 'linear') }); });
    if (s.slow) this.slow.push({ t: t0, d: +d.toFixed(3), speed: s.slow });
    if (s.hot) this.hotR.push([t0, t1]);
    this.plan.push({ t: t0, d: +d.toFixed(2), label: label || '' });
    this.t = t1; return { t0, t1 };
  }
  // plan qui accompagne un objet : décalages relatifs à sa position au début et à la fin du plan (l'action peut être ralentie)
  follow(d, o, off0, off1, s = {}, label) {
    const ts1 = this.t + d * (s.slow || 1);
    return this.shot(d, Object.assign({ from: add(posAt(o, this.t), off0), to: add(posAt(o, ts1), off1 || off0), tg: o.id }, s), label);
  }
  black(d = .35) { this.titles.push({ t: +this.t.toFixed(3), d, text: '', style: 'card', cut: true }); this.plan.push({ t: +this.t.toFixed(2), d, label: 'noir' }); this.t += d; }
  flash() { this.flashes.push(+this.t.toFixed(3)); }
  text(t, d, text, style = 'title', x = {}) { this.titles.push(Object.assign({ t: +t.toFixed(3), d: +d.toFixed(3), text, style }, x)); }
  end(lang) {
    const t = +this.t.toFixed(3), d = 1.8;
    this.titles.push({ t, d, text: '', style: 'card', cut: true }, { t, d, text: 'NÉON|BAY', sub: lang === 'en' ? 'Play free · link in bio' : 'Joue gratuitement · lien en bio', style: 'logo' });
    this.plan.push({ t, d, label: 'carte finale' }); this.t += d;
  }
}

// ---------- pays ----------
const C = {
  usa: { id: 'usa', city: 'Néon Bay', fr: 'États-Unis', en: 'USA', amb: 'night', grade: 'teal', paint: '#ff2e93', neon: ['#ff2e93', '#21e6ff'], light: '#ff2e93', palms: true, music: 'usa', seed: 7, rain: true, wet: true },
  ita: { id: 'ita', city: 'Porto Lumi', fr: 'Italie', en: 'Italy', amb: 'sunset', grade: 'warm', paint: '#c8102e', neon: ['#ffb627', '#ff6b3d'], light: '#ffb627', palms: false, music: 'ita', seed: 23 },
  col: { id: 'col', city: 'Sierra Verde', fr: 'Colombie', en: 'Colombia', amb: 'day', grade: 'warm', paint: '#ffd23f', neon: ['#a6ff4d', '#ffd23f'], light: '#a6ff4d', palms: true, music: 'col', seed: 37 },
  bra: { id: 'bra', city: 'Morro Azul', fr: 'Brésil', en: 'Brazil', amb: 'sunset', grade: 'neon', paint: '#21e6ff', neon: ['#21e6ff', '#ffd23f'], light: '#ffd23f', palms: true, music: 'bra', seed: 53 },
};
// rue de ville avec palmiers, enseignes et quelques voitures garées
function city(c, o = {}) {
  const L = o.len || 260, x0 = o.x || 0, z0 = o.z || 0, list = [obj('street', { id: o.id || 'street', name: 'Rue ' + c.city, seed: o.seed || c.seed, length: L, base: at([x0, 0, z0]) })];
  if (c.palms && o.palms !== false) for (let x = -L / 2 + 10; x < L / 2 - 10; x += 16) list.push(obj('palm', { name: 'Palmier', base: at([x0 + x, .18, z0 + (x % 32 === 0 ? 11 : -11)], x) }));
  if (o.signs !== false) for (let i = 0; i < 5; i++) { const x = -40 + i * 21; list.push(obj('neon', { name: 'Enseigne', color: { Color: c.neon[i % c.neon.length] }, base: at([x0 + x, 4.5 + (i % 3), z0 + (i % 2 ? 11.85 : -11.85)], 0, [1.6, 1, 1]) })); }
  if (o.parked !== false) list.push(
    obj('car_van', { name: 'Fourgon garé', color: { Paint: '#e8e4dc' }, base: at([x0 + 24, 0, z0 + 5.6], PI) }),
    obj('car_suv', { name: 'SUV garé', color: { Paint: '#2a2f3a' }, base: at([x0 - 30, 0, z0 - 5.6]) }));
  return list;
}
const walker = (x, z, dir, t1, x2 = {}) => obj(x2.asset || 'human_f', Object.assign({ name: 'Passant', color: { Shirt: x2.shirt || '#ffd23f' }, clip: 'Walk', keys: track(t => [x + dir * 1.4 * t, .18, z], 0, t1, 1) }, x2.extra || {}));

// ---------- textes ----------
const NO_BRAND = /\bgta\b|grand theft|rockstar|take-?two|vice city|los santos|lucia|jason/i;
const T = (fr, en) => ({ fr, en });

// ============================================================================================
// SÉRIES : chaque fonction reçoit v (0..4) et lang, et renvoie { proj, meta }
// ============================================================================================

// 1. Poursuite de police
const S_CHASE = {
  key: 'poursuite', name: 'Poursuite de police',
  v: [
    { c: 'usa', car: 'car_sports', title: 'Poursuite sous la pluie', hook: 'Ils t’ont repéré.', mid: 'Tu cours ou tu payes ?', line: 'Tout le quartier filme.', leg: 'Trois voitures de police, une rue mouillée et pas de plan B.\nTu tiendrais combien de temps ?' },
    { c: 'bra', car: 'car_sedan', amb: 'night', title: 'Fuite à Morro Azul', hook: '10 secondes d’avance.', mid: 'Pas une de plus.', line: 'Sème-les avant le pont.', leg: 'Morro Azul, minuit. La police a 10 secondes de retard.\nDis-nous en commentaire par où tu passes.' },
    { c: 'ita', car: 'car_sports', title: 'Porto Lumi ne lâche rien', hook: 'La police de Porto Lumi ne lâche rien.', mid: 'Prends la ruelle.', line: 'Les sirènes résonnent jusqu’au port.', leg: 'Coucher de soleil, sirènes et pavés.\nQui conduit mieux que ça ?' },
    { c: 'usa', car: 'car_suv', amb: 'storm', title: 'Poursuite dans l’orage', hook: 'Sirènes derrière. Orage devant.', mid: 'Personne ne s’arrête au rouge.', line: 'Visibilité zéro. Pied au plancher.', leg: 'Orage sur Néon Bay, deux patrouilles au cul.\nTu freines ou tu passes ?' },
    { c: 'usa', car: 'car_sedan', en: 1, title: 'Night chase (EN)', hook: 'They spotted you.', mid: 'Run or pay?', line: 'The whole block is filming.', leg: 'Three cop cars, wet streets, no plan B.\nHow long would you last?' },
  ],
  tags: ['#poursuite', '#jeuvideo', '#mondeouvert', '#jeumobile', '#gaming'],
  tagsEn: ['#carchase', '#openworld', '#indiegame', '#mobilegame', '#gaming'],
  build(V, v, lang) {
    const c = C[V.c], amb = V.amb || c.amb, e = new Edit();
    const lane = t => t < 5 ? -2.4 : t < 6.5 ? -2.4 + 4.6 * smooth((t - 5) / 1.5) : t < 9.5 ? 2.2 : t < 10.8 ? 2.2 - 4.6 * smooth((t - 9.5) / 1.3) : -2.4;
    const path = t => [-130 + 20 * t, 0, lane(t)];
    const hero = obj(V.car, { id: 'hero', name: 'Voiture du héros', color: { Paint: c.paint }, keys: track(path, 0, 15) });
    const cop = obj('police', { id: 'cop', name: 'Police', keys: track(t => path(t - .9), 0, 15) });
    const cop2 = obj('police', { id: 'cop2', name: 'Police 2', keys: track(t => { const p = path(t - 2); p[2] = -p[2]; return p; }, 0, 15) });
    const objs = city(c, { len: 340 }).concat([hero, cop, cop2, walker(-40, 9.5, 1, 15), walker(30, -9.5, -1, 15, { asset: 'human_m', shirt: '#2e6bff' })]);
    e.follow(1.3, cop, [8, .9, -3.6], [6.5, .8, -3.2], { ty: 1.1, f: 52, sh: 1.5 }, 'accroche : gyrophare en gros plan');
    e.text(0, 1.6, V.hook, 'hook', { cut: true });
    const h0 = posAt(hero, e.t), h1 = posAt(hero, e.t + 2);
    e.shot(2, { from: [h0[0] - 14, 34, -30], to: [h1[0] + 4, 20, -22], tg: 'hero', ty: 0, f: 50, ease: 'ease' }, 'travelling aérien lent');
    e.flash(); e.follow(1, hero, [-1, .6, -5.5], [1.5, .7, -5.2], { f: 60, sh: 2, ty: .6, hot: 1 }, 'travelling latéral bas');
    const pass = posAt(hero, e.t + .9); e.shot(.9, { from: [pass[0] + 3, .45, .6], to: [pass[0] + 3.4, .5, .6], tg: 'hero', ty: .5, f: 72, hot: 1 }, 'la voiture frôle la caméra');
    e.text(e.t + .1, 1.9, c.city, 'sub', { sub: lang === 'en' ? c.en + ' · 2 AM' : c.fr + ' · 2 h du matin' });
    e.follow(2, hero, [-3, 1.2, 5], [3, 1, 5.5], { f: 50, slow: .25, ty: .7, hot: 1 }, 'ralenti : la caméra tourne autour');
    e.flash(); e.follow(.8, cop, [-6, 1.4, -1], [-5.4, 1.3, -.6], { tg: 'hero', ty: .6, f: 45, sh: 3, hot: 1 }, 'derrière la police');
    const ph = posAt(hero, e.t + .8); e.shot(1.6, { from: [ph[0] - 2, 1.6, 10.5], to: [ph[0], 1.6, 10.3], tg: 'hero', ty: .7, f: 62, sh: 3, hot: 1 }, 'filmé au téléphone depuis le trottoir');
    e.text(e.t - 1.5, 1.4, V.line, 'caption');
    e.black(.4);
    e.follow(1.6, hero, [-14, 3, 0], [-22, 15, 0], { ty: 1, f: 50, ease: 'ease' }, 'grue qui s’élève');
    e.text(e.t - 1.5, 1.5, V.mid, 'title');
    e.end(lang);
    return { e, objs, amb, rain: amb === 'storm' || c.rain, wet: amb !== 'day', grade: c.grade, music: c.music };
  },
};

// 2. Arrivée en ville par pays
const S_ARRIVAL = {
  key: 'arrivee', name: 'Arrivée en ville',
  v: [
    { c: 'usa', title: 'Arrivée à Néon Bay', hook: 'Nouvelle ville. Zéro dollar.', mid: 'Gangs de rue, rappeurs et docks en feu.', leg: 'Néon Bay, États-Unis : la première ville du jeu.\nTu commences avec zéro dollar et un cousin qui a des plans.' },
    { c: 'ita', title: 'Arrivée à Porto Lumi', hook: 'Ici, on ne dit pas non aux familles.', mid: 'Les familles règnent sur les canaux.', leg: 'Porto Lumi, Italie. Façades ocre, port de pêche et deux familles qui se détestent.\nTu choisis ton camp ?' },
    { c: 'col', title: 'Arrivée à Sierra Verde', hook: 'Atterrissage forcé.', mid: 'Jungle, pistes clandestines et cartels.', leg: 'Sierra Verde, Colombie. Ton avion vient de se poser en catastrophe.\nRosa connaît tout le monde ici.' },
    { c: 'bra', title: 'Arrivée à Morro Azul', hook: 'Morro Azul ne dort pas.', mid: 'Favelas, baile funk et guerre des bandes.', leg: 'Morro Azul, Brésil : couleurs, musique et deux bandes rivales.\nLa dernière ville avant… l’espace.' },
    { c: 'bra', amb: 'night', en: 1, title: 'Arriving in Morro Azul (EN)', hook: 'Morro Azul never sleeps.', mid: 'Favelas, baile funk and street wars.', leg: 'Morro Azul, Brazil: colors, music and two rival crews.\nThe last city before… space.' },
  ],
  tags: ['#voyage', '#jeuvideo', '#mondeouvert', '#ville', '#gaming'],
  tagsEn: ['#openworld', '#travel', '#indiegame', '#gaming', '#browsergame'],
  build(V, v, lang) {
    const c = C[V.c], amb = V.amb || c.amb, e = new Edit();
    const hero = obj('human_m2', { id: 'hero', name: 'Le héros', color: { Shirt: c.paint, Pants: '#2f4f86' }, clip: 'Walk', keys: track(t => [-30 + 1.4 * t, .18, 9.5], 0, 16, 1) });
    const cab = obj('car_sports', { id: 'cab', name: 'Cabriolet', color: { Paint: c.neon[1] }, keys: track(t => [70 - 16 * t, 0, 2.2], 0, 16, .5) });
    const npc = obj('human_f2', { id: 'npc', name: 'Habitante', color: { Shirt: c.neon[0] }, clip: 'Idle', base: at([-6, .18, -9.5], -PI / 2) });
    const objs = city(c, { len: 260 }).concat([hero, cab, npc, walker(-60, -9.5, 1, 16, { asset: 'human_m', shirt: '#f2f2f2' }), obj('bench', { name: 'Banc', base: at([-12, .18, 11], PI) })]);
    e.follow(1.4, hero, [2.6, .5, -1.2], [2.3, .6, -1], { ty: 1.5, f: 50 }, 'contre-plongée sur le héros qui avance');
    e.text(0, 1.7, V.hook, 'hook', { cut: true, bg: c.light === '#a6ff4d' ? '#1f9e4a' : undefined });
    e.shot(3, { from: [-70, 48, 46], to: [-48, 30, 34], tg: 'street', ty: 4, f: 46, ease: 'ease' }, 'établissement aérien très lent');
    e.text(1.8, 2.6, c.city, 'sub', { sub: lang === 'en' ? c.en : c.fr });
    const cp = posAt(cab, e.t + .6); e.flash(); e.shot(1.1, { from: [cp[0] - 2, .5, -.4], to: [cp[0] - 3, .55, -.4], tg: 'cab', ty: .5, f: 70, hot: 1 }, 'le cabriolet passe au ras de la caméra');
    e.follow(1, hero, [-3, 1.65, .6], [-2.6, 1.65, .5], { ty: 1.5, f: 60, sh: 2.5, hot: 1 }, 'au téléphone, dans le dos du héros');
    e.shot(1, { from: [-3, 1.5, -6], to: [-3.4, 1.5, -6.4], tg: 'npc', ty: 1.55, f: 34, hot: 1 }, 'gros plan habitante');
    e.shot(1.2, { from: [-20, .8, -4], to: [-14, .9, -4], tg: 'cab', ty: .6, f: 62, sh: 1, hot: 1 }, 'circulation, plan large bas');
    e.black(.4);
    e.follow(1.9, hero, [7, 1.2, -1.5], [5.5, 1.4, -1.2], { ty: 1.4, f: 44 }, 'le héros marche vers la caméra');
    e.text(e.t - 1.8, 1.8, V.mid, 'title', { size: .8 });
    e.end(lang);
    return { e, objs, amb, rain: false, wet: amb === 'night', grade: c.grade, music: c.music };
  },
};

// 3. Duel / braquage au ralenti
const S_DUEL = {
  key: 'duel', name: 'Duel et braquage au ralenti',
  v: [
    { kind: 'duel', c: 'usa', title: 'Face-à-face sous les néons', hook: 'Un seul des deux repart.', mid: 'Tout le monde a un prix.', line: 'Personne ne recule.', leg: 'Deux armes, une rue mouillée, zéro témoin.\nT’es plutôt pistolet ou fusil ?' },
    { kind: 'heist', c: 'ita', title: 'Le casse du casino Lumi', hook: 'Le coffre est plein. Le préfet aussi aime l’argent.', mid: 'Le casse.', line: '40 secondes avant les sirènes.', leg: 'Le casino Lumi, son coffre et un préfet qui ferme les yeux.\nTu fais le guet ou tu conduis ?' },
    { kind: 'duel', c: 'bra', title: 'Duel au coucher du soleil', hook: 'Le dernier qui bouge a gagné.', mid: 'Pas de deuxième chance.', line: 'Le temps ralentit.', leg: 'Morro Azul, 19 h. Deux bandes, un seul trottoir.\nQui tire le premier ?' },
    { kind: 'heist', c: 'col', amb: 'storm', title: 'Braquage sous l’orage', hook: 'L’orage couvre tout. Même l’alarme.', mid: 'On ne revient pas les mains vides.', line: 'Le fourgon tourne déjà.', leg: 'Sierra Verde, nuit d’orage, un fourgon qui attend.\nTu prends quoi dans le coffre ?' },
    { kind: 'duel', c: 'usa', amb: 'storm', en: 1, title: 'Standoff in the rain (EN)', hook: 'Only one walks away.', mid: 'Everyone has a price.', line: 'Nobody blinks.', leg: 'Two guns, a wet street, no witnesses.\nPistol or rifle?' },
  ],
  tags: ['#ralenti', '#jeuvideo', '#cinematique', '#mondeouvert', '#gaming'],
  tagsEn: ['#slowmotion', '#cinematic', '#openworld', '#indiegame', '#gaming'],
  build(V, v, lang) {
    const c = C[V.c], amb = V.amb || (V.kind === 'duel' && c.id === 'usa' ? 'night' : c.amb), e = new Edit();
    const objs = city(c, { len: 160, parked: false });
    if (V.kind === 'duel') {
      const a = obj('human_m', { id: 'a', name: 'Rafa', color: { Shirt: '#16141c', Hair: '#0c0c0c' }, clip: 'Aim', weapon: 'pistol', base: at([-3, 0, 0], PI / 2) });
      const b = obj('human_f', { id: 'b', name: 'Lia', color: { Shirt: '#c8102e' }, clip: 'AimRifle', weapon: v === 2 ? 'shotgun' : 'rifle', base: at([3, 0, 0], -PI / 2) });
      objs.push(a, b, pivot('mid', [0, .9, 0]), obj('car_sedan', { name: 'Voiture phares allumés', color: { Paint: '#101016' }, base: at([12, 0, -1], PI) }),
        obj('light', { name: 'Lumière néon', color: { Color: c.light }, intensity: 5, base: at([-6, 2, 4]) }));
      e.shot(1.2, { from: [-1.5, 1.5, -1.1], to: [-1.4, 1.5, -1.0], tg: 'a', ty: 1.45, f: 34 }, 'très gros plan : Rafa vise');
      e.text(0, 1.6, V.hook, 'hook', { cut: true });
      e.shot(2.2, { from: [0, 1.1, 13], to: [0, 1.5, 8.5], tg: 'mid', ty: .5, f: 52, ease: 'ease' }, 'plan large lent entre les deux');
      e.text(1.4, 2, c.city, 'sub', { sub: lang === 'en' ? c.en : c.fr });
      e.shot(.8, { from: [-4.4, 1.7, .9], to: [-4.3, 1.7, .8], tg: 'b', ty: 1.5, f: 40 }, 'par-dessus l’épaule de Rafa');
      e.shot(.8, { from: [4.4, 1.7, -.9], to: [4.3, 1.7, -.8], tg: 'a', ty: 1.5, f: 40 }, 'contrechamp');
      e.shot(.7, { from: [1.6, 1.55, 1.1], to: [1.5, 1.55, 1.0], tg: 'b', ty: 1.55, f: 30 }, 'gros plan Lia');
      e.flash(); e.shot(3, { path: [[0, 1.3, 4.5], [3.2, 1.4, 3.2], [4.5, 1.5, 0]], tg: 'mid', ty: .6, f: 50, slow: .2, hot: 1 }, 'bullet time : la caméra tourne, le temps s’arrête');
      e.text(e.t - 2.6, 2.2, V.line, 'title');
    } else {
      const van = obj('car_van', { id: 'van', name: 'Fourgon', color: { Paint: '#1a1a22' }, base: at([2, 0, -4]) });
      const r1 = obj('human_m', { id: 'r1', name: 'Braqueur 1', color: { Shirt: '#111111', Pants: '#111111' }, clip: 'Run', weapon: 'rifle', keys: track(t => [-4 + 1.8 * Math.min(t, 4), 0, -10.5 + 1.2 * Math.min(t, 4)], 0, 12, .5) });
      const r2 = obj('human_f', { id: 'r2', name: 'Braqueuse 2', color: { Shirt: '#ffd23f', Pants: '#111111' }, clip: 'Run', weapon: 'uzi', keys: track(t => [-7 + 2 * Math.min(t, 4.5), 0, -10.5 + 1 * Math.min(t, 4.5)], 0, 12, .5) });
      const cop = obj('police', { id: 'cop', name: 'Police', keys: track(t => [70 - 14 * Math.min(t, 4.6), 0, 2.2], 0, 12, .5) });
      objs.push(van, r1, r2, cop, pivot('mid', [-2, .9, -6]), obj('light', { name: 'Lumière', color: { Color: c.light }, intensity: 6, base: at([-4, 3, -9]) }));
      e.follow(1.3, r1, [3, 1.3, 1.5], [2.6, 1.3, 1.2], { ty: 1.4, f: 46, sh: 1 }, 'braqueur qui sort, caméra devant lui');
      e.text(0, 1.7, V.hook, 'hook', { cut: true, size: .8 });
      e.shot(2, { from: [-30, 14, 16], to: [-20, 8, 12], tg: 'mid', ty: 0, f: 46, ease: 'ease' }, 'établissement : la façade, le fourgon');
      e.text(1.5, 2, c.city, 'sub', { sub: lang === 'en' ? 'The heist' : 'Le casse' });
      e.flash(); e.follow(2.6, r2, [2.5, .9, -2], [3.5, 1.1, 2], { ty: 1.2, f: 44, slow: .25, hot: 1 }, 'ralenti sur la course vers le fourgon');
      e.follow(.9, cop, [6, .8, -2.5], [5, .8, -2], { ty: 1, f: 55, sh: 2, hot: 1 }, 'la police arrive');
      e.text(e.t - .8, 1.5, V.line, 'caption');
      e.shot(1, { from: [-1, 1.6, 6], to: [0, 1.6, 6], tg: 'van', ty: 1, f: 60, sh: 3, hot: 1 }, 'au téléphone, un témoin filme');
    }
    e.black(.4);
    e.text(e.t, 1.5, V.mid, 'card'); e.shot(1.5, { from: [0, 30, 40], tg: 'mid', ty: 0, f: 40 }, 'carton titre');
    e.end(lang);
    return { e, objs, amb, rain: amb === 'storm' || (c.rain && amb === 'night'), wet: amb !== 'day', grade: V.kind === 'duel' && v === 0 ? 'neon' : c.grade, music: c.music };
  },
};

// 4. Bateau et garde-côtes
const S_BOAT = {
  key: 'bateau', name: 'Bateau et garde-côtes',
  v: [
    { c: 'usa', amb: 'night', title: 'Garde-côtes à tes trousses', hook: 'Les garde-côtes sont sur toi.', mid: 'La mer n’a pas de feux rouges.', line: 'Cap sur les docks.', leg: 'Néon Bay de nuit, vu depuis l’eau. Les garde-côtes ont allumé le projecteur.\nTu passes par le port ou par le large ?' },
    { c: 'bra', amb: 'sunset', title: 'Course au large de Copa Azul', hook: 'Plein gaz vers Copa Azul.', mid: 'Personne ne te rattrape en mer.', line: 'Le soleil se couche. Pas toi.', leg: 'Course de vedettes au large de Morro Azul.\nTu prends le volant ?' },
    { c: 'usa', amb: 'storm', title: 'Fuite en mer dans la tempête', hook: 'Tempête. Hélico. Aucune issue.', mid: 'Tiens bon la barre.', line: 'Le projecteur te cherche.', leg: 'Tempête, hélicoptère et deux vedettes derrière toi.\nOn rentre au port ou on tente le large ?' },
    { c: 'ita', amb: 'sunset', title: 'Contrebande à Porto Lumi', hook: 'La livraison arrive par la mer.', mid: 'Le port appartient aux familles.', line: 'Les garde-côtes ont été prévenus.', leg: 'Porto Lumi : ici, la marchandise arrive par la mer.\nEt les garde-côtes ne sont pas tous honnêtes.' },
    { c: 'usa', amb: 'night', en: 1, title: 'Coast guard chase (EN)', hook: 'The coast guard is on you.', mid: 'No red lights at sea.', line: 'Head for the docks.', leg: 'Néon Bay by night, seen from the water.\nHarbor or open sea?' },
  ],
  tags: ['#bateau', '#jeuvideo', '#mondeouvert', '#cinematique', '#gaming'],
  tagsEn: ['#boatchase', '#openworld', '#indiegame', '#cinematic', '#gaming'],
  build(V, v, lang) {
    const c = C[V.c], amb = V.amb, e = new Edit();
    const zig = t => Math.sin(t * .7) * 5;
    const boat = obj('boat', { id: 'boat', name: 'Vedette', color: { Paint: c.paint }, keys: track(t => [-120 + 16 * t, 0, 30 + zig(t)], 0, 16, .25) });
    const cg = obj('boat', { id: 'cg', name: 'Garde-côtes', color: { Paint: '#ff6b3d' }, keys: track(t => [-120 + 16 * (t - 1.6), 0, 30 + zig(t - 1.6) + 3], 0, 16, .25) });
    const objs = [obj('sea', { id: 'sea', name: 'Mer', size: 520, base: at([0, 0, 60]) }), boat, cg,
      obj('street', { id: 'skyline', name: 'Front de mer', seed: c.seed + 3, length: 400, base: at([0, 0, -40]) })];
    if (v !== 1 && v !== 3) objs.push(obj('gen', { id: 'helico', name: 'Hélicoptère', spec: HELICO, keys: track(t => [-140 + 16 * t, 22, 36 + zig(t - 1)], 0, 16, .5) }),
      obj('light', { id: 'spot', name: 'Projecteur', color: { Color: '#fff2c8' }, intensity: 9, keys: track(t => [-138 + 16 * t, 3, 31 + zig(t)], 0, 16, .5, false) }));
    const hot = { hot: 1 };
    e.follow(1.3, boat, [-5, .6, 2.6], [-3.5, .7, 2.2], { ty: 1, f: 54, sh: 2 }, 'au ras de l’eau derrière la vedette');
    e.text(0, 1.6, V.hook, 'hook', { cut: true });
    e.shot(2.2, { from: [posAt(boat, 1.3)[0] - 30, 40, 90], to: [posAt(boat, 3.5)[0] - 6, 22, 70], tg: 'boat', ty: 0, f: 46, ease: 'ease' }, 'aérien lent, la ville au fond');
    e.text(1.6, 2.2, c.city, 'sub', { sub: lang === 'en' ? c.en + ' · offshore' : c.fr + ' · au large' });
    e.flash(); e.follow(1.1, boat, [-1, 1.2, 8], [2, 1.2, 7.5], Object.assign({ f: 55, sh: 1.5 }, hot), 'travelling latéral');
    e.follow(1, cg, [7, 1.8, -2], [6, 1.6, -1.5], Object.assign({ tg: 'boat', ty: .8, f: 40, sh: 2.5 }, hot), 'depuis la proue des garde-côtes');
    e.follow(2.2, boat, [6, .8, -4], [-2, 1, -6], Object.assign({ f: 50, slow: .25, ty: .9 }, hot), 'ralenti : la vedette fend la vague');
    e.text(e.t - 1.9, 1.6, V.line, 'caption');
    if (objs.some(o => o.id === 'helico')) e.follow(1, boat, [-12, 26, -6], [-6, 24, -5], Object.assign({ ty: 0, f: 46, sh: 1 }, hot), 'vue depuis l’hélicoptère');
    else e.follow(1, boat, [14, .5, 3], [10, .5, 3], Object.assign({ ty: .9, f: 62 }, hot), 'la vedette fonce vers la caméra');
    e.black(.4);
    e.follow(1.7, boat, [-16, 4, 10], [-26, 14, 16], { ty: .8, f: 48, ease: 'ease' }, 'la caméra recule et s’élève');
    e.text(e.t - 1.6, 1.6, V.mid, 'title');
    e.end(lang);
    return { e, objs, amb, rain: amb === 'storm', wet: false, grade: amb === 'sunset' ? 'warm' : 'teal', music: c.music };
  },
};

// 5. Fusée vers la Lune / Mars
const S_ROCKET = {
  key: 'fusee', name: 'Fusée vers la Lune et Mars',
  v: [
    { kind: 'launch', amb: 'night', title: 'Décollage de nuit', hook: '3… 2… 1…', mid: 'Prochain arrêt : la Lune.', line: 'Quand la ville devient trop petite.', leg: 'Quand la police de 4 pays te cherche, il reste une solution : la fusée.\nLune ou Mars, tu choisis quoi ?', music: 'moon' },
    { kind: 'moon', amb: 'moon', title: 'Base Tranquille, sur la Lune', hook: 'La Terre est au-dessus de ta tête.', mid: 'Gravité faible. Oxygène compté.', line: 'Base Tranquille · Lune', leg: 'Le jeu ne s’arrête pas sur Terre : il y a une base sur la Lune.\nLa Terre se lève derrière le dôme.', music: 'moon' },
    { kind: 'mars', amb: 'sunset', title: 'Colonie Ares, sur Mars', hook: 'Bienvenue sur Mars.', mid: 'Un ciel couleur rouille.', line: 'Colonie Ares · Mars', leg: 'Colonie Ares : tempêtes de poussière et colons armés.\nTu tiendrais combien de jours ?', music: 'mars' },
    { kind: 'launch', amb: 'sunset', title: 'Décollage au coucher du soleil', hook: 'Tout le monde te cherche. Tu pars.', mid: 'Tu quittes la Terre.', line: 'Fuir la Terre, c’est une option.', leg: 'Fin de la partie sur Terre, début de la partie dans l’espace.\nQui monte avec toi ?', music: 'mars' },
    { kind: 'moon', amb: 'moon', en: 1, title: 'Moon base (EN)', hook: 'Earth is above your head.', mid: 'Low gravity. Limited oxygen.', line: 'Tranquility Base · Moon', leg: 'The game doesn’t stop on Earth: there’s a base on the Moon.\nWould you go?', music: 'moon' },
  ],
  tags: ['#espace', '#lune', '#jeuvideo', '#fusee', '#gaming'],
  tagsEn: ['#space', '#moon', '#indiegame', '#rocket', '#gaming'],
  build(V, v, lang) {
    const e = new Edit(); let objs = [], grade = 'teal';
    if (V.kind === 'launch') {
      const rk = obj('rocket', { id: 'rocket', name: 'Fusée', ignite: 1.2, keys: [{ t: 0, p: [0, 0, 0], r: R0, s: S1, ease: 'linear' }, { t: 3.4, p: [0, 0, 0], r: R0, s: S1 }, { t: 7, p: [0, 30, 0], r: R0, s: S1, ease: 'linear' }, { t: 14, p: [0, 330, 0], r: R0, s: S1 }] });
      objs = [obj('street', { id: 'street', name: 'Ville', seed: 21, length: 200, base: at([0, 0, -50]) }), rk,
        obj('human_m', { id: 'hero', name: 'Toi', color: { Shirt: '#21e6ff' }, base: at([12, 0, 26], PI + .7) }), obj('car_suv', { name: 'Rover', color: { Paint: '#f4f4f4' }, base: at([-14, 0, 16], .7) })];
      for (let i = 0; i < 3; i++) objs.push(obj('lamp', { name: 'Projecteur', base: at([-12 + i * 12, 0, 10], PI) }));
      e.shot(1.3, { from: [2.5, 1.5, 4.5], to: [2.4, 1.3, 4.2], tg: 'rocket', ty: .5, f: 56, sh: .8 }, 'les tuyères s’allument');
      e.text(0, 1.5, V.hook, 'hook', { cut: true, size: 1.3 });
      e.shot(2.1, { from: [40, 3, 70], to: [32, 4, 56], tg: 'rocket', ty: 16, f: 42, ease: 'ease' }, 'plan large lent : la fusée sur son pas de tir');
      e.text(1.5, 2.1, lang === 'en' ? 'Launch pad' : 'Pas de tir', 'sub', { sub: lang === 'en' ? 'Néon Bay · 3 AM' : 'Néon Bay · 3 h du matin' });
      e.follow(1.2, rk, [11, 1.6, 22], [11, 1.6, 22], { tg: 'hero', ty: 1.5, f: 40, sh: .5 }, 'le héros regarde');
      e.flash(); e.shot(2.4, { from: [24, 2, 40], to: [26, 3, 44], tg: 'rocket', ty: 10, f: 44, sh: 6, slow: .3, hot: 1 }, 'ralenti du décollage, la caméra tremble');
      e.text(e.t - 2, 1.8, V.line, 'caption');
      e.shot(1.4, { from: [-5, 1.6, 30], to: [-4, 1.6, 30], tg: 'rocket', ty: 10, f: 60, sh: 3, hot: 1 }, 'au téléphone depuis la rue');
      e.black(.4);
      e.shot(1.8, { from: [60, 12, 120], to: [60, 8, 120], tg: 'rocket', ty: 0, f: 36 }, 'la fusée file vers le ciel');
      e.text(e.t - 1.7, 1.7, V.mid, 'title');
      grade = V.amb === 'sunset' ? 'warm' : 'teal';
    } else {
      const mars = V.kind === 'mars', rock = mars ? '#a4573a' : '#8a8a92';
      const robot = obj('robot', { id: 'bot', name: 'Astronaute', clip: 'Walk', keys: track(t => [-12 + 1.2 * t, 0, 8], 0, 16, 1) });
      const rover = obj('car_suv', { id: 'rover', name: 'Rover', color: { Paint: mars ? '#ff7a3d' : '#f4f4f4' }, keys: track(t => [40 - 6 * t, 0, -6], 0, 16, .5) });
      objs = [obj('rocket', { id: 'rocket', name: 'Fusée posée', color: { Color: mars ? '#ff7a3d' : '#d6332a' }, base: at([20, 0, -24]) }), robot, rover,
        obj('sphere', { id: 'dome', name: 'Dôme', color: { Color: '#e8e8ee' }, base: at([-26, -6, -30], 0, [26, 18, 26]) }),
        obj('sphere', { name: 'Dôme 2', color: { Color: '#d8dae2' }, base: at([-2, -3, -46], 0, [14, 10, 14]) }),
        obj('neon', { name: 'Balise', color: { Color: mars ? '#ff7a3d' : '#21e6ff' }, base: at([-26, 3, -17], 0, [3, 1, 1]) }),
        obj('light', { name: 'Lumière base', color: { Color: mars ? '#ffb27a' : '#cfe6ff' }, intensity: 6, base: at([-10, 3, 0]) })];
      for (let i = 0; i < 9; i++) objs.push(obj('sphere', { name: 'Rocher', color: { Color: rock }, base: at([-60 + i * 15, -.6, (i % 2 ? 20 : -14) + i], 0, [2 + i % 3, 1.2 + i % 2, 2.5]) }));
      e.follow(1.3, robot, [2.2, 1.2, 1.8], [1.9, 1.2, 1.6], { ty: 1.6, f: 44, sh: .6 }, 'l’astronaute avance vers nous');
      e.text(0, 1.6, V.hook, 'hook', { cut: true, bg: mars ? '#c2461f' : '#2b3d63' });
      e.shot(2.6, { from: [60, 28, 70], to: [40, 16, 50], tg: 'dome', ty: 6, f: 46, ease: 'ease' }, 'établissement : la base, très lent');
      e.text(1.6, 2.4, V.line.split(' · ')[0], 'sub', { sub: V.line.split(' · ')[1] });
      e.follow(1.3, rover, [-5, .8, 4], [-4, .8, 4], { tg: 'rover', ty: .8, f: 58, sh: 2, hot: 1 }, 'le rover passe');
      e.flash(); e.follow(2.4, robot, [3, 1.4, -3], [-3, 1.6, -3.5], { ty: 1.4, f: 46, slow: .3, hot: 1 }, 'ralenti autour de l’astronaute');
      e.shot(1.3, { from: [10, 1.6, 10], to: [11, 1.6, 10], tg: 'rocket', ty: 18, f: 50, sh: 2.5, hot: 1 }, 'au téléphone vers la fusée');
      e.black(.4);
      e.shot(1.8, { from: [-40, 4, 40], to: [-50, 10, 50], tg: 'dome', ty: 18, f: 50, ease: 'ease' }, mars ? 'le ciel rouille' : 'la Terre dans le ciel');
      e.text(e.t - 1.7, 1.7, V.mid, 'title');
      grade = mars ? 'warm' : 'teal';
    }
    e.end(lang);
    return { e, objs, amb: V.amb, rain: false, wet: false, grade, music: V.music, bloom: true };
  },
};

// 6. « POV : tu débarques à… »
const S_POV = {
  key: 'pov', name: 'POV : tu débarques à…',
  v: [
    { c: 'usa', title: 'POV Néon Bay', hook: 'POV : tu débarques à Néon Bay', l: ['Premier jour. Zéro dollar.', 'Mon cousin a dit : « reste discret ».', '… raté.'], leg: 'Premier jour à Néon Bay, zéro dollar en poche.\nTu aurais fait quoi à sa place ?' },
    { c: 'ita', title: 'POV Porto Lumi', hook: 'POV : tu débarques à Porto Lumi', l: ['Le soleil, le port, les lasagnes.', 'Puis un monsieur en costume te sourit.', 'Trop gentil pour être honnête.'], leg: 'Porto Lumi a l’air calme. Ça ne dure jamais.\nTu fais confiance au monsieur en costume ?' },
    { c: 'col', title: 'POV Sierra Verde', hook: 'POV : ton avion s’est posé à Sierra Verde', l: ['La piste était un champ.', 'Rosa dit qu’elle connaît tout le monde.', 'Tout le monde a l’air de la connaître aussi.'], leg: 'Atterrissage forcé en Colombie. Rosa a l’air sûre d’elle.\nOn la suit ?' },
    { c: 'bra', title: 'POV Morro Azul', hook: 'POV : tu débarques à Morro Azul', l: ['Musique partout. Couleurs partout.', 'Un DJ te demande un service.', 'Petit service. Gros problème.'], leg: 'Morro Azul : on te demande toujours un petit service.\nIl n’est jamais petit.' },
    { c: 'usa', en: 1, title: 'POV Néon Bay (EN)', hook: 'POV: you just landed in Néon Bay', l: ['Day one. Zero dollars.', 'My cousin said: “keep a low profile.”', '… yeah, no.'], leg: 'Day one in Néon Bay, zero dollars.\nWhat would you do?' },
  ],
  tags: ['#pov', '#jeuvideo', '#mondeouvert', '#jeumobile', '#gaming'],
  tagsEn: ['#pov', '#openworld', '#indiegame', '#mobilegame', '#gaming'],
  build(V, v, lang) {
    const c = C[V.c], e = new Edit();
    const eye = t => [-24 + 1.4 * t, 1.65, 8.8], look = t => [-24 + 1.4 * t + 8, 1.4, 7.2];
    const tgt = pivot('look', look(0), track(look, 0, 16, 1, false));
    const gun = obj('human_m', { id: 'gun', name: 'Le type louche', color: { Shirt: '#16141c' }, clip: 'Aim', weapon: 'pistol', base: at([-5, .18, 6.5], -PI / 2 - .5) });
    const suit = obj('human_m2', { id: 'suit', name: 'Le contact', color: { Shirt: '#f2f2f2', Pants: '#1d1a2e', Hat: '#111111' }, base: at([-11, .18, 8.6], PI) });
    const cop = obj('police', { id: 'cop', name: 'Police', keys: track(t => [60 - 15 * t, 0, 2.2], 0, 16, .5) });
    const cab = obj('car_sports', { id: 'cab', name: 'Cabriolet', color: { Paint: c.paint }, keys: track(t => [-80 + 18 * t, 0, -2.4], 0, 16, .5) });
    const objs = city(c, { len: 220 }).concat([tgt, gun, suit, cop, cab, walker(-10, 9.6, -1, 16, { asset: 'human_f2', shirt: c.neon[0] })]);
    const pov = (d, label, s = {}) => e.shot(d, Object.assign({ from: eye(e.t), to: eye(e.t + d), tg: 'look', ty: 0, f: 66, sh: 1.2 }, s), label);
    pov(1.6, 'subjectif : on marche sur le trottoir');
    e.text(0, 1.8, V.hook, 'hook', { cut: true, size: .8 });
    e.text(1.8, 2.2, V.l[0], 'caption');
    pov(2.2, 'subjectif, suite');
    const cp = posAt(cab, e.t + .5); e.flash(); e.shot(1, { from: [cp[0] + 2, .7, -5.6], to: [cp[0] + 1, .7, -5.6], tg: 'cab', ty: .6, f: 64, hot: 1 }, 'un cabriolet passe');
    e.shot(2, { from: [-13, 1.65, 8.9], to: [-12.4, 1.65, 8.9], tg: 'suit', ty: 1.6, f: 44, sh: 1, hot: 1 }, 'subjectif : le contact se retourne');
    e.text(e.t - 2, 2, V.l[1], 'caption');
    e.shot(1.3, { from: [-6.6, 1.6, 8.4], to: [-6.5, 1.6, 8.3], tg: 'gun', ty: 1.5, f: 40, sh: 2.2, hot: 1 }, 'quelqu’un sort une arme');
    const cpp = posAt(cop, e.t + .6); e.shot(1, { from: [cpp[0] - 6, 1.65, 8.6], to: [cpp[0] - 7, 1.65, 8.6], tg: 'cop', ty: .9, f: 58, sh: 2.5, hot: 1 }, 'la police déboule');
    e.black(.4);
    e.text(e.t, 1.7, V.l[2], 'title');
    e.shot(1.7, { from: [-6, 30, 26], to: [-6, 36, 30], tg: 'gun', ty: 0, f: 46 }, 'plongée : on te voit d’en haut');
    e.end(lang);
    return { e, objs, amb: c.amb, rain: false, wet: c.amb === 'night', grade: c.grade, music: c.music };
  },
};

// 7. « 3 secrets de Néon Bay »
const SEC = {
  tags: { fr: '12 tags secrets sont cachés dans les rues', en: '12 secret tags are hidden in the streets', shot: 'neon' },
  bribe: { fr: 'Tu peux acheter un flic. Il te revendra plus tard.', en: 'You can buy a cop. He’ll sell you out later.', shot: 'cop' },
  rocket: { fr: 'Quand la Terre est trop petite : la fusée', en: 'When Earth gets too small: the rocket', shot: 'rocket' },
  tunnels: { fr: 'Des tunnels de contrebandiers passent sous Porto Lumi', en: 'Smuggler tunnels run under Porto Lumi', shot: 'street' },
  jail: { fr: 'Tu peux faire évader des prisonniers', en: 'You can break prisoners out', shot: 'cop' },
  mars: { fr: 'Il y a une colonie sur Mars. Avec des colons armés.', en: 'There’s a colony on Mars. Armed colonists included.', shot: 'rocket' },
  strip: { fr: 'En Colombie, une piste d’atterrissage clandestine', en: 'A hidden airstrip in Colombia', shot: 'street' },
  nonna: { fr: 'Une mission entière pour sauver une trattoria', en: 'A whole mission to save a trattoria', shot: 'neon' },
  stars: { fr: 'Chaque niveau se finit avec 1 à 3 étoiles', en: 'Every level ends with 1 to 3 stars', shot: 'car' },
  free: { fr: 'Le niveau 1 est gratuit, sans inscription', en: 'Level 1 is free, no sign-up', shot: 'car' },
  moon: { fr: 'Sur la Lune, la Terre se lève au-dessus de ta tête', en: 'On the Moon, Earth rises above your head', shot: 'rocket' },
};
const S_SECRETS = {
  key: 'secrets', name: '3 secrets de Néon Bay',
  v: [
    { s: ['tags', 'bribe', 'rocket'], c: 'usa', title: '3 secrets (tags, flic, fusée)', hook: '3 secrets de Néon Bay', leg: 'Trois choses que la plupart des joueurs ratent.\nTu connaissais la troisième ?' },
    { s: ['tunnels', 'jail', 'mars'], c: 'usa', amb: 'storm', title: '3 secrets (tunnels, évasion, Mars)', hook: '3 trucs que personne ne voit', leg: 'Des tunnels, une évasion et une colonie sur Mars.\nLequel t’étonne le plus ?' },
    { s: ['strip', 'nonna', 'moon'], c: 'bra', amb: 'night', title: '3 secrets (piste, trattoria, Lune)', hook: '3 détails cachés dans Néon Bay', leg: 'Une piste clandestine, une trattoria et la Lune.\nOui, tout ça dans le même jeu.' },
    { s: ['stars', 'free', 'rocket'], c: 'usa', title: '3 choses à savoir avant de jouer', hook: '3 choses à savoir avant de jouer', leg: 'Avant de lancer ta première partie, lis ça.\nLa deuxième va te plaire.' },
    { s: ['tags', 'bribe', 'rocket'], c: 'usa', en: 1, title: '3 secrets (EN)', hook: '3 secrets of Néon Bay', leg: 'Three things most players miss.\nDid you know the third one?' },
  ],
  tags: ['#secrets', '#astuces', '#jeuvideo', '#mondeouvert', '#gaming'],
  tagsEn: ['#secrets', '#gamingtips', '#openworld', '#indiegame', '#gaming'],
  build(V, v, lang) {
    const c = C[V.c], amb = V.amb || c.amb, e = new Edit();
    const car = obj('car_sports', { id: 'car', name: 'Voiture', color: { Paint: c.paint }, keys: track(t => [-80 + 14 * t, 0, -2.4], 0, 16, .5) });
    const cop = obj('police', { id: 'cop', name: 'Police', base: at([6, 0, 4.2], PI - .3) });
    const guy = obj('human_m', { id: 'guy', name: 'Le flic', color: { Shirt: '#2e6bff', Pants: '#1d1a2e' }, base: at([3, .18, 7.5], PI / 2 + .6) });
    const me = obj('human_m2', { id: 'me', name: 'Toi', color: { Shirt: c.paint }, base: at([5, .18, 8.8], -PI / 2 - .4) });
    const rk = obj('rocket', { id: 'rocket', name: 'Fusée', ignite: 0, keys: track(t => [-240, Math.max(0, t - 9) ** 2 * 3, 0], 0, 16, .25, false) });
    const sign = obj('neon', { id: 'sign', name: 'Tag néon', color: { Color: '#a6ff4d' }, base: at([-20, 2.6, -11.85], 0, [1.2, 2.4, 1]) });
    const objs = city(c, { len: 220 }).concat([car, cop, guy, me, rk, sign, obj('light', { name: 'Halo', color: { Color: '#a6ff4d' }, intensity: 4, base: at([-20, 1.6, -9.5]) }),
      ...Array.from({ length: 3 }, (_, i) => obj('lamp', { name: 'Projecteur', base: at([-252 + i * 12, 0, 10], PI) }))]);
    const shotOf = (kind, d, label) => {
      if (kind === 'neon') return e.shot(d, { from: [-23, 1.5, -6], to: [-21.5, 1.6, -7], tg: 'sign', ty: 0, f: 44, sh: .8 }, label + ' : le tag néon');
      if (kind === 'cop') return e.shot(d, { from: [-1, 1.6, 10], to: [0, 1.6, 10.4], tg: 'guy', ty: 1.4, f: 46, sh: 1.2 }, label + ' : face au flic');
      if (kind === 'rocket') return e.shot(d, { from: [-210, 3, 40], to: [-212, 3, 44], tg: 'rocket', ty: 14, f: 46, sh: 2.5 }, label + ' : la fusée');
      if (kind === 'car') return e.follow(d, car, [-6, 1, -4], [-4, 1, -4.5], { ty: .7, f: 54, sh: 1 }, label + ' : la voiture');
      return e.shot(d, { from: [-60, 18, 0], to: [-30, 10, 0], tg: 'street', ty: 2, f: 50, ease: 'ease' }, label + ' : vue d’ensemble');
    };
    shotOf('car', 1.6, 'accroche'); e.text(0, 1.6, V.hook, 'hook', { cut: true });
    V.s.forEach((k, i) => {
      if (i === 2) e.black(.35); else e.flash();
      const t0 = e.t, d = i === 2 ? 3.4 : 3.2;
      e.text(t0, d, String(i + 1), 'title', { size: 2.4, y: .3, cut: true, fg: '#ffd23f' });
      e.text(t0 + .2, d - .2, SEC[k][lang], 'caption', { size: 1.05 });
      if (SEC[k].shot === 'rocket') { rk.ignite = +(t0 + .4).toFixed(2); rk.keys = track(t => [-240, Math.max(0, t - t0 - 1.2) ** 2 * 4, 0], 0, 16, .25, false); }
      shotOf(SEC[k].shot, d / 2, 'secret ' + (i + 1));
      shotOf(SEC[k].shot === 'street' ? 'car' : 'street', d / 2, 'secret ' + (i + 1) + ', 2e plan');
    });
    e.hotR.push([1.6, e.t]);
    e.end(lang);
    return { e, objs, amb, rain: amb === 'storm', wet: amb !== 'day', grade: c.grade, music: v === 2 ? 'bra' : 'usa' };
  },
};

// 8. Avant / après rendu
const S_BEFORE = {
  key: 'avant-apres', name: 'Avant / après rendu',
  v: [
    { amb: 'sunset', c: 'usa', title: 'Avant / après : la voiture', hook: 'Avant.', after: 'Après.', mid: 'Des cubes gris à Néon Bay.', leg: 'Tout commence par des cubes gris. Voilà ce qu’ils deviennent.\nTu veux voir d’autres avant/après ?', music: 'lofi' },
    { amb: 'night', c: 'usa', title: 'Avant / après : la rue de nuit', hook: 'Avant : des boîtes.', after: 'Après : Néon Bay.', mid: 'Même plan. Même caméra.', leg: 'Même plan, même caméra : à gauche les boîtes, à droite le rendu final.\nOn fait la même chose avec la Lune ?', music: 'usa' },
    { amb: 'day', c: 'col', title: 'Avant / après : Sierra Verde', hook: 'Version maquette.', after: 'Version finale.', mid: 'Chaque scène passe par là.', leg: 'Sierra Verde en maquette, puis en version finale.\nLaquelle tu préfères (mauvaise réponse : la première) ?', music: 'col' },
    { amb: 'storm', c: 'usa', title: 'Avant / après : l’orage', hook: 'Sans la pluie.', after: 'Avec la pluie.', mid: 'Ajoute l’orage. Tout change.', leg: 'Des cubes sous le soleil, puis la même rue sous l’orage.\nC’est la pluie qui fait tout, non ?', music: 'usa' },
    { amb: 'sunset', c: 'bra', en: 1, title: 'Before / after (EN)', hook: 'Before.', after: 'After.', mid: 'Grey boxes to Morro Azul.', leg: 'Every scene starts as grey boxes. Here’s what they become.\nWant more before/afters?', music: 'bra' },
  ],
  tags: ['#avantapres', '#gamedev', '#3d', '#jeuvideo', '#devlog'],
  tagsEn: ['#beforeandafter', '#gamedev', '#3d', '#indiegame', '#devlog'],
  build(V, v, lang) {
    const c = C[V.c], e = new Edit(), X = 600, grey = '#8d8d96';
    const carPath = (x0) => t => [x0 - 40 + 10 * t, 0, -2.4];
    const car = obj('car_sports', { id: 'car', name: 'Voiture', color: { Paint: c.paint }, keys: track(carPath(0), 0, 16, .5) });
    const box = obj('cube', { id: 'box', name: 'Cube voiture', color: { Color: grey }, keys: track(t => { const p = carPath(X)(t); p[1] = 0; return p; }, 0, 16, .5).map(k => Object.assign(k, { s: [4.4, 1.3, 1.9] })) });
    const hero = obj('human_m', { id: 'hero', name: 'Héros', color: { Shirt: c.paint }, clip: 'Walk', keys: track(t => [-20 + 1.4 * t, .18, 9.5], 0, 16, 1) });
    const cyl = obj('cylinder', { id: 'cyl', name: 'Cylindre perso', color: { Color: grey }, keys: track(t => [X - 20 + 1.4 * t, .18, 9.5], 0, 16, 1).map(k => Object.assign(k, { s: [.55, 1.8, .55] })) });
    const objs = city(c, { len: 200 }).concat([car, hero, box, cyl]);
    // maquette : des blocs gris à la place des immeubles, éclairés sobrement
    for (const sz of [-1, 1]) for (let i = 0; i < 12; i++) objs.push(obj('cube', { name: 'Bloc', color: { Color: i % 2 ? '#7a7a84' : grey }, base: at([X - 90 + i * 15, 0, sz * 18], 0, [12, 10 + (i * 7) % 22, 10]) }));
    objs.push(obj('cube', { name: 'Route maquette', color: { Color: '#5a5a62' }, base: at([X, -.48, 0], 0, [200, 1, 14]) }), obj('light', { name: 'Lumière maquette', color: { Color: '#ffffff' }, intensity: 8, base: at([X - 20, 10, 0]) }), obj('light', { name: 'Lumière maquette 2', color: { Color: '#ffffff' }, intensity: 8, base: at([X + 15, 10, 4]) }));
    const pair = (d, o1, o2, off0, off1, s, label) => { e.follow(d, o1, off0, off1, Object.assign({}, s), label + ' (maquette)'); e.flash(); e.follow(d, o2, off0, off1, Object.assign({}, s, { hot: 1 }), label + ' (rendu)'); };
    // 1re paire : la voiture
    e.text(0, 1.5, V.hook, 'hook', { cut: true, size: 1.4, bg: '#55555e' });
    e.follow(1.5, box, [-5, 1.2, -5], [-3, 1.1, -5.5], { tg: 'box', ty: .6, f: 52 }, 'accroche : la voiture en cube');
    e.text(e.t, 1.6, V.after, 'hook', { cut: true, size: 1.4 }); e.flash();
    e.follow(1.6, car, [-5, 1.2, -5], [-3, 1.1, -5.5], { ty: .6, f: 52, hot: 1 }, 'la même voiture, rendu final');
    // 2e paire : le personnage
    e.text(e.t, 1.3, lang === 'en' ? 'Before' : 'Avant', 'caption'); e.text(e.t + 1.3, 1.3, lang === 'en' ? 'After' : 'Après', 'caption');
    pair(1.3, cyl, hero, [3, 1.3, -1.6], [2.5, 1.4, -1.4], { ty: 1.2, f: 46 }, 'le personnage');
    // 3e paire : la rue entière, ralenti sur le rendu
    e.text(e.t, 1.4, lang === 'en' ? 'Before' : 'Avant', 'caption');
    e.shot(1.4, { from: [X - 50, 22, 26], to: [X - 40, 18, 22], tg: 'box', ty: 0, f: 50 }, 'la rue (maquette)');
    e.flash(); e.text(e.t, 2.2, lang === 'en' ? 'After' : 'Après', 'caption');
    e.shot(2.2, { from: [-50, 22, 26], to: [-40, 18, 22], tg: 'car', ty: 0, f: 50, slow: .35, hot: 1 }, 'la rue (rendu), ralenti');
    e.black(.4);
    e.text(e.t, 1.7, V.mid, 'title', { size: .85 });
    e.follow(1.7, car, [6, .6, -3], [8, .9, -2], { ty: .7, f: 56 }, 'la voiture s’éloigne');
    e.end(lang);
    return { e, objs, amb: V.amb, rain: V.amb === 'storm', wet: V.amb === 'night' || V.amb === 'storm', grade: V.amb === 'day' ? 'warm' : c.grade, music: V.music };
  },
};

// 9. « Ce jeu tourne dans un navigateur »
const S_BROWSER = {
  key: 'navigateur', name: 'Ce jeu tourne dans un navigateur',
  v: [
    { c: 'usa', title: 'Ça tourne dans un navigateur', hook: 'Ce jeu tourne dans un navigateur.', l: ['Pas de téléchargement.', 'Pas de console.', 'Juste un lien.'], mid: 'Niveau 1 gratuit.', leg: 'Pas de console, pas d’installation : un lien et tu joues.\nTu l’essaies sur quel appareil ?' },
    { c: 'bra', amb: 'night', title: 'Même sur un vieux téléphone', hook: 'Ton téléphone suffit.', l: ['Ouvre le lien.', 'Choisis ta ville.', 'C’est parti.'], mid: '4 pays. 30 missions.', leg: 'Un lien, ton téléphone, et 4 pays à prendre.\nAndroid ou navigateur, tu choisis.' },
    { c: 'ita', title: 'Dans un onglet, entre deux cours', hook: 'Un onglet. Une ville entière.', l: ['Pendant la pause.', 'Dans le bus.', 'Entre deux cours (on n’a rien dit).'], mid: 'Rien à installer.', leg: 'Une ville entière dans un onglet de navigateur.\nOn ne dira rien à ton prof.' },
    { c: 'usa', amb: 'storm', title: 'Pas besoin d’une console à 500 €', hook: 'Pas de console à 500 €.', l: ['Ton navigateur suffit.', 'Ou l’appli Android.', 'Le niveau 1 est gratuit.'], mid: 'Poursuites, gangs, fusée.', leg: 'Poursuites, gangs et une fusée, sans console.\nLe niveau 1 est gratuit, le reste coûte moins qu’un café.' },
    { c: 'usa', en: 1, title: 'Runs in your browser (EN)', hook: 'This game runs in a browser.', l: ['No download.', 'No console.', 'Just a link.'], mid: 'Level 1 is free.', leg: 'No console, no install: one link and you play.\nWhich device are you trying it on?' },
  ],
  tags: ['#jeunavigateur', '#jeumobile', '#jeuvideo', '#gratuit', '#gaming'],
  tagsEn: ['#browsergame', '#mobilegame', '#indiegame', '#freegame', '#gaming'],
  build(V, v, lang) {
    const c = C[V.c], amb = V.amb || c.amb, e = new Edit();
    const path = t => [-110 + 18 * t, 0, -2.4];
    const hero = obj('car_sports', { id: 'hero', name: 'Voiture', color: { Paint: c.paint }, keys: track(path, 0, 16, .25) });
    const cop = obj('police', { id: 'cop', name: 'Police', keys: track(t => path(t - 1), 0, 16, .25) });
    const moto = obj('gen', { id: 'moto', name: 'Moto néon', spec: MOTO, keys: track(t => [60 - 15 * t, 0, 2.6], 0, 16, .25) });
    const a = obj('human_f', { id: 'a', name: 'Lia', color: { Shirt: '#c8102e' }, clip: 'AimRifle', weapon: 'rifle', base: at([10, .18, -9.5], PI / 2 + .3) });
    const objs = city(c, { len: 300 }).concat([hero, cop, moto, a]);
    e.follow(1.5, hero, [5, .6, -3], [4, .6, -2.6], { ty: .6, f: 58, sh: 1 }, 'accroche : la voiture fonce vers la caméra');
    e.text(0, 1.7, V.hook, 'hook', { cut: true, size: .85 });
    e.shot(2, { from: [-80, 36, -40], to: [-58, 24, -30], tg: 'hero', ty: 0, f: 48, ease: 'ease' }, 'aérien lent');
    e.text(1.8, 2, V.l[0], 'caption');
    e.flash(); e.follow(1.2, cop, [-5, 1.2, 4], [-3, 1.2, 4.4], { tg: 'hero', ty: .6, f: 50, sh: 2, hot: 1 }, 'la police colle au pare-chocs');
    e.text(e.t - 1.2, 2.2, V.l[1], 'caption');
    e.follow(1, moto, [-4, .6, 2], [-6, .6, 2.4], { ty: .8, f: 56, hot: 1 }, 'la moto néon croise');
    e.shot(2, { path: [[7, 1.5, -6.5], [10, 1.6, -5.5], [13, 1.5, -6.5]], tg: 'a', ty: 1.5, f: 40, slow: .3, hot: 1 }, 'ralenti sur Lia qui vise');
    e.text(e.t - 1.9, 1.9, V.l[2], 'caption');
    const ph = posAt(hero, e.t + .6); e.shot(1, { from: [ph[0] - 3, 1.6, 10.4], to: [ph[0] - 1, 1.6, 10.4], tg: 'hero', ty: .7, f: 60, sh: 3, hot: 1 }, 'au téléphone sur le trottoir');
    e.black(.35);
    e.text(e.t, 1.7, V.mid, 'title');
    e.follow(1.7, hero, [-12, 4, 0], [-18, 12, 0], { ty: 1, f: 50, ease: 'ease' }, 'grue qui s’élève');
    e.end(lang);
    return { e, objs, amb, rain: amb === 'storm', wet: amb !== 'day' && amb !== 'sunset', grade: c.grade, music: c.music };
  },
};

// 10. Montage « vibes » au coucher du soleil
const S_VIBES = {
  key: 'vibes', name: 'Vibes au coucher du soleil',
  v: [
    { c: 'usa', title: 'Néon Bay, 19 h 42', hook: 'Néon Bay, 19 h 42.', line: 'Rien à faire. Tout à voir.', leg: 'Juste rouler, sans mission, au coucher du soleil.\nSauvegarde-la pour plus tard.', music: 'lofi', grade: 'warm' },
    { c: 'bra', title: 'Copa Azul au coucher du soleil', hook: 'Copa Azul, fin de journée.', line: 'Le baile commence dans une heure.', leg: 'Fin de journée à Morro Azul, la mer, les palmiers et la moto.\nTu restes jusqu’à la nuit ?', music: 'bra', grade: 'neon' },
    { c: 'ita', title: 'Porto Lumi, l’heure dorée', hook: 'L’heure dorée à Porto Lumi.', line: 'Même les familles font une pause.', leg: 'Porto Lumi à l’heure dorée. Pour une fois, personne ne tire.\nÇa ne va pas durer.', music: 'ita', grade: 'warm' },
    { c: 'col', title: 'Sierra Verde, fin d’après-midi', hook: 'Sierra Verde, 18 h.', line: 'La jungle s’endort. Pas la ville.', leg: 'Fin d’après-midi à Sierra Verde.\nUne vidéo calme, pour une fois.', music: 'col', grade: 'teal' },
    { c: 'usa', en: 1, title: 'Néon Bay sunset (EN)', hook: 'Néon Bay, 7:42 PM.', line: 'Nothing to do. Everything to see.', leg: 'Just driving at sunset, no mission.\nSave it for later.', music: 'lofi', grade: 'warm' },
  ],
  tags: ['#coucherdesoleil', '#ambiance', '#jeuvideo', '#chill', '#gaming'],
  tagsEn: ['#sunset', '#aesthetic', '#chill', '#indiegame', '#gaming'],
  build(V, v, lang) {
    const c = C[V.c], e = new Edit();
    const cab = obj('car_sports', { id: 'cab', name: 'Cabriolet', color: { Paint: c.paint }, keys: track(t => [-70 + 9 * t, 0, -2.4], 0, 16, .5) });
    const moto = obj('gen', { id: 'moto', name: 'Moto', spec: MOTO, keys: track(t => [50 - 8 * t, 0, 2.4], 0, 16, .5) });
    const boat = obj('boat', { id: 'boat', name: 'Vedette', color: { Paint: '#f4f4f4' }, keys: track(t => [-40 + 5 * t, 0, 70], 0, 16, .5) });
    const walkerH = obj('human_f2', { id: 'w', name: 'Promeneuse', color: { Shirt: c.neon[0] }, clip: 'Walk', keys: track(t => [-10 + 1.3 * t, .18, 9.5], 0, 16, 1) });
    const objs = city(c, { len: 240, parked: false, palms: true }).concat([cab, moto, boat, walkerH, obj('sea', { id: 'sea', name: 'Mer', size: 300, base: at([0, 0, 170]) })]);
    if (!c.palms) for (let x = -100; x < 100; x += 16) objs.push(obj('palm', { name: 'Palmier', base: at([x, .18, 11], x) }));
    e.shot(1.6, { from: [-30, 1.2, 30], to: [-26, 1.4, 28], tg: 'cab', ty: 1, f: 40 }, 'contre-jour : palmiers et cabriolet');
    e.text(0, 1.8, V.hook, 'hook', { cut: true, bg: '#ff7a3d' });
    e.shot(3, { from: [-60, 30, 60], to: [-30, 22, 50], tg: 'street', ty: 3, f: 46, ease: 'ease' }, 'très lent travelling sur la ville');
    e.follow(2, cab, [-1, 1, -5], [2, 1.1, -5], { ty: .8, f: 54 }, 'travelling sur le cabriolet');
    e.text(e.t - 1.8, 2, V.line, 'caption');
    e.follow(1.4, walkerH, [-2.6, 1.6, .8], [-2.2, 1.6, .6], { ty: 1.5, f: 56, sh: 2 }, 'au téléphone derrière la promeneuse');
    e.follow(2, moto, [4, .7, 3], [-3, .9, 3.5], { ty: .8, f: 48, slow: .35 }, 'ralenti : la moto passe');
    e.follow(1.6, boat, [-20, 4, -16], [-16, 4, -14], { ty: .6, f: 44 }, 'la vedette au large');
    e.black(.35);
    e.shot(1.6, { from: [0, 40, 20], to: [0, 48, 16], tg: 'street', ty: 0, f: 50 }, 'plongée finale');
    e.end(lang);
    e.hotR = [];
    return { e, objs, amb: 'sunset', rain: false, wet: false, grade: V.grade, music: V.music };
  },
};

// ============================================================================================
const SERIES = [S_CHASE, S_ARRIVAL, S_DUEL, S_BOAT, S_ROCKET, S_POV, S_SECRETS, S_BEFORE, S_BROWSER, S_VIBES];
const slugify = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\(en\)/, 'en').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40);
fs.mkdirSync(OUT, { recursive: true });
for (const f of fs.readdirSync(OUT)) if (f.endsWith('.json')) fs.unlinkSync(path.join(OUT, f));
const all = [];
SERIES.forEach((S, si) => S.v.forEach((V, v) => {
  uidN = 0; const n = si * 5 + v + 1, lang = V.en ? 'en' : 'fr';
  const r = S.build(V, v, lang), e = r.e, dur = +e.t.toFixed(2);
  const texts = e.titles.map(x => [x.text, x.sub].filter(Boolean).join(' ')).concat([V.leg, V.hook]);
  for (const s of texts) if (NO_BRAND.test(s)) throw new Error('Marque interdite dans la vidéo ' + n + ' : ' + s);
  if (dur < 10 || dur > 20) throw new Error('Durée hors limites (' + dur + ' s) pour la vidéo ' + n);
  if (!e.titles.some(x => x.t === 0 && x.style === 'hook')) throw new Error('Pas d’accroche à 0 s : ' + n);
  const cam = obj('camera', { id: 'cam', name: 'Caméra', fov: 50, keys: e.keys });
  const hot = e.hotR.map(([a, b]) => [Math.floor(a), Math.ceil(b)]).sort((a, b) => a[0] - b[0]).reduce((m, r) => { const l = m[m.length - 1]; if (l && r[0] <= l[1]) l[1] = Math.max(l[1], r[1]); else m.push(r); return m; }, []).map(r => r.join('-')).join(',');
  const slug = String(n).padStart(2, '0') + '-' + slugify(V.title);
  const tags = (lang === 'en' ? S.tagsEn : S.tags).concat(lang === 'en' ? ['#neonbay'] : ['#neonbay']).slice(0, 6);
  const proj = { v: 1, name: V.title, duration: dur, aspect: '9:16', res: 720, amb: r.amb, bloom: true, rain: !!r.rain, wet: !!r.wet, grade: r.grade, fades: false,
    objects: [cam].concat(r.objs), titles: e.titles, flashes: e.flashes, slow: e.slow,
    tiktok: { n, slug, series: S.name, seriesKey: S.key, lang, title: V.title, hook: V.hook, legend: V.leg, hashtags: tags, music: r.music, hot, duration: dur, plan: e.plan } };
  fs.writeFileSync(path.join(OUT, slug + '.json'), JSON.stringify(proj, null, 1) + '\n');
  all.push(proj.tiktok);
}));

// ---------- manifeste ----------
const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'], JOURS = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'];
const fmtD = d => `${JOURS[d.getUTCDay()]} ${d.getUTCDate()} ${MOIS[d.getUTCMonth()]}`;
// ordre de publication : on alterne les séries (jamais deux fois la même d'affilée) ; 2 vidéos du jeudi au dimanche, 1 sinon
const order = []; for (let i = 0; i < 5; i++) for (let s = 0; s < 10; s++) order.push(all[s * 5 + ((i + s) % 5)]);
const start = new Date(Date.UTC(2026, 10, 30)); const cal = []; let d = new Date(start), q = order.slice();
while (q.length) { const wd = d.getUTCDay(), two = [4, 5, 6, 0].includes(wd); const slots = two ? ['12 h 30', '19 h 00'] : ['19 h 00']; for (const h of slots) if (q.length) cal.push([fmtD(d), h, q.shift()]); d = new Date(d.getTime() + 864e5); }
const fmtS = s => s.toFixed(1).replace('.', ',') + ' s';
let md = `# Néon Bay · 50 vidéos TikTok verticales\n\nFichier généré par \`node tools/studio/tiktok/generate.js\` (ne pas modifier à la main : modifier le générateur puis relancer).\nRendu : \`tools/studio/tiktok/render-all.sh\` · vidéos dans \`marketing/tiktok/NN-slug.mp4\` (720×1280, 30 i/s).\nGrammaire de montage : \`tools/studio/tiktok/GRAMMAIRE.md\`.\n\n`;
md += `Toutes les vidéos : format 9:16, accroche en gros dès la première image, textes dans la zone sûre (15 % haut, 25 % bas, 12 % droite), carte finale de 1,8 s « NÉON BAY · Joue gratuitement · lien en bio ».\nVersions anglaises (10) : n° ${all.filter(x => x.lang === 'en').map(x => x.n).join(', ')}.\n\n`;
md += `| N° | Titre | Série | Langue | Accroche | Musique | Durée |\n|---|---|---|---|---|---|---|\n`;
for (const x of all) md += `| ${x.n} | ${x.title} | ${x.series} | ${x.lang.toUpperCase()} | ${x.hook} | ${x.music} | ${fmtS(x.duration)} |\n`;
md += `\n## Légendes prêtes à coller\n\n`;
for (const x of all) md += `### ${String(x.n).padStart(2, '0')} · ${x.title}${x.lang === 'en' ? ' · ANGLAIS' : ''}\nFichier : \`marketing/tiktok/${x.slug}.mp4\` · série : ${x.series} · musique : ${x.music} · ${fmtS(x.duration)}\n\n\`\`\`\n${x.legend}\n${x.hashtags.join(' ')}\n\`\`\`\n\n`;
md += `## Calendrier de publication conseillé\n\nDépart le lundi 30 novembre 2026. Une vidéo par jour du lundi au mercredi (19 h), deux du jeudi au dimanche (12 h 30 et 19 h), heure de Paris. Les séries alternent pour ne jamais publier deux fois la même d'affilée. Les vidéos en anglais peuvent aussi partir sur un second compte au même rythme.\n\n| Jour | Heure | N° | Titre | Langue |\n|---|---|---|---|---|\n`;
for (const [day, h, x] of cal) md += `| ${day} | ${h} | ${x.n} | ${x.title} | ${x.lang.toUpperCase()} |\n`;
md += `\nFin du calendrier : ${cal[cal.length - 1][0]}.\n`;
fs.writeFileSync(path.join(HERE, 'MANIFESTE.md'), md);
const tot = all.reduce((a, x) => a + x.duration, 0);
console.log(`${all.length} projets écrits dans ${path.relative(ROOT, OUT)}/ (${Math.round(tot)} s de vidéo au total, ${all.filter(x => x.lang === 'en').length} en anglais) + MANIFESTE.md`);
