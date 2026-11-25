#!/usr/bin/env node
// Série « Poursuite embarquée » : vue subjective depuis le siège du conducteur, gros plans sur son visage,
// la police dans le dos, puis l'accident au ralenti. Inspirée de la grammaire des courtes histoires animées
// (POV, réaction du personnage, chute), avec nos propres décors, voitures et personnages.
//   node tools/studio/tiktok/embarquee.js   → tools/studio/tiktok/projets/51…55-*.json (ne touche pas aux 50 autres)
'use strict';
const fs = require('fs'), path = require('path');
const HERE = __dirname, OUT = path.join(HERE, 'projets'), PI = Math.PI;
// on réutilise les briques et le montage de generate.js (mêmes plans, mêmes coupes, même rendu)
const src = fs.readFileSync(path.join(HERE, 'generate.js'), 'utf8');
const lib = src.slice(src.indexOf('// ---------- briques ----------'), src.indexOf('// ---------- textes ----------'));
const { obj, at, track, posAt, add, pivot, Edit, C, city, smooth } = Function('fs', 'path', 'ROOT', 'HELICO', 'MOTO', 'PI', 'require', lib + '\nreturn { obj, at, track, posAt, add, pivot, Edit, C, city, smooth };')(fs, path, path.join(HERE, '..', '..', '..'), null, null, PI, require);

const V = [
  { n: 51, c: 'usa', car: 'car_sedan', paint: '#20232c', title: 'POV : la police te suit', hook: 'POV : la police te suit.', mid: 'Ils gagnent du terrain.', end: 'Tu aurais fait quoi ?', leg: 'Vue conducteur, sirènes dans le rétro, et un virage de trop.\nTu aurais freiné ?', music: 'usa' },
  { n: 52, c: 'bra', car: 'car_sports', paint: '#21e6ff', title: 'POV : dernier virage', hook: 'POV : tu crois les avoir semés.', mid: 'Le pont est fermé.', end: 'Erreur fatale.', leg: 'Morro Azul, 2 h du matin. Une seule erreur suffit.\nTu passes ou tu freines ?', music: 'bra' },
  { n: 53, c: 'ita', car: 'car_sports', paint: '#c8102e', title: 'POV : course de nuit à Porto Lumi', hook: 'POV : 200 à l’heure dans les ruelles.', mid: 'Un camion au carrefour.', end: 'Trop tard.', leg: 'Porto Lumi, coucher de soleil, et la police en embuscade.\nQui conduit mieux que ça ?', music: 'ita', amb: 'sunset' },
  { n: 54, c: 'usa', car: 'car_suv', paint: '#ffd23f', title: 'POV : la fuite sous l’orage', hook: 'POV : l’orage, la police, et toi.', mid: 'Les essuie-glaces ne suffisent plus.', end: 'Fin de la course.', leg: 'Visibilité zéro, deux patrouilles, une décision.\nTu tiendrais combien de temps ?', music: 'usa', amb: 'storm' },
  { n: 55, c: 'usa', car: 'car_sedan', paint: '#ff2e93', en: 1, title: 'POV: the cops are behind you (EN)', hook: 'POV: the cops are behind you.', mid: 'They are closing in.', end: 'What would you do?', leg: 'Driver POV, sirens in the mirror, one turn too many.\nWould you brake?', music: 'usa' },
];

for (const v of V) {
  const c = C[v.c], lang = v.en ? 'en' : 'fr', e = new Edit(), amb = v.amb || c.amb;
  // trajectoire : ligne droite, changement de voie pour éviter un camion, puis perte de contrôle et tonneaux
  const lane = t => t < 4.4 ? -2.4 : t < 5.4 ? -2.4 + 4.6 * smooth((t - 4.4) / 1) : 2.2;
  const X = t => -120 + 24 * t, CRASH = 9.2;
  const hk = []; for (let t = 0; t <= CRASH + 1e-6; t += .2) { const tt = +t.toFixed(2), dz = lane(tt + .05) - lane(tt); hk.push({ t: tt, p: [+X(tt).toFixed(2), 0, +lane(tt).toFixed(2)], r: [0, +(-Math.atan2(dz, 1.2) * .9).toFixed(3), 0], s: [1, 1, 1], ease: 'linear' }); }
  const x0 = X(CRASH), z0 = lane(CRASH);
  // tonneaux : la voiture décolle, tourne sur elle-même et retombe sur le toit
  [[.45, [x0 + 9, 1.4, z0 + 1.2], [1.1, -.25, .12]], [.9, [x0 + 16, 2.3, z0 + 2], [2.6, -.4, .2]], [1.35, [x0 + 21, 1.6, z0 + 2.6], [4.4, -.5, .1]], [1.75, [x0 + 24, 1.45, z0 + 2.8], [3 * PI, -.55, 0]], [4, [x0 + 24.5, 1.45, z0 + 2.8], [3 * PI, -.55, 0]]]
    .forEach(([dt, p, r]) => hk.push({ t: +(CRASH + dt).toFixed(2), p, r, s: [1, 1, 1], ease: 'ease' }));
  const hero = obj(v.car, { id: 'hero', name: 'Voiture du héros', color: { Paint: v.paint }, keys: hk });
  // conducteur assis : on le place dans la voiture (le bas du corps est caché par la carrosserie), puis il disparaît au moment du choc
  const DRV = [-.15, -.62, -.38]; // position du siège conducteur (côté gauche = -Z), tête vers 1,15 m
  const dk = hk.filter(k => k.t <= CRASH).map(k => ({ t: k.t, p: add(k.p, DRV), r: [0, k.r[1] + PI / 2, 0], s: [1, 1, 1], ease: 'linear' }));
  dk.push({ t: +(CRASH + .05).toFixed(2), p: [x0, -9, z0], r: [0, PI / 2, 0], s: [1, 1, 1], ease: 'cut' });
  const driver = obj('human_m', { id: 'driver', name: 'Conducteur', color: { Shirt: '#16141c', Skin: '#8d5a3b', Hair: '#0c0c0c' }, clip: 'Idle', keys: dk });
  const cop = obj('police', { id: 'cop', name: 'Police', keys: track(t => [X(t) - 22 + Math.min(10, t * .9), 0, t < 5.6 ? -2.4 : -2.4 + 4.6 * smooth(Math.min(1, (t - 5.6) / 1))], 0, CRASH + 4) });
  const cop2 = obj('police', { id: 'cop2', name: 'Police 2', keys: track(t => [X(t) - 40 + Math.min(14, t * 1.2), 0, 2.2], 0, CRASH + 4) });
  const truck = obj('car_van', { id: 'truck', name: 'Fourgon au carrefour', color: { Paint: '#e8e4dc' }, base: at([X(4.4) + 30, 0, -2.4], PI) });
  const look = pivot('look', [0, 1, 0], hk.filter(k => k.t <= CRASH).map(k => ({ t: k.t, p: [k.p[0] + 30, 1.1, k.p[2] * .6], r: [0, 0, 0], ease: 'linear' })));
  const face = pivot('face', [0, 1, 0], dk.filter(k => k.t <= CRASH).map(k => ({ t: k.t, p: add(k.p, [0, 1.72, 0]), r: [0, 0, 0], ease: 'linear' })));
  // lumière d'habitacle (tableau de bord) qui éclaire le visage, et reflet bleu-rouge des gyrophares
  const dash = obj('light', { id: 'dash', name: 'Lumière du tableau de bord', color: { Color: '#9fdcff' }, intensity: 2.2, keys: dk.filter(k => k.t <= CRASH).map(k => ({ t: k.t, p: add(k.p, [.45, 1.45, .1]), r: [0, 0, 0], s: [1, 1, 1], ease: 'linear' })).concat([{ t: +(CRASH + .05).toFixed(2), p: [x0, -9, z0], r: [0, 0, 0], s: [1, 1, 1], ease: 'cut' }]) });
  const objs = city(c, { len: 600, x: 60 }).concat([hero, driver, cop, cop2, truck, look, face, dash]);

  const EYE = [.38, 1.2, -.38]; // devant la tête du conducteur (sinon la caméra est dans sa tête) // œil du conducteur, relatif à la voiture
  const pov = (d, label, extra = {}) => e.follow(d, hero, EYE, EYE, Object.assign({ tg: 'look', ty: 0, f: 30, ease: 'linear', sh: .6 }, extra), label);
  // 1. accroche : vue du conducteur, la route défile, le gyrophare dans le dos
  pov(1.5, 'POV conducteur : la route, les gyrophares derrière');
  e.text(0, 1.5, v.hook, 'hook', { cut: true });
  // 2. extérieur bas, devant la voiture : la police colle derrière
  e.follow(1.2, hero, [14, .6, -4.5], [7, .6, -4], { ty: .7, f: 42, ease: 'linear', sh: .5, hot: 1 }, 'extérieur bas devant : la police derrière');
  // 3. gros plan visage à travers le pare-brise
  e.follow(1.3, driver, [.35, 1.74, -1.05], [.3, 1.74, -1.0], { tg: 'face', ty: 0, f: 34, ease: 'linear', sh: .4 }, 'gros plan visage par la vitre, mâchoire serrée');
  // 4. POV : le fourgon au carrefour, coup de volant (changement de voie)
  pov(1.2, 'POV : coup de volant pour éviter le fourgon', { hot: 1 });
  // 5. regard dans le rétro : la police gagne du terrain
  e.follow(1.2, hero, [.6, 1.2, -.42], [.6, 1.2, -.42], { tg: 'cop', ty: .8, f: 40, ease: 'linear', sh: .4, hot: 1 }, 'regard arrière : les gyrophares se rapprochent');
  e.text(e.t - 1.2, 1.2, v.mid, 'caption');
  // 6. gros plan visage, plus serré
  e.follow(1.2, driver, [.7, 1.72, -.95], [.55, 1.72, -.9], { tg: 'face', ty: 0, f: 42, ease: 'linear', sh: .7, hot: 1 }, 'visage de trois-quarts, la tension monte');
  // 7. dernier POV avant le choc
  pov(CRASH - e.t - .05, 'POV : la voiture décroche', { sh: 1.2, hot: 1 });
  // 8. l'accident au ralenti, plan large extérieur
  e.flash(); e.shot(2.6, { from: [x0 + 6, 1.4, z0 - 15], to: [x0 + 14, 2.2, z0 - 13], tg: 'hero', ty: .4, f: 40, slow: .3, hot: 1 }, 'ralenti : tonneaux');
  // 9. après : la voiture sur le toit, la police arrive
  e.shot(1.6, { from: [x0 + 34, 1.3, z0 + 9], to: [x0 + 33, 1.3, z0 + 8], tg: 'hero', ty: .4, f: 38, sh: .5 }, 'la voiture sur le toit, sirènes');
  e.text(e.t - 1.6, 1.6, v.end, 'title');
  e.black(.35); e.end(lang);

  const dur = +e.t.toFixed(2), cam = obj('camera', { id: 'cam', name: 'Caméra', fov: 50, keys: e.keys });
  const slug = v.n + '-' + v.title.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\(en\)/, 'en').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40);
  const hot = '1-' + Math.ceil(dur - 2);
  const proj = { v: 1, name: v.title, duration: dur, aspect: '9:16', res: 720, amb, bloom: true, rain: amb === 'night' || amb === 'storm', wet: amb !== 'sunset', grade: c.grade, fades: false,
    objects: [cam].concat(objs), titles: e.titles, flashes: e.flashes, slow: e.slow,
    tiktok: { n: v.n, slug, series: 'Poursuite embarquée', seriesKey: 'embarquee', lang, title: v.title, hook: v.hook, legend: v.leg, hashtags: (lang === 'en' ? ['#pov', '#carchase', '#openworld', '#mobilegame', '#gaming'] : ['#pov', '#poursuite', '#jeuvideo', '#jeumobile', '#gaming']).concat(['#neonbay']), music: v.music, hot, duration: dur, plan: e.plan } };
  fs.writeFileSync(path.join(OUT, slug + '.json'), JSON.stringify(proj, null, 1) + '\n');
  console.log(slug + ' · ' + dur + ' s');
}
