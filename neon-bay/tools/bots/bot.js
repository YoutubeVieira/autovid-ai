// Testeur automatique de Néon Bay : joue vraiment (mêmes vitesses, tirs, conduite et règles qu'un joueur),
// sans téléportation, en simulation accélérée (pas de rendu). Chargé dans la page par tools/bots/run.js.
(function () {
  const TAU = Math.PI * 2;
  const dist = (a, b, c, d) => Math.hypot(c - a, d - b);
  const ang = (a, b, c, d) => Math.atan2(d - b, c - a);
  const angDiff = (a, b) => { let d = (a - b) % TAU; if (d > Math.PI) d -= TAU; if (d < -Math.PI) d += TAU; return d; };
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const rnd = (a, b) => a + Math.random() * (b - a);

  async function runBot(profile, opts) {
    const nb = window.__nb, S = nb.S, P = nb.P, save = nb.save, D = nb.D;
    const DT = 0.05, report = { id: profile.id, name: profile.name, role: profile.role, levels: [], totalGame: 0, attempts: 0 };
    save.premium = true; save.diff = profile.diff; save.money = 500; save.maxLevel = 30; save.ghost = true;
    let mem = {};

    function bestWeapon() {
      if (profile.melee) return 'fists';
      let best = 'pistol', bv = 0;
      for (const w of D.WEAPONS) { if (!save.owned[w.id] || w.melee) continue; const a = P.ammo && P.ammo[w.id]; if (a && a.mag <= 0 && a.res <= 0) continue; const d = nb.wepDef(w.id); const v = d.dmg * d.pellets / d.rate * (w.explosive ? .6 : 1); if (v > bv) { bv = v; best = w.id; } }
      return best;
    }
    function shop() {
      const s = profile.shop; if (s === 'none') return;
      const buy = id => { try { nb.buy(id); } catch (e) {} };
      if (s === 'train' || s === 'max') for (let k = 0; k < 3; k++) for (const t of ['end', 'aim', 'str']) try { nb.train(t); } catch (e) {}
      const n = save.maxLevel;
      if (s !== 'contracts') { const ws = D.WEAPONS.filter(w => w.price && w.lvl <= mem.level && !save.owned[w.id]).sort((a, b) => b.price - a.price); for (const w of ws) if (save.money >= w.price * (s === 'max' || s === 'weapons' ? 1 : 2.5)) { buy(w.id); break; } }
      if (s !== 'noarmor') { const ar = D.GEAR.filter(g => g.kind === 'armor' && g.lvl <= mem.level && save.armor < g.value).sort((a, b) => b.value - a.value); for (const g of ar) if (save.money >= g.price * (s === 'max' ? 1 : 1.5)) { buy(g.id); break; } }
      for (let k = 0; k < 3 && save.medkits < (s === 'max' ? 5 : 3); k++) if (save.money > 1200) buy('medkit');
      if (profile.nitro) for (let k = 0; k < 3 && save.nitro < 6; k++) if (save.money > 2000) buy('nitro');
    }

    // --- navigation : itinéraire par les routes (même A* que le GPS du jeu) ---
    function waypoint(tx, ty) {
      const me = P.car || P, key = Math.round(tx / 40) + ',' + Math.round(ty / 40);
      if (!mem.path || mem.pkey !== key || mem.pT <= 0 || !mem.path.length) { mem.path = nb.route(me.x, me.y, tx, ty) || []; mem.pkey = key; mem.pT = 1.2; }
      while (mem.path.length > 1 && dist(me.x, me.y, mem.path[0].x, mem.path[0].y) < 46) mem.path.shift();
      return mem.path.length ? mem.path[0] : { x: tx, y: ty };
    }
    function walkTo(B, tx, ty) { const a = ang(P.x, P.y, tx, ty); B.mx = Math.cos(a); B.my = Math.sin(a); B.run = profile.run; }
    function driveTo(B, tx, ty, slow) {
      if (P.car.hp < 45) { (mem.badCar = mem.badCar || []).push(P.car); nb.toggleCar(); return; }
      const c = P.car, d = dist(c.x, c.y, tx, ty); let wp = waypoint(tx, ty);
      const p0 = mem.path || []; if (p0.length > 2) { const q = p0[Math.min(2, p0.length - 1)]; if (dist(c.x, c.y, q.x, q.y) < 200) wp = { x: (p0[1].x + q.x) / 2, y: (p0[1].y + q.y) / 2 }; }
      if (d < 140) wp = { x: tx, y: ty };
      const da = angDiff(ang(c.x, c.y, wp.x, wp.y), c.a), turn = Math.abs(da);
      if (d < 140 && turn > 1.1) { B.thr = c.v > 30 ? -1 : -.8; B.st = -Math.sign(da); return; } // cible dans le rayon de braquage : manœuvre en marche arrière
      B.st = clamp(da * 2.6, -1, 1);
      let vmax = slow ? 110 : turn > .7 ? 140 : d < 200 ? 160 : 480 * profile.drive;
      const p = mem.path || []; // virage à venir : direction à 3-4 cases devant, pas le zigzag case par case
      if (p.length > 3) { const far = p[Math.min(4, p.length - 1)], ta = Math.abs(angDiff(ang(c.x, c.y, far.x, far.y), c.a)); if (ta > .55) vmax = Math.min(vmax, 135 + (1 - Math.min(1, ta / 1.6)) * 140); }
      B.thr = turn > 1.7 ? (c.v > 60 ? -1 : .6) : c.v > vmax ? (c.v > vmax + 80 ? -1 : 0) : 1;
      B.nitro = profile.nitro && turn < .2 && d > 900;
      if (Math.abs(c.v) < 18 && B.thr > 0) mem.stuck = (mem.stuck || 0) + DT; else mem.stuck = 0;
      if (mem.stuck > 1.1) { mem.rev = .9; mem.stuck = 0; mem.revSt = -Math.sign(B.st || 1); mem.unstuck = (mem.unstuck || 0) + 1; if (mem.unstuck > 4) { mem.unstuck = 0; (mem.badCar = mem.badCar || []).push(c); nb.toggleCar(); return; } }
      if (Math.abs(c.v) > 120) mem.unstuck = 0;
      if (mem.rev > 0) { mem.rev -= DT; B.thr = -1; B.st = mem.revSt; }
    }
    function getCar(B) {
      if (P.car) return true;
      const cs = nb.cars.filter(c => !c.wreck && c.hp > 55 && c.kind !== 'police' && !c.convoy && !(mem.badCar || []).includes(c) && dist(c.x, c.y, P.x, P.y) < 700);
      if (!cs.length) return false;
      cs.sort((a, b) => dist(a.x, a.y, P.x, P.y) - dist(b.x, b.y, P.x, P.y)); const c = cs[0];
      if (dist(c.x, c.y, P.x, P.y) < 34) { nb.toggleCar(); if (!P.car) (mem.badCar = mem.badCar || []).push(c); return !!P.car; }
      walkTo(B, c.x, c.y); return 'going';
    }
    function goTo(B, tx, ty, o = {}) {
      if (P.car && P.car.hp < 45) { (mem.badCar = mem.badCar || []).push(P.car); nb.toggleCar(); return; }
      const me = P.car || P, d = dist(me.x, me.y, tx, ty);
      const wantCar = o.car || (profile.car && d > profile.carDist && !o.foot);
      if (o.foot && P.car) { if (Math.abs(P.car.v) > 60) { B.thr = -1; B.hb = true; return; } nb.toggleCar(); return; }
      if (wantCar && !P.car) { const r = getCar(B); if (r === 'going') return; if (!r && o.car) { walkTo(B, tx, ty); return; } }
      if (P.car) driveTo(B, tx, ty, o.slow); else walkTo(B, tx, ty);
    }
    function fight(B, foes, forceAim) {
      if (P.car) return false;
      const alive = foes.filter(e => e.hp > 0); if (!alive.length) return false;
      alive.sort((a, b) => dist(a.x, a.y, P.x, P.y) - dist(b.x, b.y, P.x, P.y)); const e = alive[0], d = dist(e.x, e.y, P.x, P.y);
      if (d > (forceAim ? 900 : profile.range)) return false;
      const w = bestWeapon(); if (save.weapon !== w) save.weapon = w;
      const am = P.ammo && P.ammo[w];
      if (profile.melee) { if (d > 30) walkTo(B, e.x, e.y); B.aimA = d < 40 ? ang(P.x, P.y, e.x, e.y) : null; B.shoot = d < 40; return true; }
      B.aimA = ang(P.x, P.y, e.x, e.y) + rnd(-profile.aimErr, profile.aimErr); B.shoot = !(am && am.mag <= 0 && am.res <= 0) && d < 520;
      if (d > 260) walkTo(B, e.x, e.y); else if (profile.strafe) { const a = ang(P.x, P.y, e.x, e.y) + Math.PI / 2 * (Math.sin(S.time * 1.3) > 0 ? 1 : -1); B.mx = Math.cos(a) * .7; B.my = Math.sin(a) * .7; }
      return true;
    }

    function escapeMove(B) {
      if (profile.tunnel) { const w = nb.world2; const tu = w.tunnels.slice().sort((a, b) => dist(a.x, a.y, P.x, P.y) - dist(b.x, b.y, P.x, P.y))[0]; if (tu && dist(tu.x, tu.y, P.x, P.y) < 1600) { if (dist(tu.x, tu.y, P.x, P.y) < 26 && !P.car) { mem.act = 'tunnel'; nb.contextAction2(); return; } goTo(B, tu.x, tu.y, dist(tu.x, tu.y, P.x, P.y) < 260 ? { foot: true } : { car: true }); return; } }
      if (!mem.esc || dist(P.x, P.y, mem.esc.x, mem.esc.y) < 200 || (mem.escT = (mem.escT || 0) + DT) > 25) { mem.escT = 0; const cops = nb.cars.filter(c => c.kind === 'police' && c.ai); const cx = cops.length ? cops.reduce((s2, c) => s2 + c.x, 0) / cops.length : P.x - 1, cy = cops.length ? cops.reduce((s2, c) => s2 + c.y, 0) / cops.length : P.y; const a = ang(cx, cy, P.x, P.y) + rnd(-.9, .9); const W = nb.W || 5248; mem.esc = { x: clamp(P.x + Math.cos(a) * 1500, 250, W - 250), y: clamp(P.y + Math.sin(a) * 1500, 250, W - 250) }; }
      goTo(B, mem.esc.x, mem.esc.y, { car: true });
    }
    function decide() {
      const L = nb.L, st = L.step, B = {}; S.bot = B; if (!st) return;
      mem.pT = (mem.pT || 0) - DT * profile.think;
      const g = 'g' + L.idx, maxHp = 100 + 15 * ((save.train || {}).end || 0);
      if (profile.heal && !P.car && S.hp < maxHp * .4 && save.medkits > 0 && (mem.hT || 0) <= 0) { nb.useMedkit(); mem.hT = 3; } mem.hT = (mem.hT || 0) - DT;
      const near = nb.enemies.filter(e => e.hp > 0 && dist(e.x, e.y, P.x, P.y) < profile.range && (e.alert || e.group === g));
      const tgt = st.dyn ? st.dyn() : st.target;
      // détour d'explorateur
      if (profile.wander && Math.random() < .002) mem.wander = { x: P.x + rnd(-900, 900), y: P.y + rnd(-900, 900), t: 12 };
      if (mem.wander && mem.wander.t > 0 && !near.length) { mem.wander.t -= DT; goTo(B, mem.wander.x, mem.wander.y); return; }
      const t = st.type;
      if (t === 'buy' && L.bought) return;
      // éviter l'arrestation : ne jamais rester immobile au contact d'un policier
      if (nb.stars() > 0) { const cop = nb.cars.filter(c => c.kind === 'police' && c.ai === 'police' && !c.wreck).sort((a, b) => dist(a.x, a.y, P.x, P.y) - dist(b.x, b.y, P.x, P.y))[0];
        if (cop && (S.bust > .25 || (P.car && dist(cop.x, cop.y, P.x, P.y) < 70 && Math.abs(P.car.v) < 40))) { mem.flee = 1.0; mem.fleeA = ang(cop.x, cop.y, P.x, P.y); } }
      { const fire = nb.cars.find(c => c.burn > 0 && c !== P.car && !c.wreck && dist(c.x, c.y, P.x, P.y) < 130); if (fire && !P.car) { mem.flee = .8; mem.fleeA = ang(fire.x, fire.y, P.x, P.y); } }
      if (P.car && P.car.burn > 0) { nb.toggleCar(); mem.flee = 1.2; mem.fleeA = rnd(0, 6.28); return; } // voiture en feu : on sort comme un joueur
      if (P.car && Math.abs(P.car.v) < 35 && S.bust > .7) { nb.toggleCar(); mem.fightCops = 3; return; } // coincé par la police : sortir et riposter
      if (mem.fightCops > 0 && !P.car) { mem.fightCops -= DT; const cop = nb.cars.filter(c => c.kind === 'police' && c.ai && !c.wreck).sort((a, b) => dist(a.x, a.y, P.x, P.y) - dist(b.x, b.y, P.x, P.y))[0];
        if (cop) { save.weapon = bestWeapon(); B.aimA = ang(P.x, P.y, cop.x, cop.y) + rnd(-profile.aimErr, profile.aimErr); B.shoot = true; const a = ang(cop.x, cop.y, P.x, P.y); B.mx = Math.cos(a); B.my = Math.sin(a); B.run = true; return; } }
      if (mem.flee > 0) { mem.flee -= DT; if (P.car) { const da = angDiff(mem.fleeA, P.car.a); B.st = clamp(da * 2, -1, 1); B.thr = Math.abs(da) > 2 ? -1 : 1; } else { B.mx = Math.cos(mem.fleeA); B.my = Math.sin(mem.fleeA); B.run = true; } return; }
      // stratégie humaine : semer la police avant de continuer quand il y a trop d'étoiles
      const combat = t === 'elim' || t === 'boss' || t === 'survive' || (t === 'jailbreak' && st.phase === 1);
      if (!combat && t !== 'escape' && nb.stars() >= profile.copsMax && !(st.time !== null && st.time < 25)) { escapeMove(B); return; }
      if ((t === 'elim' || t === 'boss' || (t === 'jailbreak' && st.phase === 1) || t === 'survive')) {
        const grp = nb.enemies.filter(e => e.hp > 0 && (e.group === g || t === 'survive'));
        if (fight(B, grp.length ? grp : near, true)) return;
        const e = grp.sort((a, b) => dist(a.x, a.y, P.x, P.y) - dist(b.x, b.y, P.x, P.y))[0] || tgt;
        if (e) goTo(B, e.x, e.y, dist(e.x, e.y, P.x, P.y) < 450 ? { foot: true } : {}); return;
      }
      const timed = st.time !== null && !st.survive;
      if (near.length && !P.car && profile.fightBack && (!timed || S.hp < 50) && fight(B, near.filter(e => dist(e.x, e.y, P.x, P.y) < (timed ? 160 : profile.range)))) return;
      switch (t) {
        case 'steal': { const c = st.car; if (!c) return; if (P.car === c) return; if (P.car) { nb.toggleCar(); return; } if (dist(c.x, c.y, P.x, P.y) < 40) nb.toggleCar(); else walkTo(B, c.x, c.y); return; }
        case 'garage': case 'deliver': {
          if (t === 'garage' && L.stolen && !L.stolen.wreck && P.car !== L.stolen) { if (P.car) { nb.toggleCar(); return; } if (dist(L.stolen.x, L.stolen.y, P.x, P.y) < 40) nb.toggleCar(); else walkTo(B, L.stolen.x, L.stolen.y); return; }
          if (tgt) goTo(B, tgt.x, tgt.y, { car: true, slow: dist(P.x, P.y, tgt.x, tgt.y) < 160 }); return;
        }
        case 'buy': case 'tunnel': case 'bribe': {
          const T = t === 'bribe' ? nb.agent : tgt; if (!T) return;
          if (dist(T.x, T.y, P.x, P.y) < (t === 'bribe' ? 40 : 26) && !P.car) { mem.act = t; nb.contextAction2(); return; }
          goTo(B, T.x, T.y, dist(T.x, T.y, P.x, P.y) < 300 ? { foot: true } : {}); return;
        }
        case 'escape': { escapeMove(B); return; }
        case 'escape_old': {
          if (profile.tunnel) { const w = nb.world2; const tu = w.tunnels.slice().sort((a, b) => dist(a.x, a.y, P.x, P.y) - dist(b.x, b.y, P.x, P.y))[0]; if (tu) { if (dist(tu.x, tu.y, P.x, P.y) < 26 && !P.car) { mem.act = 'tunnel'; nb.contextAction2(); return; } goTo(B, tu.x, tu.y, dist(tu.x, tu.y, P.x, P.y) < 300 ? { foot: true } : { car: true }); return; } }
          if (!mem.esc || dist(P.x, P.y, mem.esc.x, mem.esc.y) < 150) { const cops = nb.cars.filter(c => c.kind === 'police' && c.ai); const cx = cops.length ? cops.reduce((s, c) => s + c.x, 0) / cops.length : P.x - 1, cy = cops.length ? cops.reduce((s, c) => s + c.y, 0) / cops.length : P.y; const a = ang(cx, cy, P.x, P.y) + rnd(-.8, .8); const W = nb.W || 6000; mem.esc = { x: clamp(P.x + Math.cos(a) * 1400, 200, W - 200), y: clamp(P.y + Math.sin(a) * 1400, 200, W - 200) }; }
          goTo(B, mem.esc.x, mem.esc.y, { car: true }); return;
        }
        case 'escort': case 'jailbreak': {
          const vip = nb.vip; if (!tgt) return;
          if ((t === 'escort' && st.phase === 1) || (t === 'jailbreak' && st.phase === 2)) {
            const dd = dist(P.x, P.y, tgt.x, tgt.y);
            if (vip && !vip.inCar && P.car && profile.car) { const dv = dist(P.car.x, P.car.y, vip.x, vip.y); if (dv < 90) { B.thr = P.car.v > 20 ? -1 : 0; B.hb = true; return; } driveTo(B, vip.x, vip.y, true); return; }
            if (vip && !vip.inCar && !P.car && profile.car && dd > profile.carDist) { const r = getCar(B); if (r === 'going') return; }
            if (P.car) driveTo(B, tgt.x, tgt.y, false); else { if (vip && dist(vip.x, vip.y, P.x, P.y) > 160) { B.mx = 0; B.my = 0; return; } walkTo(B, tgt.x, tgt.y); }
            return;
          }
          goTo(B, tgt.x, tgt.y, t === 'jailbreak' && st.phase === 0 && dist(P.x, P.y, tgt.x, tgt.y) < 400 ? { foot: true } : {}); return;
        }
        case 'destroy': {
          const live = (st.cars || []).filter(c => !c.wreck); if (!live.length) return;
          const c = live.sort((a, b) => dist(a.x, a.y, P.x, P.y) - dist(b.x, b.y, P.x, P.y))[0], d = dist(c.x, c.y, P.x, P.y);
          if (d < 320) { if (P.car) { nb.toggleCar(); return; } const w = bestWeapon(); save.weapon = w; B.aimA = ang(P.x, P.y, c.x, c.y) + rnd(-profile.aimErr, profile.aimErr); B.shoot = true; if (d > 200) walkTo(B, c.x, c.y); return; }
          goTo(B, c.x, c.y, { car: d > 600 }); return;
        }
        default: if (tgt) goTo(B, tgt.x, tgt.y, { car: !!st.needCar }); return;
      }
    }

    async function attempt(n, from) {
      mem = { level: n, k: 0 }; nb.startLevel(n, from); S.cine = null; const t0 = S.time; let lastIdx = -1, idxT = 0, res = null;
      while (true) {
        if (S.mode === 'shop') { shop(); nb.resumeGame(); }
        if (S.mode === 'pause') nb.resumeGame();
        if (S.mode !== 'play') break;
        const L = nb.L; if (L.idx >= 10) break;
        if (L.idx !== lastIdx) { lastIdx = L.idx; idxT = 0; mem.path = null; mem.wander = null; mem.esc = null; mem.measure = 2; }
        if (mem.measure && --mem.measure === 0 && L.step && L.step.time !== null && !L.step.survive) {
          const st = L.step, rl = pts => { let t = 0, x = P.x, y = P.y; for (const q of pts) { const r = nb.route(x, y, q.x, q.y) || []; let px = x, py = y; for (const w of r) { t += dist(px, py, w.x, w.y); px = w.x; py = w.y; } t += dist(px, py, q.x, q.y); x = q.x; y = q.y; } return t; };
          const tg = st.pts || [st.dyn ? st.dyn() : st.target].filter(Boolean);
          if (tg.length) { const len = rl(tg); (report.timing = report.timing || []).push({ n, idx: L.idx, type: st.type, time: Math.round(st.time), route: Math.round(len), need: Math.round(len / Math.max(1, st.time)) }); }
        }
        idxT += DT * 2;
        if (idxT > opts.stepCap) { res = { ok: false, stuck: true, reason: 'bloqué', step: L.step && L.step.type, idx: L.idx }; break; }
        try { decide(); } catch (e) { report.botErrors = (report.botErrors || 0) + 1; if (!report.firstBotError) report.firstBotError = String(e && e.stack || e).slice(0, 300); S.bot = {}; }
        nb.sim(DT, 2);
        if (mem.act === 'tunnel') { mem.act = null; await new Promise(r => setTimeout(r, 760)); }
        if ((++mem.k % 400) === 0) await new Promise(r => setTimeout(r, 0));
      }
      S.bot = null;
      const L = nb.L, time = S.time - t0;
      if (!res) res = L && L.idx >= 10 ? { ok: true } : { ok: false, reason: S.lastFail || '?', step: S.lastFailStep, idx: L ? L.idx : -1 };
      res.time = Math.round(time); res.from = from; return res;
    }

    for (let n = opts.from || 1; n <= (opts.to || 30); n++) {
      mem = { level: n }; shop(); // passage en boutique avant le niveau, comme un joueur
      const lv = { n, tries: [], ok: false, time: 0 };
      let from = 0;
      for (let k = 0; k < opts.maxTries; k++) {
        const r = await attempt(n, from); lv.tries.push(r); lv.time += r.time; report.attempts++;
        if (r.ok) { lv.ok = true; break; }
        if (!profile.noCheckpoint && r.idx >= 5) from = 5;
      }
      lv.stars = (save.stars || {})[n] || 0; lv.money = save.money;
      report.levels.push(lv); report.totalGame += lv.time;
      if (opts.onLevel) opts.onLevel(lv);
    }
    report.gameErrors = S.simErrs || 0; report.gameError1 = S.simErr1 || '';
    return report;
  }
  window.NB_BOT = { runBot };
})();
