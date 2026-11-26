#!/usr/bin/env node
// Introduction cinématique du jeu (premier lancement) : voix off Supertonic (media/intro/i1…i6.wav), plans calés sur la voix.
//   node tools/studio/intro.js            → tools/studio/intro.json (16:9) et tools/studio/intro-vertical.json (9:16, TikTok)
//   node tools/studio/render.js tools/studio/intro.json --res 720 --blur 3 --music usa --hot 9-21 --out media/intro.mp4
'use strict';
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const HERE = __dirname, ROOT = path.join(HERE, '..', '..'), PI = Math.PI;
const src = fs.readFileSync(path.join(HERE, 'tiktok', 'generate.js'), 'utf8');
const lib = src.slice(src.indexOf('// ---------- briques ----------'), src.indexOf('// ---------- textes ----------'));
const { obj, at, track, posAt, add, pivot, Edit, C, city, smooth } = Function('fs', 'path', 'ROOT', 'HELICO', 'MOTO', 'PI', 'require', lib + '\nreturn { obj, at, track, posAt, add, pivot, Edit, C, city, smooth };')(fs, path, ROOT, null, null, PI, require);

// durées réelles des répliques (pour caler les plans)
const dur = f => +execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path.join(ROOT, 'media', 'intro', f + '.wav')]).toString().trim();
const L = ['i1', 'i2', 'i3', 'i4', 'i5', 'i6'].map(id => ({ id, d: dur(id) }));

function build(aspect) {
  const c = C.usa, e = new Edit(), voice = [];
  // décor : la rue néon, la voiture du héros, la police, un fourgon (le « bus » de l'arrivée), des passants
  const X = t => -150 + 26 * Math.max(0, t - 9), CRASH = 17.2;
  const hk = []; for (let t = 0; t <= 24; t += .25) { const tt = +t.toFixed(2); hk.push({ t: tt, p: [+X(tt).toFixed(2), 0, tt < 13.5 ? -2.4 : 2.2 - 4.6 * Math.max(0, 1 - (tt - 13.5) / 1)], r: [0, 0, 0], s: [1, 1, 1], ease: 'linear' }); }
  const hero = obj('car_sedan', { id: 'hero', name: 'Voiture du héros', color: { Paint: '#ff2e93' }, keys: hk.filter(k => k.t >= 0) });
  // la police part en tonneaux au ralenti pendant le montage final
  const pk = []; for (let t = 0; t <= CRASH + 1e-6; t += .25) { const tt = +t.toFixed(2); pk.push({ t: tt, p: [+(X(tt) - 18 + Math.min(8, Math.max(0, tt - 9) * .8)).toFixed(2), 0, tt < 14 ? -2.4 : 2.2], r: [0, 0, 0], s: [1, 1, 1], ease: 'linear' }); }
  const px0 = X(CRASH) - 10;
  [[.5, [px0 + 8, 1.4, 3.4], [1.1, -.3, .1]], [1, [px0 + 14, 2.2, 4.4], [2.6, -.5, .15]], [1.5, [px0 + 18, 1.5, 5], [4.4, -.6, .1]], [1.9, [px0 + 20, 1.45, 5.2], [3 * PI, -.6, 0]], [6, [px0 + 20, 1.45, 5.2], [3 * PI, -.6, 0]]]
    .forEach(([dt, p, r]) => pk.push({ t: +(CRASH + dt).toFixed(2), p, r, s: [1, 1, 1], ease: 'ease' }));
  const cop = obj('police', { id: 'cop', name: 'Police', keys: pk });
  const walker = obj('human_m', { id: 'walker', name: 'Le héros (à pied)', color: { Shirt: '#16141c', Pants: '#2a3a5a', Skin: '#8d5a3b', Hair: '#0c0c0c' }, clip: 'Walk', keys: track(t => [-163 + 1.25 * t, .18, 8.6], 0, 9, .5).map(k => Object.assign(k, { r: [0, PI / 2, 0] })),
    faceKeys: [{ t: 0, w: {} }, { t: 6.2, w: { Smile: .25 } }, { t: 8.6, w: { Smile: .45, JawClench: .2 } }] });
  const van = obj('car_van', { id: 'van', name: 'Bus de nuit', color: { Paint: '#e8e4dc' }, keys: [{ t: 0, p: [-200, 0, 5.4], r: [0, 0, 0], s: [1, 1, 1] }, { t: 2.6, p: [-165, 0, 5.4], r: [0, 0, 0], s: [1, 1, 1] }, { t: 5.5, p: [-165, 0, 5.4], r: [0, 0, 0], s: [1, 1, 1] }, { t: 8, p: [-120, 0, 5.4], r: [0, 0, 0], s: [1, 1, 1] }] });
  // conducteur dans la voiture pour le gros plan « Grave erreur »
  const DRV = [-.15, -.62, -.38];
  const dk = hk.filter(k => k.t <= CRASH + 3).map(k => ({ t: k.t, p: add(k.p, DRV), r: [0, PI / 2, 0], s: [1, 1, 1], ease: 'linear' }));
  const driver = obj('human_m', { id: 'driver', name: 'Le héros (au volant)', color: { Shirt: '#16141c', Skin: '#8d5a3b', Hair: '#0c0c0c' }, clip: 'Idle', keys: dk, faceKeys: [{ t: 9, w: { JawClench: .4 } }, { t: 12.4, w: { Angry: .9, JawClench: .7 } }, { t: 14.2, w: { Angry: .6, Smile: .3 } }] });
  const face = pivot('face', [0, 1, 0], dk.map(k => ({ t: k.t, p: add(k.p, [0, 1.72, 0]), r: [0, 0, 0], ease: 'linear' })));
  const wface = pivot('wface', [0, 1, 0], walker.keys.map(k => ({ t: k.t, p: add(k.p, [0, 1.62, 0]), r: [0, 0, 0], ease: 'linear' })));
  const dash = obj('light', { id: 'dash', name: 'Lumière tableau de bord', color: { Color: '#9fdcff' }, intensity: 1.1, keys: dk.map(k => ({ t: k.t, p: add(k.p, [.45, 1.45, .1]), r: [0, 0, 0], s: [1, 1, 1], ease: 'linear' })) });
  const objs = city(c, { len: 520, x: -40 }).concat([hero, cop, walker, van, driver, face, wface, dash]);

  let t = 0; const cue = (i, at) => { voice.push({ t: +at.toFixed(2), file: 'media/intro/' + L[i].id + '.wav' }); return at + L[i].d; };
  e.black(.7); t = .7;
  // 1. « On m'a toujours dit… » : survol de la ville sous la pluie, puis le bus de nuit arrive
  let end = cue(0, .8);
  e.shot(2.6, { from: [-60, 70, 70], to: [-120, 52, 50], tg: 'van', ty: 0, f: 46, ease: 'ease' }, 'survol de la ville sous la pluie');
  e.follow(end + .3 - e.t, van, [-12, 1.1, -7], [-8, 1.3, -6.5], { ty: 1, f: 40, sh: .3 }, 'le bus de nuit s’arrête');
  // 2. « Moi, je suis resté. » : le héros descend, gros plan visage sous les néons
  end = cue(1, e.t + .2);
  e.follow(1.4, walker, [1.25, 1.66, -.75], [1.45, 1.7, -.7], { tg: 'wface', ty: 0, f: 32, sh: .3 }, 'gros plan : il lève les yeux vers les néons');
  e.follow(end + .4 - e.t, walker, [-4, 1.2, 3], [-2, 1.4, 3.6], { tg: 'walker', ty: 1.2, f: 40, sh: .4 }, 'il s’éloigne dans la rue');
  // 3. « Ils m'ont pris pour un touriste. » : la voiture rose démarre, la police surgit
  e.black(.25); end = cue(2, e.t + .1);
  e.follow(1.3, hero, [10, .6, -4.5], [6, .7, -4], { ty: .7, f: 40, sh: .4, hot: 1 }, 'la voiture rose démarre');
  e.follow(end + .2 - e.t, cop, [6, .9, -3.2], [4, .9, -3], { ty: .8, f: 45, sh: .6, hot: 1 }, 'gyrophares en gros plan');
  // 4. « Grave erreur. » : visage du conducteur, colère froide, par la vitre
  end = cue(3, e.t + .1);
  e.follow(end + .5 - e.t, driver, [.78, 1.8, .22], [.72, 1.78, .16], { tg: 'face', ty: 0, f: 30, sh: .25 }, 'gros plan : regard noir');
  // 5. « Quatre villes. Trente nuits. Une seule règle : ne jamais s'arrêter. » : montage rapide, ralenti des tonneaux
  e.flash(); end = cue(4, e.t + .05);
  e.follow(1, hero, [-8, 1.2, 2.5], [-6, 1.4, 2], { ty: .6, f: 42, sh: .8, hot: 1 }, 'la voiture coupe la route');
  e.text(e.t - 1, 1, 'QUATRE VILLES', 'title');
  e.follow(1.1, cop, [10, .5, 5], [7, .6, 4.4], { ty: .7, f: 40, sh: .8, hot: 1 }, 'la police colle derrière');
  e.text(e.t - 1.1, 1.1, 'TRENTE NUITS', 'title');
  e.flash(); e.shot(Math.max(2.4, end + .4 - e.t), { from: [px0 + 8, 1.3, -11], to: [px0 + 14, 2, -10], tg: 'cop', ty: .4, f: 40, slow: .3, hot: 1 }, 'ralenti : la police part en tonneaux');
  e.text(e.t - 1.8, 1.8, 'NE JAMAIS S’ARRÊTER', 'title');
  // 6. « Bienvenue à Néon Bay. » : carte titre
  e.black(.2); const t6 = e.t; cue(5, t6 + .3);
  e.titles.push({ t: +t6.toFixed(2), d: 3.2, text: '', style: 'card', cut: true }, { t: +t6.toFixed(2), d: 3.2, text: 'NÉON|BAY', sub: 'Bienvenue chez toi', style: 'logo' });
  e.t = t6 + 3.2;
  const d = +e.t.toFixed(2), cam = obj('camera', { id: 'cam', name: 'Caméra', fov: 50, keys: e.keys });
  return { v: 1, name: 'Introduction Néon Bay', duration: d, aspect, res: 720, amb: 'night', bloom: true, rain: true, wet: true, grade: 'teal', fades: false,
    objects: [cam].concat(objs), titles: e.titles, flashes: e.flashes, slow: e.slow, voice, plan: e.plan };
}
for (const [f, a] of [['intro.json', '16:9'], ['intro-vertical.json', '9:16']]) { const p = build(a); fs.writeFileSync(path.join(HERE, f), JSON.stringify(p, null, 1) + '\n'); console.log(f + ' · ' + p.duration + ' s · ' + p.voice.map(v => v.t).join(' / ')); }
