/* Néon Bay : sons et musiques.
   Tout est synthétisé en direct (Web Audio) : aucun fichier, aucun droit d'auteur.
   On peut remplacer n'importe quel son par un fichier : voir NB_DATA.AUDIO_FILES dans js/data.js. */
window.NB_AUDIO = (() => {
  'use strict';
  let ctx = null, master, sfxBus, musBus, comp, noiseBuf;
  const prefs = (() => { try { return Object.assign({ sfx: true, music: true }, JSON.parse(localStorage.getItem('neonbay.audio') || '{}')); } catch (e) { return { sfx: true, music: true }; } })();
  const savePrefs = () => { try { localStorage.setItem('neonbay.audio', JSON.stringify(prefs)); } catch (e) {} };
  const files = {}; // buffers chargés depuis des fichiers
  let tOff = 0;
  const now = () => ctx.currentTime + tOff;
  const rnd = (a, b) => a + Math.random() * (b - a);

  function init() {
    if (ctx) { if (ctx.state === 'suspended') ctx.resume(); return; }
    const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
    ctx = new AC();
    comp = ctx.createDynamicsCompressor(); comp.threshold.value = -14; comp.ratio.value = 4; comp.connect(ctx.destination);
    master = ctx.createGain(); master.gain.value = .9; master.connect(comp);
    sfxBus = ctx.createGain(); sfxBus.gain.value = prefs.sfx ? .8 : 0; sfxBus.connect(master);
    musBus = ctx.createGain(); musBus.gain.value = prefs.music ? .42 : 0; musBus.connect(master);
    noiseBuf = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
    const d = noiseBuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    // réverbération de rue : les tirs et explosions résonnent entre les immeubles
    try { const len = ctx.sampleRate * 1.8, ir = ctx.createBuffer(2, len, ctx.sampleRate);
      for (let c = 0; c < 2; c++) { const ch = ir.getChannelData(c); for (let i = 0; i < len; i++) ch[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 3.2) * (i < 900 ? .2 : 1); }
      const conv = ctx.createConvolver(); conv.buffer = ir; const send = ctx.createGain(); send.gain.value = .28; const hp = ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 220;
      sfxBus.connect(send); send.connect(hp); hp.connect(conv); conv.connect(master); } catch (e) {}
    loadFiles();
  }
  async function loadFiles() {
    const cfg = (window.NB_DATA && window.NB_DATA.AUDIO_FILES) || {};
    for (const [k, url] of Object.entries(cfg)) {
      if (!url) continue;
      try { const r = await fetch(url); if (!r.ok) continue; files[k] = await ctx.decodeAudioData(await r.arrayBuffer()); } catch (e) {}
    }
  }
  // ---------- briques ----------
  function out(bus, pan = 0, vol = 1) {
    const g = ctx.createGain(); g.gain.value = vol;
    if (ctx.createStereoPanner) { const p = ctx.createStereoPanner(); p.pan.value = Math.max(-1, Math.min(1, pan)); g.connect(p); p.connect(bus); } else g.connect(bus);
    return g;
  }
  function env(g, t, a, peak, dec, sus = 0, rel = 0) {
    g.gain.cancelScheduledValues(t); g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(Math.max(peak, .0002), t + a);
    g.gain.exponentialRampToValueAtTime(Math.max(sus, .0001), t + a + dec);
    if (rel) g.gain.exponentialRampToValueAtTime(.0001, t + a + dec + rel);
  }
  function noise(dest, t, dur, type, freq, q = 1, peak = 1, a = .002, sweepTo) {
    const s = ctx.createBufferSource(); s.buffer = noiseBuf; s.loop = true;
    const f = ctx.createBiquadFilter(); f.type = type; f.frequency.setValueAtTime(freq, t); f.Q.value = q;
    if (sweepTo) f.frequency.exponentialRampToValueAtTime(sweepTo, t + dur);
    const g = ctx.createGain(); s.connect(f); f.connect(g); g.connect(dest);
    env(g, t, a, peak, dur); s.start(t, Math.random()); s.stop(t + dur + .05);
  }
  function tone(dest, t, type, f0, f1, dur, peak = .5, a = .003) {
    const o = ctx.createOscillator(); o.type = type; o.frequency.setValueAtTime(f0, t);
    if (f1 && f1 !== f0) o.frequency.exponentialRampToValueAtTime(f1, t + dur);
    const g = ctx.createGain(); o.connect(g); g.connect(dest); env(g, t, a, peak, dur); o.start(t); o.stop(t + dur + .05);
  }
  function playFile(key, bus, pan, vol, rate = 1) {
    const b = files[key]; if (!b) return false;
    const s = ctx.createBufferSource(); s.buffer = b; s.playbackRate.value = rate; s.connect(out(bus, pan, vol)); s.start(); return true;
  }
  // ---------- effets ----------
  const SHOTS = {
    pistol: d => { noise(d, now(), .015, 'highpass', 4500, .7, .9); noise(d, now(), .12, 'bandpass', 1800, .8, .9); tone(d, now(), 'sine', 180, 50, .1, .7); },
    uzi: d => { noise(d, now(), .06, 'bandpass', 2400, 1, .7); tone(d, now(), 'square', 140, 60, .05, .25); },
    shotgun: d => { noise(d, now(), .35, 'lowpass', 2600, .7, 1, .002, 300); tone(d, now(), 'sine', 120, 35, .25, .9); },
    rifle: d => { noise(d, now(), .02, 'highpass', 5000, .7, 1); noise(d, now(), .1, 'bandpass', 2900, 1.2, .9); noise(d, now(), .25, 'lowpass', 900, .5, .3); tone(d, now(), 'sine', 160, 45, .09, .6); },
    sniper: d => { noise(d, now(), .02, 'highpass', 6000, .7, 1.1); noise(d, now(), .5, 'lowpass', 3500, .6, 1, .001, 400); tone(d, now(), 'sine', 220, 30, .4, .9); },
    rocket: d => { noise(d, now(), .7, 'bandpass', 500, .8, .7, .02, 2600); tone(d, now(), 'sawtooth', 90, 200, .5, .2); },
    minigun: d => { noise(d, now(), .045, 'bandpass', 2600, 1, .55); },
    lmg: d => { noise(d, now(), .02, 'highpass', 4200, .7, 1); noise(d, now(), .14, 'bandpass', 2000, 1, .95); tone(d, now(), 'sine', 120, 40, .12, .8); },
    gl: d => { noise(d, now(), .18, 'lowpass', 900, .7, .9); tone(d, now(), 'sine', 90, 40, .2, 1); },
    rail: d => { tone(d, now(), 'sawtooth', 2400, 120, .35, .5); tone(d, now(), 'sine', 600, 60, .45, .7); noise(d, now(), .3, 'highpass', 3000, .7, .5); },
    enemy: d => { noise(d, now(), .12, 'bandpass', 1300, .8, .7); tone(d, now(), 'sine', 150, 50, .08, .4); },
  };
  let lastShot = 0;
  function shot(kind, pan = 0, vol = 1) {
    if (!ctx || !prefs.sfx) return;
    if (kind === 'minigun' || kind === 'uzi') { if (now() - lastShot < .04) return; }
    lastShot = now();
    if (playFile('shot_' + kind, sfxBus, pan, vol, rnd(.95, 1.05)) || playFile('shot', sfxBus, pan, vol, rnd(.95, 1.05))) return;
    (SHOTS[kind] || SHOTS.pistol)(out(sfxBus, pan, vol * rnd(.85, 1)));
  }
  function boom(pan = 0, vol = 1) {
    if (!ctx || !prefs.sfx) return;
    if (playFile('explosion', sfxBus, pan, vol)) return;
    const d = out(sfxBus, pan, vol);
    noise(d, now(), 1.4, 'lowpass', 2400, .7, 1.2, .005, 120);
    tone(d, now(), 'sine', 110, 28, 1.1, 1.1);
    noise(d, now() + .05, .9, 'bandpass', 700, .6, .4, .05, 200);
  }
  function crash(vol = 1, pan = 0) {
    if (!ctx || !prefs.sfx) return;
    if (playFile('crash', sfxBus, pan, vol)) return;
    const d = out(sfxBus, pan, Math.min(1, vol));
    noise(d, now(), .3, 'lowpass', 1800, .8, .9, .002, 200);
    [430, 710, 1150].forEach(f => tone(d, now(), 'triangle', f, f * .7, .35, .12));
  }
  function hit(pan = 0) { if (!ctx || !prefs.sfx) return; const d = out(sfxBus, pan, .6); noise(d, now(), .08, 'lowpass', 900, 1, .8); tone(d, now(), 'sine', 220, 90, .08, .5); }
  function hurt() { if (!ctx || !prefs.sfx) return; const d = out(sfxBus, 0, .6); tone(d, now(), 'sawtooth', 160, 70, .18, .35); noise(d, now(), .12, 'lowpass', 600, 1, .5); }
  function ko(pan = 0) { if (!ctx || !prefs.sfx) return; const d = out(sfxBus, pan, .45); tone(d, now(), 'square', 520, 140, .16, .25); }
  function blips(notes, type = 'square', step = .07, vol = .3, len = .09) {
    if (!ctx || !prefs.sfx) return; const d = out(sfxBus, 0, vol);
    notes.forEach((f, i) => tone(d, now() + i * step, type, f, f, len, .6));
  }
  const lock = () => blips([1400, 1400, 1900], 'square', .06, .25, .05);
  const alarm = () => { if (!ctx || !prefs.sfx) return; const d = out(sfxBus, 0, .5); for (let k = 0; k < 4; k++) tone(d, now() + k * .55, 'sawtooth', 620, 980, .5, .35); };
  const cash = () => { if (!playFile('cash', sfxBus, 0, .7)) blips([988, 1319], 'square', .06, .55, .1); };
  const pickup = () => blips([660, 880, 1175], 'triangle', .05, .6);
  const step = () => blips([523, 659, 784, 1047], 'triangle', .08, .6, .14);
  const win = () => { if (!playFile('win', sfxBus, 0, .8)) blips([523, 659, 784, 1047, 784, 1047, 1319], 'square', .11, .3, .2); };
  const fail = () => { if (!playFile('fail', sfxBus, 0, .8)) blips([392, 330, 262, 196], 'sawtooth', .16, .3, .25); };
  const buy = () => blips([784, 1175, 1568], 'square', .05, .25, .1);
  // sons d'interface doux (style menu de console) : survol = tic feutré, clic = « toc » grave et court
  const click = () => { if (!ctx || !prefs.sfx) return; const d = out(sfxBus, 0, .5); tone(d, now(), 'sine', 880, 520, .07, .5, .002); noise(d, now(), .03, 'bandpass', 2400, 2, .25); };
  const hover = () => { if (!ctx || !prefs.sfx) return; const d = out(sfxBus, 0, .18); tone(d, now(), 'sine', 1760, 1640, .035, .4, .002); };
  const deny = () => blips([220, 180], 'square', .08, .2, .09);
  function whoosh() { if (!ctx || !prefs.sfx) return; const d = out(sfxBus, 0, .7); noise(d, now(), 1, 'bandpass', 300, .7, .8, .3, 3000); }
  function door() { if (!ctx || !prefs.sfx) return; const d = out(sfxBus, 0, .5); noise(d, now(), .08, 'lowpass', 700, 1, .7); tone(d, now() + .06, 'sine', 140, 90, .08, .4); }

  // ---------- sons continus : moteur, crissement, sirène ----------
  let engine = null, screech = null, siren = null, rotor = null, rainL = null;
  function loops() {
    if (engine) return;
    const mk = (type, f) => { const o = ctx.createOscillator(); o.type = type; o.frequency.value = f; o.start(); return o; };
    const eg = ctx.createGain(); eg.gain.value = 0; const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 600;
    const o1 = mk('sawtooth', 50), o2 = mk('square', 25.5); const g2 = ctx.createGain(); g2.gain.value = .5;
    o1.connect(lp); o2.connect(g2); g2.connect(lp); lp.connect(eg); eg.connect(sfxBus);
    engine = { eg, lp, o1, o2 };
    const sg = ctx.createGain(); sg.gain.value = 0; const sn = ctx.createBufferSource(); sn.buffer = noiseBuf; sn.loop = true;
    const sf = ctx.createBiquadFilter(); sf.type = 'bandpass'; sf.frequency.value = 2200; sf.Q.value = 6; sn.connect(sf); sf.connect(sg); sg.connect(sfxBus); sn.start();
    screech = { sg };
    const rg = ctx.createGain(); rg.gain.value = 0; const ro = mk('sawtooth', 700); const rf = ctx.createBiquadFilter(); rf.type = 'lowpass'; rf.frequency.value = 1800;
    ro.connect(rf); rf.connect(rg); rg.connect(sfxBus);
    siren = { rg, ro, t: 0 };
    const hg = ctx.createGain(); hg.gain.value = 0; const hn = ctx.createBufferSource(); hn.buffer = noiseBuf; hn.loop = true;
    const hf = ctx.createBiquadFilter(); hf.type = 'lowpass'; hf.frequency.value = 320; const am = ctx.createGain(); am.gain.value = .5;
    const lfo = mk('square', 13); const lg = ctx.createGain(); lg.gain.value = .5; lfo.connect(lg); lg.connect(am.gain);
    hn.connect(hf); hf.connect(am); am.connect(hg); hg.connect(sfxBus); hn.start();
    rotor = { hg };
    const rg2 = ctx.createGain(); rg2.gain.value = 0; const rn = ctx.createBufferSource(); rn.buffer = noiseBuf; rn.loop = true; const rf2 = ctx.createBiquadFilter(); rf2.type = 'highpass'; rf2.frequency.value = 1200; rn.connect(rf2); rf2.connect(rg2); rg2.connect(sfxBus); rn.start();
    rainL = { rg2 };
  }
  function update(st, dt) {
    if (!ctx) return;
    loops();
    const t = now(), on = prefs.sfx && st.playing;
    const sp = Math.min(1, Math.abs(st.speed || 0) / 520);
    const ev = on && st.inCar ? .22 + sp * .2 : 0;
    engine.eg.gain.setTargetAtTime(ev, t, .08);
    engine.o1.frequency.setTargetAtTime(45 + sp * 140 + (st.nitro ? 40 : 0), t, .1);
    engine.o2.frequency.setTargetAtTime(22.5 + sp * 70, t, .1);
    engine.lp.frequency.setTargetAtTime(350 + sp * 1600, t, .1);
    screech.sg.gain.setTargetAtTime(on && st.inCar && st.drift && Math.abs(st.speed) > 160 ? .1 : 0, t, .05);
    siren.t += dt;
    const sv = on && st.sirenDist < 900 ? (1 - st.sirenDist / 900) * .16 : 0;
    siren.rg.gain.setTargetAtTime(sv, t, .2);
    rainL.rg2.gain.setTargetAtTime(on && st.rain ? .07 : 0, t, .5);
    rotor.hg.gain.setTargetAtTime(on && st.heliDist < 1200 ? (1 - st.heliDist / 1200) * .5 : 0, t, .2);
    siren.ro.frequency.setTargetAtTime(750 + 420 * (.5 + .5 * Math.sin(siren.t * 2.6)), t, .05);
  }

  // ---------- musique (générée, originale) ----------
  const N2F = n => 440 * Math.pow(2, (n - 69) / 12);
  // chaque style : tempo, accords (notes MIDI de la basse), gamme pour la mélodie, motif de batterie (16 pas)
  // ---- styles modernes (trap 808, lo-fi, dembow) : générés, originaux
  function kickAt(t, f0 = 150, f1 = 45, dur = .16, pk = 1) { const g = ctx.createGain(); g.connect(musBus); const o = ctx.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f1, t + dur * .7); o.connect(g); env(g, t, .002, pk, dur); o.start(t); o.stop(t + dur + .05); }
  function b808(t, note, dur, pk = .85) {
    const g = ctx.createGain(); g.connect(musBus); const f = N2F(note);
    const o = ctx.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(f * 1.5, t); o.frequency.exponentialRampToValueAtTime(f, t + .05);
    const o2 = ctx.createOscillator(); o2.type = 'triangle'; o2.frequency.setValueAtTime(f * 2, t); const g2 = ctx.createGain(); g2.gain.value = .25; o2.connect(g2); g2.connect(g);
    o.connect(g); env(g, t, .004, pk, dur); o.start(t); o2.start(t); o.stop(t + dur + .1); o2.stop(t + dur + .1);
  }
  function clap(t, pk = .55) { for (let k = 0; k < 3; k++) noise(musBus, t + k * .011, .09 + k * .03, 'bandpass', 1400, .9, pk * (k === 2 ? 1 : .6)); }
  function hat(t, pk = .14, open) { noise(musBus, t, open ? .18 : .03, 'highpass', 8500, .7, pk); }
  function keys(t, notes, dur, pk = .06, type = 'triangle', cut = 1800) {
    for (const n of notes) { const o = ctx.createOscillator(); o.type = type; o.frequency.value = N2F(n); const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = cut; const g = ctx.createGain(); o.connect(f); f.connect(g); g.connect(musBus); env(g, t, .01, pk, dur); o.start(t); o.stop(t + dur + .1); }
  }
  function trapStep(i, p, t, spb, root, hot) {
    const bar = Math.floor(i / 16) % 4;
    if ([0, 7, 10].includes(p) || (bar % 2 && p === 14)) { kickAt(t, 160, 48, .12, .9); b808(t, root - 24 + (p === 10 ? 3 : p === 14 ? 7 : 0), spb * (p === 0 ? 6 : 3)); }
    if (p === 8) clap(t, .6); if (hot && p === 15) clap(t, .3);
    if (p % 2 === 0) hat(t, .12); if (p === 6 || p === 14) hat(t, .08, true);
    if ((bar === 1 || bar === 3) && p >= 12) { hat(t, .1); hat(t + spb / 2, .09); if (p === 15) hat(t + spb / 4, .08), hat(t + spb * .75, .08); }
    if (p === 0) keys(t, [root + 12, root + 15, root + 19].map(n => n), spb * 15, .035, 'sawtooth', 900);
    const mel = [0, 3, 7, 10, 12, 10, 7, 3];
    if (p % 4 === 2) keys(t, [root + 24 + mel[(i / 4 | 0) % 8]], spb * 1.5, .07, 'triangle', 4000);
  }
  function lofiStep(i, p, t, spb, root) {
    const sw = p % 2 ? spb * .18 : 0, tt = t + sw;
    if (p === 0 || p === 10) kickAt(tt, 110, 45, .18, .7);
    if (p === 4 || p === 12) { noise(musBus, tt, .12, 'bandpass', 1800, .6, .25); tone(musBus, tt, 'triangle', 200, 170, .06, .08); }
    if (p % 2 === 0) hat(tt, .05);
    if (p === 0 || p === 8) { keys(tt, [root, root + 4, root + 7, root + 11].map(n => n + 12), spb * 7.5, .045, 'sine', 1400); keys(tt + .02, [root + 12, root + 16], spb * 7, .02, 'triangle', 1100); }
    if (p === 0 || p === 8) b808(tt, root - 12, spb * 6, .35);
    if (Math.random() < .35) noise(musBus, t + Math.random() * spb, .01, 'highpass', 3000, 1, .03);
    if (p === 6 || p === 14) keys(tt, [root + 24 + [7, 9, 4, 2][(i / 8 | 0) % 4]], spb * 2, .03, 'sine', 3000);
  }
  function dembowStep(i, p, t, spb, root, hot) {
    if (p % 4 === 0) kickAt(t, 140, 50, .14, .85);
    if ([3, 6, 11, 14].includes(p)) { noise(musBus, t, .07, 'bandpass', 2400, 1.2, .4); tone(musBus, t, 'square', 380, 300, .03, .06); }
    if (p % 2 === 0 || hot) hat(t, .08);
    if ([0, 3, 8, 11].includes(p)) b808(t, root - 12, spb * 2.5, .55);
    if (p === 0) keys(t, [root + 12, root + 15, root + 19], spb * 15, .03, 'sawtooth', 1100);
    if (p % 2 === 1) keys(t, [root + 24 + [0, 3, 5, 7, 10, 7, 5, 3][(i / 2 | 0) % 8]], spb * .9, .05, 'square', 2600);
  }
  const STYLES = {
    trap: { bpm: 142, chords: [45, 41, 48, 43], minor: true, custom: trapStep },
    lofi: { bpm: 78, chords: [50, 43, 48, 53], minor: false, custom: lofiStep },
    dembow: { bpm: 95, chords: [45, 41, 43, 40], minor: true, custom: dembowStep },
    synth: null,
    menu: { bpm: 84, chords: [45, 41, 48, 43], minor: true, kick: 'x...............', snare: '................', hat: '..x...x...x...x.', lead: 'pad', arp: '0 - - - 7 - - - 12 - - - 7 - - -' },
    usa: { bpm: 100, chords: [45, 41, 48, 43], minor: true, kick: 'x...x...x...x...', snare: '....x.......x...', hat: 'x.x.x.x.x.x.x.x.', lead: 'synth', arp: '0 - 4 - 7 - 4 - 0 - 4 - 7 - 9 -' },
    ita: { bpm: 92, chords: [50, 46, 41, 45], minor: true, kick: 'x.....x.x.......', snare: '....x.......x..x', hat: '..x...x...x...x.', lead: 'pluck', arp: '0 - 2 - 4 - 5 - 7 - 5 - 4 - 2 -' },
    col: { bpm: 96, chords: [43, 48, 50, 43], minor: false, kick: 'x...x...x...x...', snare: '..x...x...x...x.', hat: 'xx.xxx.xxx.xxx.x', lead: 'marimba', arp: '0 4 7 - 12 - 7 4 0 - 4 7 - 4 - -' },
    bra: { bpm: 128, chords: [40, 40, 43, 38], minor: true, kick: 'x..x..x...x..x..', snare: '....x..x....x...', hat: 'x.xxx.xxx.xxx.xx', lead: 'synth', arp: '0 - - 4 - - 7 - - 10 - - 7 - 4 -' },
  };
  STYLES.moon = { bpm: 70, chords: [45, 48, 43, 40], minor: true, kick: 'x...............', snare: '................', hat: '....x.......x...', lead: 'pad', arp: '0 - - - 7 - - - 12 - - - 5 - - -' }; STYLES.mars = { bpm: 84, chords: [40, 43, 38, 41], minor: true, kick: 'x.......x.......', snare: '........x.......', hat: '..x...x...x...x.', lead: 'pad', arp: '0 - 3 - 7 - 3 - 0 - 5 - 7 - 10 -' };
  STYLES.synth = STYLES.usa; STYLES.funk = STYLES.bra; STYLES.usa = STYLES.trap; STYLES.menu = STYLES.lofi;
  let mus = { style: null, timer: null, step: 0, next: 0, intensity: 0 };
  function setMusic(style) {
    if (!ctx) return;
    if (mus.style === style) return;
    mus.style = style; mus.step = 0; mus.next = now() + .1;
    if (mus.fileSrc) { try { mus.fileSrc.stop(); } catch (e) {} mus.fileSrc = null; }
    if (!style) return;
    const fb = files['music_' + style];
    if (fb) { const s = ctx.createBufferSource(); s.buffer = fb; s.loop = true; s.connect(musBus); s.start(); mus.fileSrc = s; return; }
    if (!mus.timer) mus.timer = setInterval(schedule, 25);
  }
  function setIntensity(v) { mus.intensity = v; }
  function schedule() {
    if (!ctx || !mus.style || mus.fileSrc) return;
    const s = STYLES[mus.style]; if (!s) return; const spb = 60 / s.bpm / 4; // durée d'un 16e
    while (mus.next < now() + .12) { playStep(s, mus.step, mus.next, spb); mus.step++; mus.next += spb; }
  }
  function playStep(s, i, t, spb) {
    if (s.custom) { s.custom(i, i % 16, t, spb, s.chords[Math.floor(i / 16) % s.chords.length], mus.intensity > 0); return; }
    const p = i % 16, bar = Math.floor(i / 16) % s.chords.length, root = s.chords[bar];
    const third = s.minor ? 3 : 4;
    const hot = mus.intensity > 0;
    if (s.kick[p] === 'x' || (hot && p % 4 === 0)) { const g = ctx.createGain(); g.connect(musBus); const o = ctx.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(140, t); o.frequency.exponentialRampToValueAtTime(42, t + .14); o.connect(g); env(g, t, .002, 1, .22); o.start(t); o.stop(t + .3); }
    if (s.snare[p] === 'x') { noise(musBus, t, .14, 'bandpass', 1900, .7, .55); tone(musBus, t, 'triangle', 220, 160, .07, .2); }
    if (s.hat[p] === 'x' || (hot && p % 2 === 1)) noise(musBus, t, .035, 'highpass', 8000, .7, hot ? .22 : .16);
    // basse
    if (p % 4 === 0 || (mus.style === 'bra' && p % 4 === 3)) {
      const o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = N2F(root - 12 + (p === 12 && s.minor ? 7 : 0));
      const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.setValueAtTime(900, t); f.frequency.exponentialRampToValueAtTime(180, t + spb * 3);
      const g = ctx.createGain(); o.connect(f); f.connect(g); g.connect(musBus); env(g, t, .005, .32, spb * 3.2); o.start(t); o.stop(t + spb * 4);
    }
    // nappe sur chaque mesure
    if (p === 0) {
      [0, third, 7, 12].forEach((iv, k) => {
        const o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = N2F(root + 12 + iv); o.detune.value = (k - 1.5) * 7;
        const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = mus.style === 'menu' ? 900 : 1300;
        const g = ctx.createGain(); o.connect(f); f.connect(g); g.connect(musBus);
        const len = spb * 16; g.gain.setValueAtTime(.0001, t); g.gain.linearRampToValueAtTime(.045, t + len * .25); g.gain.linearRampToValueAtTime(.0001, t + len);
        o.start(t); o.stop(t + len + .05);
      });
    }
    // arpège / mélodie
    const tok = s.arp.split(' ')[p], has = tok && tok !== '-';
    if (has && s.lead !== 'pad') {
      const n = root + 24 + (+tok === 3 || +tok === 4 ? third : +tok);
      const type = s.lead === 'marimba' ? 'sine' : s.lead === 'pluck' ? 'triangle' : 'square';
      const o = ctx.createOscillator(); o.type = type; o.frequency.value = N2F(n);
      const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = s.lead === 'synth' ? 2200 : 3200;
      const g = ctx.createGain(); o.connect(f); f.connect(g); g.connect(musBus);
      env(g, t, .003, s.lead === 'synth' ? .08 : .12, s.lead === 'marimba' ? .25 : spb * 1.8); o.start(t); o.stop(t + .4);
      if (s.lead === 'pluck' && p % 4 === 0) { const o2 = ctx.createOscillator(); o2.type = 'triangle'; o2.frequency.value = N2F(n + 12); const g2 = ctx.createGain(); o2.connect(g2); g2.connect(musBus); env(g2, t + spb / 2, .002, .05, .12); o2.start(t + spb / 2); o2.stop(t + .4); }
    }
    if (s.lead === 'pad' && has) {
      const o = ctx.createOscillator(); o.type = 'sine'; o.frequency.value = N2F(root + 24 + (+tok === 4 ? third : +tok));
      const g = ctx.createGain(); o.connect(g); g.connect(musBus); env(g, t, .01, .05, .5); o.start(t); o.stop(t + .6);
    }
  }
  function duck(on) { if (!ctx) return; musBus.gain.setTargetAtTime(prefs.music ? (on ? .15 : .42) : 0, now(), .2); }
  function toggle(kind) {
    prefs[kind] = !prefs[kind]; savePrefs();
    if (ctx) { if (kind === 'sfx') sfxBus.gain.setTargetAtTime(prefs.sfx ? .8 : 0, now(), .05); else musBus.gain.setTargetAtTime(prefs.music ? .42 : 0, now(), .1); }
    return prefs[kind];
  }
  // Rendu hors ligne (bande-annonce) : musique d'un style + bruitages placés dans le temps -> WAV
  async function renderOffline(style, seconds, events = []) {
    const saved = { ctx, master, sfxBus, musBus, comp, noiseBuf, sfx: prefs.sfx, music: prefs.music };
    const OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext;
    const oc = new OAC(2, Math.ceil(44100 * seconds), 44100);
    ctx = oc; prefs.sfx = prefs.music = true;
    comp = ctx.createDynamicsCompressor(); comp.threshold.value = -14; comp.ratio.value = 4; comp.connect(ctx.destination);
    master = ctx.createGain(); master.gain.value = .9; master.connect(comp);
    sfxBus = ctx.createGain(); sfxBus.gain.value = .8; sfxBus.connect(master);
    musBus = ctx.createGain(); musBus.gain.value = .5; musBus.connect(master);
    noiseBuf = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate); const nd = noiseBuf.getChannelData(0); for (let i = 0; i < nd.length; i++) nd[i] = Math.random() * 2 - 1;
    const st = STYLES[style] || STYLES.usa, spb = 60 / st.bpm / 4, prevI = mus.intensity;
    for (let i = 0, t = 0; t < seconds; i++, t += spb) { mus.intensity = events.some(e => e.hot && t >= e.t && t < e.t + e.d) ? 1 : 0; playStep(st, i, t, spb); }
    mus.intensity = prevI;
    for (const e of events) { if (!e.fn) continue; tOff = e.t; try { api[e.fn](...(e.args || [])); } catch (err) {} }
    tOff = 0;
    const buf = await oc.startRendering();
    ({ ctx, master, sfxBus, musBus, comp, noiseBuf } = saved); prefs.sfx = saved.sfx; prefs.music = saved.music;
    // encodage WAV 16 bits
    const n = buf.length, ch = 2, out = new DataView(new ArrayBuffer(44 + n * ch * 2));
    const ws = (o, str) => { for (let i = 0; i < str.length; i++) out.setUint8(o + i, str.charCodeAt(i)); };
    ws(0, 'RIFF'); out.setUint32(4, 36 + n * ch * 2, true); ws(8, 'WAVEfmt '); out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, ch, true);
    out.setUint32(24, 44100, true); out.setUint32(28, 44100 * ch * 2, true); out.setUint16(32, ch * 2, true); out.setUint16(34, 16, true); ws(36, 'data'); out.setUint32(40, n * ch * 2, true);
    const L = buf.getChannelData(0), Rr = buf.getChannelData(1);
    for (let i = 0, o = 44; i < n; i++) { for (const v of [L[i], Rr[i]]) { out.setInt16(o, Math.max(-1, Math.min(1, v)) * 32767, true); o += 2; } }
    return out.buffer;
  }
  function setMute(m) { if (ctx) master.gain.setTargetAtTime(m ? 0 : .9, now(), .05); }
  const api = { lock, alarm, renderOffline, setMute, init, shot, boom, crash, hit, hurt, ko, cash, pickup, step, win, fail, buy, click, hover, deny, whoosh, door, update, setMusic, setIntensity, duck, toggle, prefs, get ready() { return !!ctx; } };
  return api;
})();
