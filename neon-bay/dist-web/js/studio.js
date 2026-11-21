// Néon Studio : éditeur 3D d'animations et de cinématiques (three.js r128).
// Scène -> objets avec images clés -> caméra cinéma -> export vidéo (navigateur) ou rendu cloud (tools/studio/render.js).
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const PI = Math.PI, TAU = PI * 2;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, u) => a + (b - a) * u;
  const fmtT = t => { const m = Math.floor(t / 60), s = t - m * 60; return String(m).padStart(2, '0') + ':' + s.toFixed(2).padStart(5, '0'); };
  const uid = () => Math.random().toString(36).slice(2, 9);
  const rng = seed => { let s = seed >>> 0 || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; };

  // ---------- bibliothèque ----------
  const ASSETS = {
    human_m: { cat: 'Chars', name: 'Homme', desc: 'animé', file: 'human_m', kind: 'human', slots: ['Skin', 'Shirt', 'Pants', 'Shoes', 'Hair'], h: 1.8 },
    human_f: { cat: 'Chars', name: 'Femme', desc: 'animée', file: 'human_f', kind: 'human', slots: ['Skin', 'Shirt', 'Pants', 'Shoes', 'Hair'], h: 1.71 },
    robot: { cat: 'Chars', name: 'Robot', desc: 'animé', file: 'robot', kind: 'human', slots: [], h: 1.8 },
    car_sedan: { cat: 'Cars', name: 'Berline', desc: '4,45 m', file: 'car_sedan', kind: 'car', slots: ['Paint'] },
    car_sports: { cat: 'Cars', name: 'Sportive', desc: 'cabriolet', file: 'car_sports', kind: 'car', slots: ['Paint'] },
    car_suv: { cat: 'Cars', name: 'SUV', desc: '4,65 m', file: 'car_suv', kind: 'car', slots: ['Paint'] },
    car_van: { cat: 'Cars', name: 'Fourgon', desc: '4,85 m', file: 'car_van', kind: 'car', slots: ['Paint'] },
    police: { cat: 'Cars', name: 'Police', desc: 'gyrophare', file: 'car_sedan', kind: 'car', slots: ['Paint'], police: true },
    street: { cat: 'Props', name: 'Rue néon', desc: 'immeubles', kind: 'street' },
    rocket: { cat: 'Props', name: 'Fusée', desc: 'flammes', kind: 'rocket', slots: ['Color'] },
    boat: { cat: 'Cars', name: 'Bateau', desc: 'vedette', kind: 'boat', slots: ['Paint'] },
    palm: { cat: 'Props', name: 'Palmier', desc: '7 m', file: 'palm', kind: 'prop', h: 7 },
    lamp: { cat: 'Props', name: 'Lampadaire', desc: 'éclaire', file: 'lamp', kind: 'prop', h: 5.5, light: true },
    traffic_light: { cat: 'Props', name: 'Feu', desc: 'tricolore', file: 'traffic_light', kind: 'prop', h: 4.2 },
    bench: { cat: 'Props', name: 'Banc', desc: 'bois', file: 'bench', kind: 'prop', h: .9 },
    hydrant: { cat: 'Props', name: 'Borne', desc: 'incendie', file: 'hydrant', kind: 'prop', h: .85 },
    cube: { cat: 'Prims', name: 'Cube', desc: '1 m', kind: 'prim', slots: ['Color'] },
    sphere: { cat: 'Prims', name: 'Sphère', desc: '1 m', kind: 'prim', slots: ['Color'] },
    cylinder: { cat: 'Prims', name: 'Cylindre', desc: '1 m', kind: 'prim', slots: ['Color'] },
    neon: { cat: 'Prims', name: 'Enseigne', desc: 'néon', kind: 'prim', slots: ['Color'] },
    light: { cat: 'Prims', name: 'Lumière', desc: 'ponctuelle', kind: 'light', slots: ['Color'] },
  };
  const DEFCOL = { Skin: '#c68b59', Shirt: '#21e6ff', Pants: '#1d1a2e', Shoes: '#f2f2f2', Hair: '#1a120c', Paint: '#ff2e93', Color: '#8a7dff' };
  const CLIPS = ['Idle', 'Walk', 'Run', 'Punch', 'Death'];

  // ---------- état ----------
  let P = null; // projet
  const rt = {}; // objets 3D par id
  let sel = null, t = 0, playing = false, camView = false, recording = false;
  const models = {}, loading = {};

  // ---------- rendu ----------
  const cv = $('cv'), view = $('view');
  const R = new THREE.WebGLRenderer({ canvas: cv, antialias: true, preserveDrawingBuffer: true });
  const lowEnd = matchMedia('(max-width: 860px)').matches;
  R.setPixelRatio(Math.min(devicePixelRatio || 1, lowEnd ? 1.5 : 2));
  R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 1;
  R.shadowMap.enabled = true; R.shadowMap.type = THREE.PCFSoftShadowMap;
  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(R);
  const envTex = pmrem.fromScene(new THREE.RoomEnvironment(), .04).texture;
  scene.environment = envTex;
  const edCam = new THREE.PerspectiveCamera(50, 1, .1, 4000); edCam.position.set(14, 9, 18);
  const orbit = new THREE.OrbitControls(edCam, cv); orbit.target.set(0, 1, 0); orbit.enableDamping = true; orbit.update();
  const gizmo = new THREE.TransformControls(edCam, cv); gizmo.setSize(lowEnd ? 1.2 : .9); scene.add(gizmo);
  gizmo.addEventListener('dragging-changed', e => { orbit.enabled = !e.value; if (!e.value) commitTransform(); });
  const hemi = new THREE.HemisphereLight(0xbfd4ff, 0x2a2233, .6); scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xffffff, 1); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -60, right: 60, top: 60, bottom: -60, near: 1, far: 400 }); scene.add(sun, sun.target);
  const sky = new THREE.Sky(); sky.scale.setScalar(3500); scene.add(sky);
  const stars = (() => { const g = new THREE.BufferGeometry(), a = new Float32Array(1500 * 3), r = rng(5); for (let i = 0; i < 1500; i++) { const th = r() * TAU, ph = r() * .45 * PI; a[i * 3] = Math.cos(th) * Math.sin(ph) * 1500; a[i * 3 + 1] = Math.cos(ph) * 1500; a[i * 3 + 2] = Math.sin(th) * Math.sin(ph) * 1500; } g.setAttribute('position', new THREE.BufferAttribute(a, 3)); return new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 2, sizeAttenuation: false, fog: false })); })();
  scene.add(stars);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200), new THREE.MeshStandardMaterial({ color: 0x1a1822, roughness: .95 })); ground.rotation.x = -PI / 2; ground.receiveShadow = true; scene.add(ground);
  const grid = new THREE.GridHelper(200, 100, 0x3b3658, 0x24213a); grid.position.y = .01; scene.add(grid);
  let mirror = null;
  // pluie
  const rain = (() => { const n = 2500, g = new THREE.BufferGeometry(), a = new Float32Array(n * 6), r = rng(9); for (let i = 0; i < n; i++) { const x = (r() - .5) * 80, y = r() * 40, z = (r() - .5) * 80; a.set([x, y, z, x + .05, y - .9, z], i * 6); } g.setAttribute('position', new THREE.BufferAttribute(a, 3)); const m = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x9fb6d8, transparent: true, opacity: .35 })); m.frustumCulled = false; return m; })();
  scene.add(rain);
  // caméra cinéma (réelle) et son repère dans l'éditeur
  const cinCam = new THREE.PerspectiveCamera(40, 16 / 9, .1, 4000);
  // post-traitement : halo néon + passage en sRGB + vignette et grain de film
  const FINAL = { uniforms: { tDiffuse: { value: null }, time: { value: 0 }, vig: { value: .35 }, grain: { value: .045 } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: 'uniform sampler2D tDiffuse; uniform float time, vig, grain; varying vec2 vUv; float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233)) + time) * 43758.5453); } void main(){ vec2 d = vUv - .5; float ca = .0012; vec3 c; c.r = texture2D(tDiffuse, vUv + d * ca).r; c.g = texture2D(tDiffuse, vUv).g; c.b = texture2D(tDiffuse, vUv - d * ca).b; c = LinearTosRGB(vec4(c, 1.)).rgb; c *= 1. - vig * dot(d, d) * 2.2; c += (h(vUv * 900.) - .5) * grain; gl_FragColor = vec4(c, 1.); }' };
  let composer = null, bloomPass = null, finalPass = null;
  function setupComposer(cam) {
    composer = new THREE.EffectComposer(R); composer.addPass(new THREE.RenderPass(scene, cam));
    bloomPass = new THREE.UnrealBloomPass(new THREE.Vector2(256, 256), .8, .5, .82); composer.addPass(bloomPass);
    finalPass = new THREE.ShaderPass(FINAL); composer.addPass(finalPass);
  }
  setupComposer(edCam);

  // ---------- chargement des modèles (.glb.js en base64, servi à côté de la page) ----------
  function loadModel(file) {
    if (models[file]) return Promise.resolve(models[file]);
    if (loading[file]) return loading[file];
    return loading[file] = new Promise(res => {
      const s = document.createElement('script'); s.src = 'models/' + file + '.glb.js';
      s.onload = () => { try { const b64 = (window.NB_MODEL_DATA || {})[file], bin = atob(b64), buf = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
        new THREE.GLTFLoader().parse(buf.buffer, '', gl => { gl.scene.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } }); const box = new THREE.Box3().setFromObject(gl.scene); models[file] = { scene: gl.scene, anims: gl.animations, size: box.getSize(new THREE.Vector3()) }; res(models[file]); }, () => res(null)); } catch (e) { res(null); } };
      s.onerror = () => res(null); document.head.appendChild(s);
    });
  }
  const needFiles = objs => [...new Set(objs.map(o => ASSETS[o.asset] && ASSETS[o.asset].file).filter(Boolean))];

  // ---------- construction des objets ----------
  function tint(root, colors) {
    root.traverse(o => { if (!o.isMesh || !o.material) return; const mats = Array.isArray(o.material) ? o.material : [o.material];
      o.material = mats.map(m => { const c = m.clone(); const want = colors[m.name] || (colors.Color && !m.name ? colors.Color : null); if (want && c.color) c.color.set(want); if (/paint/i.test(m.name)) { c.metalness = .55; c.roughness = .28; } if (/glass/i.test(m.name)) { c.metalness = .2; c.roughness = .05; } c.envMapIntensity = 1; return c; });
      if (o.material.length === 1) o.material = o.material[0]; });
  }
  function streetGroup(o) {
    const g = new THREE.Group(), r = rng(o.seed || 7), L = o.length || 200;
    const asphalt = new THREE.MeshStandardMaterial({ color: 0x23212b, roughness: .85, transparent: true, opacity: .93 });
    const road = new THREE.Mesh(new THREE.PlaneGeometry(L, 14), asphalt); road.rotation.x = -PI / 2; road.position.y = .02; road.receiveShadow = true; g.add(road);
    const lineM = new THREE.MeshBasicMaterial({ color: 0xffd23f });
    for (let x = -L / 2 + 2; x < L / 2; x += 6) { const d = new THREE.Mesh(new THREE.PlaneGeometry(3, .18), lineM); d.rotation.x = -PI / 2; d.position.set(x, .03, 0); g.add(d); }
    const walkM = new THREE.MeshStandardMaterial({ color: 0x55505f, roughness: .9 });
    for (const sz of [-1, 1]) { const w = new THREE.Mesh(new THREE.BoxGeometry(L, .18, 5), walkM); w.position.set(0, .09, sz * 9.5); w.receiveShadow = true; g.add(w); }
    // immeubles avec fenêtres allumées et enseignes
    const winTex = (() => { const c = document.createElement('canvas'); c.width = 64; c.height = 128; const x = c.getContext('2d'); x.fillStyle = '#000'; x.fillRect(0, 0, 64, 128); for (let yy = 4; yy < 128; yy += 10) for (let xx = 4; xx < 64; xx += 10) { const v = r(); x.fillStyle = v < .45 ? '#ffd98a' : v < .55 ? '#8fd8ff' : '#06060a'; x.fillRect(xx, yy, 6, 6); } const tx = new THREE.CanvasTexture(c); tx.wrapS = tx.wrapT = THREE.RepeatWrapping; tx.encoding = THREE.sRGBEncoding; return tx; })();
    const neonCols = [0xff2e93, 0x21e6ff, 0xa6ff4d, 0xffb627, 0x9d7bff];
    for (const sz of [-1, 1]) for (let x = -L / 2 + 6; x < L / 2 - 4;) {
      const w = 8 + r() * 10, d = 10 + r() * 6, h = 8 + r() * 34, col = new THREE.Color().setHSL(.68 + r() * .15, .18 + r() * .2, .16 + r() * .14);
      const tx = winTex.clone(); tx.needsUpdate = true; tx.repeat.set(w / 6, h / 10);
      const m = new THREE.MeshStandardMaterial({ color: col, roughness: .8, emissive: 0xffffff, emissiveMap: tx, emissiveIntensity: .9 });
      const roofM = new THREE.MeshStandardMaterial({ color: col.clone().multiplyScalar(.7), roughness: .9 });
      const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), [m, m, roofM, roofM, m, m]); b.position.set(x + w / 2, h / 2, sz * (12 + d / 2)); b.castShadow = true; b.receiveShadow = true; g.add(b);
      if (r() < .55) { const nc = neonCols[Math.floor(r() * neonCols.length)], s = new THREE.Mesh(new THREE.BoxGeometry(Math.min(w * .7, 6), .7, .15), new THREE.MeshBasicMaterial({ color: nc })); s.position.set(x + w / 2, 4 + r() * 5, sz * (12 - .1)); g.add(s); }
      x += w + .6 + r() * 2;
    }
    // lampadaires simples (lumineux)
    const poleM = new THREE.MeshStandardMaterial({ color: 0x2a2830, metalness: .6, roughness: .4 }), bulbM = new THREE.MeshBasicMaterial({ color: 0xfff1c8 });
    for (let x = -L / 2 + 10; x < L / 2; x += 22) for (const sz of [-1, 1]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(.08, .12, 6, 8), poleM); p.position.set(x, 3, sz * 7.6); g.add(p); const bl = new THREE.Mesh(new THREE.SphereGeometry(.22, 10, 8), bulbM); bl.position.set(x, 6.05, sz * 7.1); g.add(bl); g.userData.bulbs = (g.userData.bulbs || []).concat([bl]); }
    g.userData.street = true; return g;
  }
  function build(o) {
    const a = ASSETS[o.asset] || {}, holder = new THREE.Group(); holder.userData.oid = o.id; let inner = null; const u = { holder, wheels: [], mixer: null, action: null };
    if (o.asset === 'camera') {
      inner = new THREE.Group(); const body = new THREE.Mesh(new THREE.BoxGeometry(.5, .35, .7), new THREE.MeshBasicMaterial({ color: 0xff2e93, wireframe: true })); const lens = new THREE.Mesh(new THREE.ConeGeometry(.3, .5, 4, 1, true), new THREE.MeshBasicMaterial({ color: 0xff2e93, wireframe: true })); lens.rotation.x = PI / 2; lens.position.z = -.55; inner.add(body, lens); u.helper = true;
    } else if (a.kind === 'street') inner = streetGroup(o);
    else if (a.kind === 'rocket') { // fusée 33 m : corps, coiffe, ailerons, flamme animée (visible quand la fusée monte)
      inner = new THREE.Group(); const W = new THREE.MeshStandardMaterial({ color: 0xf4f4f4, roughness: .35, metalness: .3 }), Rd = new THREE.MeshStandardMaterial({ color: (o.color || {}).Color || '#d6332a', roughness: .4 });
      const body = new THREE.Mesh(new THREE.CylinderGeometry(1.8, 1.8, 24, 24), W); body.position.y = 14; const nose = new THREE.Mesh(new THREE.ConeGeometry(1.8, 6, 24), Rd); nose.position.y = 29;
      inner.add(body, nose); for (let i = 0; i < 4; i++) { const f = new THREE.Mesh(new THREE.BoxGeometry(.25, 4, 2.4), Rd); f.position.set(Math.cos(i * PI / 2) * 2.3, 3.5, Math.sin(i * PI / 2) * 2.3); f.rotation.y = -i * PI / 2; inner.add(f); }
      const noz = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.9, 2, 18), new THREE.MeshStandardMaterial({ color: 0x1a1a22, metalness: .7, roughness: .3 })); noz.position.y = 1; inner.add(noz);
      inner.traverse(x => { if (x.isMesh) { x.castShadow = true; } });
      const fl = new THREE.Group(); const f1 = new THREE.Mesh(new THREE.ConeGeometry(1.5, 9, 16), new THREE.MeshBasicMaterial({ color: 0xffa21a, transparent: true, opacity: .9 })); f1.rotation.x = PI; f1.position.y = -4.5; const f2 = new THREE.Mesh(new THREE.ConeGeometry(.8, 5, 12), new THREE.MeshBasicMaterial({ color: 0xfff4c0 })); f2.rotation.x = PI; f2.position.y = -2.5; fl.add(f1, f2); inner.add(fl);
      const fL = new THREE.PointLight(0xffa040, 0, 120, 2); fL.position.y = -3; inner.add(fL); u.flame = fl; u.flameL = fL;
      const smoke = new THREE.Group(); for (let i = 0; i < 14; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(1, 10, 8), new THREE.MeshStandardMaterial({ color: 0xd8d4dc, roughness: 1, transparent: true, opacity: .8 })); smoke.add(m); } u.smoke = smoke; u.smokeRoot = true;
    }
    else if (a.kind === 'boat') { inner = new THREE.Group(); const pm = new THREE.MeshStandardMaterial({ color: (o.color || {}).Paint || '#ffffff', roughness: .3, metalness: .2 });
      const hull = new THREE.Mesh(new THREE.BoxGeometry(6, 1.2, 2.4), pm); hull.position.y = .5; const bow = new THREE.Mesh(new THREE.CylinderGeometry(0, 1.2, 2, 4), pm); bow.rotation.z = -PI / 2; bow.rotation.x = PI / 4; bow.scale.set(1, 1, .9); bow.position.set(4, .5, 0);
      const cab = new THREE.Mesh(new THREE.BoxGeometry(2, 1.1, 1.8), new THREE.MeshStandardMaterial({ color: 0xf4f4f4 })); cab.position.set(-.6, 1.6, 0); const ws = new THREE.Mesh(new THREE.BoxGeometry(.1, .7, 1.6), new THREE.MeshStandardMaterial({ color: 0x9fd6ff, metalness: .3, roughness: .05 })); ws.position.set(.45, 1.7, 0);
      inner.add(hull, bow, cab, ws); inner.traverse(x => { if (x.isMesh) x.castShadow = true; }); u.boat = true; }
    else if (a.kind === 'prim') {
      const geo = { cube: new THREE.BoxGeometry(1, 1, 1), sphere: new THREE.SphereGeometry(.5, 32, 20), cylinder: new THREE.CylinderGeometry(.5, .5, 1, 28), neon: new THREE.BoxGeometry(3, .5, .12) }[o.asset];
      const col = (o.color || {}).Color || DEFCOL.Color; inner = new THREE.Mesh(geo, o.asset === 'neon' ? new THREE.MeshBasicMaterial({ color: col }) : new THREE.MeshStandardMaterial({ color: col, roughness: .5 })); inner.castShadow = inner.receiveShadow = true; if (o.asset !== 'neon') inner.position.y = .5;
    } else if (a.kind === 'light') {
      inner = new THREE.Group(); const L = new THREE.PointLight((o.color || {}).Color || '#ff2e93', o.intensity || 3, 30, 2); L.position.y = 1; const b = new THREE.Mesh(new THREE.SphereGeometry(.15, 10, 8), new THREE.MeshBasicMaterial({ color: (o.color || {}).Color || '#ff2e93' })); b.position.y = 1; inner.add(L, b); u.light = L;
    } else if (a.file && models[a.file]) {
      const md = models[a.file];
      inner = a.kind === 'human' ? THREE.SkeletonUtils.clone(md.scene) : md.scene.clone(true);
      const cols = Object.assign({}, ...((a.slots || []).map(s => ({ [s]: DEFCOL[s] }))), a.police ? { Paint: '#eef0ff' } : {}, o.color || {});
      tint(inner, cols);
      if (a.h) inner.scale.setScalar(a.h / (md.size.y || 1));
      if (a.kind === 'human') { inner.traverse(x => { if (x.isMesh) x.frustumCulled = false; }); u.mixer = new THREE.AnimationMixer(inner); u.anims = md.anims; }
      if (a.kind === 'car') { inner.traverse(x => { if (/^Wheel/i.test(x.name)) u.wheels.push(x); });
        if (a.police) { const bar = new THREE.Group(); const red = new THREE.Mesh(new THREE.BoxGeometry(.3, .14, .5), new THREE.MeshBasicMaterial({ color: 0xff2e4d })), blue = red.clone(); blue.material = new THREE.MeshBasicMaterial({ color: 0x2e6bff }); red.position.z = -.3; blue.position.z = .3; bar.add(red, blue); bar.position.set(-.2, md.size.y + .07, 0); inner.add(bar); u.flash = [red, blue]; u.flashL = new THREE.PointLight(0xff2e4d, 0, 14, 2); u.flashL.position.set(0, md.size.y + .5, 0); inner.add(u.flashL); }
        const hl = new THREE.SpotLight(0xfff2d0, 0, 40, .45, .5, 1.5); hl.position.set(md.size.x / 2, .7, 0); hl.target.position.set(md.size.x / 2 + 10, 0, 0); inner.add(hl, hl.target); u.head = hl; }
      if (a.light) { const L = new THREE.PointLight(0xffe2a8, 0, 18, 2); L.position.set(0, (a.h || 5) * .95, 1); inner.add(L); u.lampL = L; }
    } else { inner = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshBasicMaterial({ color: 0x555066, wireframe: true })); inner.position.y = .5; u.pending = true; }
    holder.add(inner); u.inner = inner; scene.add(holder); rt[o.id] = u; setClip(o); if (AMB.env != null) holder.traverse(x => { if (x.isMesh && x.material) (Array.isArray(x.material) ? x.material : [x.material]).forEach(m => { if ('envMapIntensity' in m) m.envMapIntensity = AMB.env; }); }); return u;
  }
  function setClip(o) {
    const u = rt[o.id]; if (!u || !u.mixer) return; u.mixer.stopAllAction();
    const clip = (u.anims || []).find(c => new RegExp(o.clip || 'Idle', 'i').test(c.name)) || (u.anims || [])[0]; if (!clip) return;
    u.action = u.mixer.clipAction(clip); u.action.play(); u.clipDur = clip.duration;
  }
  function rebuild(o) { const u = rt[o.id]; if (u) { scene.remove(u.holder); if (u.smoke) scene.remove(u.smoke); if (gizmo.object === u.holder) gizmo.detach(); delete rt[o.id]; } build(o); if (sel === o.id) attach(); }
  function clearScene() { for (const id in rt) { scene.remove(rt[id].holder); if (rt[id].smoke) scene.remove(rt[id].smoke); delete rt[id]; } gizmo.detach(); if (mirror) { scene.remove(mirror); mirror = null; } }

  // ---------- animation : interpolation des images clés ----------
  const ease = u => u * u * (3 - 2 * u);
  function sample(o, time) {
    const k = o.keys || [];
    if (!k.length) return { p: o.base.p, r: o.base.r, s: o.base.s, f: o.fov || 40 };
    if (time <= k[0].t) return k[0]; if (time >= k[k.length - 1].t) return k[k.length - 1];
    let i = 0; while (i < k.length - 1 && k[i + 1].t < time) i++;
    const a = k[i], b = k[i + 1], uu = (time - a.t) / Math.max(1e-6, b.t - a.t), e = a.ease === 'linear' ? uu : ease(uu);
    return { p: a.p.map((v, j) => lerp(v, b.p[j], e)), r: a.r.map((v, j) => lerp(v, b.r[j], e)), s: a.s.map((v, j) => lerp(v, b.s[j], e)), f: lerp(a.f || 40, b.f || 40, e) };
  }
  function pathLen(o, time) { const k = o.keys || []; if (k.length < 2) return 0; let d = 0, prev = sample(o, 0).p; const n = Math.max(2, Math.ceil(time * 15)); for (let i = 1; i <= n; i++) { const q = sample(o, time * i / n).p; d += Math.hypot(q[0] - prev[0], q[2] - prev[2]); prev = q; } return d; }
  function evaluate(time) {
    for (const o of P.objects) {
      const u = rt[o.id]; if (!u) continue; const s = sample(o, time), h = u.holder;
      if (!(gizmo.dragging && gizmo.object === h)) { h.position.fromArray(s.p); h.rotation.set(s.r[0], s.r[1], s.r[2]); h.scale.fromArray(s.s); }
      if (o.asset === 'camera') {
        cinCam.position.copy(h.position); cinCam.fov = s.f || 40;
        const tg = o.target && P.objects.find(x => x.id === o.target);
        if (tg && rt[tg.id]) { const tp = rt[tg.id].holder.position.clone(); tp.y += (o.tgtY != null ? o.tgtY : 1); cinCam.lookAt(tp); h.quaternion.copy(cinCam.quaternion); }
        else cinCam.quaternion.copy(h.quaternion);
        cinCam.updateProjectionMatrix(); h.visible = !camView && !recording;
      }
      if (u.action) { u.action.time = ((time * (o.speed || 1)) % (u.clipDur || 1)); u.mixer.update(0); }
      if (u.wheels.length) { const ang = pathLen(o, time) / .34; for (const w of u.wheels) w.rotation.z = -ang; }
      if (u.flash) { const f = Math.sin(time * 18) > 0; u.flash[0].material.color.set(f ? 0xff2e4d : 0x300810); u.flash[1].material.color.set(f ? 0x0a1030 : 0x2e6bff); u.flashL.color.set(f ? 0xff2e4d : 0x2e6bff); u.flashL.intensity = AMB.night ? 6 : 2; }
      if (u.flame) { const y0 = sample(o, Math.max(0, time - .1)).p[1], vy = (s.p[1] - y0) * 10, on = vy > .2 || (o.ignite != null && time >= o.ignite); u.flame.visible = on; u.flame.scale.set(1, on ? .8 + Math.random() * .5 : 0, 1); u.flameL.intensity = on ? 6 + Math.random() * 3 : 0;
        if (!u.smoke.parent) scene.add(u.smoke); const base = u.holder.position; u.smoke.children.forEach((m, i) => { const st = on ? ((time * .6 + i / 14) % 1) : 0; m.visible = on && st > 0; const a = i * 2.4; m.position.set(base.x + Math.cos(a) * st * 14, Math.max(.6, base.y * .15) + st * 4, base.z + Math.sin(a) * st * 14); m.scale.setScalar(1 + st * 5); m.material.opacity = .75 * (1 - st); }); }
      if (u.boat) { u.inner.position.y = Math.sin(time * 2) * .12; u.inner.rotation.z = Math.sin(time * 1.6) * .03; }
      if (u.head) u.head.intensity = AMB.night ? 30 : 0;
      if (u.lampL) u.lampL.intensity = AMB.night ? 8 : 0;
    }
    if (P.rain) { const a = rain.geometry.attributes.position.array, c = (camView || recording) ? cinCam.position : edCam.position; rain.position.set(c.x, 0, c.z); const fall = (time * 32) % 40; for (let i = 0; i < a.length; i += 6) { const y0 = (a[i + 1] - fall + 400) % 40; a[i + 1] = y0; a[i + 4] = y0 - .9; } rain.geometry.attributes.position.needsUpdate = true; rain.userData.f = fall; }
  }

  // ---------- ambiances ----------
  let AMB = {};
  const AMBS = {
    night: { night: true, sky: false, bg: 0x05040a, fog: [0x07060f, 60, 320], hemi: [0x4a5a98, 0x0c0a12, .18], sun: [0x8aa0ff, .3, [-40, 60, -30]], exp: .95, bloom: .95, ground: 0x0f0e14, env: .12 },
    sunset: { sky: true, turb: 6, ray: 2.2, el: 4, az: 230, fog: [0xb87a68, 140, 1100], hemi: [0xffc4a0, 0x30242c, .4], sun: [0xffa860, 2.4, null], exp: .62, bloom: .4, ground: 0x2a2628, env: .45 },
    day: { sky: true, turb: 4, ray: 1, el: 48, az: 160, fog: [0xbcd3ea, 220, 1400], hemi: [0xdfeeff, 0x6a6458, .6], sun: [0xffffff, 2.8, null], exp: .5, bloom: .15, ground: 0x34313a, env: .8 },
    storm: { night: true, sky: false, bg: 0x0c0e14, fog: [0x12141b, 30, 220], hemi: [0x5b6680, 0x101116, .28], sun: [0x9aa6c0, .25, [30, 50, 20]], exp: 1, bloom: .7, ground: 0x121216, rain: true, env: .18 },
  };
  function applyAmbience() {
    AMB = AMBS[P.amb] || AMBS.night; const A = AMB;
    sky.visible = !!A.sky; stars.visible = !!A.night && P.amb !== 'storm';
    if (A.sky) { const u = sky.material.uniforms; u.turbidity.value = A.turb; u.rayleigh.value = A.ray; u.mieCoefficient.value = .005; u.mieDirectionalG.value = .8;
      const phi = THREE.MathUtils.degToRad(90 - A.el), th = THREE.MathUtils.degToRad(A.az), v = new THREE.Vector3().setFromSphericalCoords(1, phi, th); u.sunPosition.value.copy(v); sun.position.copy(v).multiplyScalar(120); scene.background = null; }
    else { scene.background = new THREE.Color(A.bg); sun.position.fromArray(A.sun[2]); }
    scene.fog = new THREE.Fog(A.fog[0], A.fog[1], A.fog[2]);
    hemi.color.set(A.hemi[0]); hemi.groundColor.set(A.hemi[1]); hemi.intensity = A.hemi[2];
    sun.color.set(A.sun[0]); sun.intensity = A.sun[1]; R.toneMappingExposure = A.exp;
    ground.material.color.set(A.ground); bloomPass.strength = P.bloom ? A.bloom : 0;
    rain.visible = !!P.rain; $('amb').value = P.amb; $('bloomBtn').classList.toggle('on', !!P.bloom); $('rainBtn').classList.toggle('on', !!P.rain); $('wetBtn').classList.toggle('on', !!P.wet);
    if (P.wet && !mirror) { mirror = new THREE.Reflector(new THREE.PlaneGeometry(400, 400), { textureWidth: lowEnd ? 512 : 1024, textureHeight: lowEnd ? 512 : 1024, color: AMB.night ? 0x3a3a44 : 0x888888, clipBias: .003 }); mirror.rotation.x = -PI / 2; mirror.position.y = .005; scene.add(mirror); ground.visible = false; }
    if (!P.wet && mirror) { scene.remove(mirror); mirror = null; ground.visible = true; }
    grid.visible = !camView && !recording; applyEnv();
  }
  function applyEnv() { const k = AMB.env != null ? AMB.env : .5; scene.traverse(o => { if (!o.isMesh || !o.material) return; (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => { if ('envMapIntensity' in m) m.envMapIntensity = k; }); }); if (mirror) mirror.material.uniforms.color.value.set(AMB.night ? 0x3a3a44 : 0x888888); }

  // ---------- rendu ----------
  function outSize() { const res = +(P.res || 720); return P.aspect === '9:16' ? [Math.round(res), Math.round(res * 16 / 9)] : P.aspect === '2.39' ? [Math.round(res * 2.39), res] : [Math.round(res * 16 / 9), res]; }
  const outAspect = () => { const [w, h] = outSize(); return w / h; };
  function layoutFrame() {
    const W = view.clientWidth, H = view.clientHeight, a = outAspect(); let fw = W, fh = W / a; if (fh > H) { fh = H; fw = H * a; }
    const f = $('frame'); f.style.width = fw + 'px'; f.style.height = fh + 'px'; f.style.left = (W - fw) / 2 + 'px'; f.style.top = (H - fh) / 2 + 'px'; f.classList.toggle('cam', camView);
    return [fw, fh, (W - fw) / 2, (H - fh) / 2];
  }
  let lastSize = '';
  function render(time) {
    const W = view.clientWidth, H = view.clientHeight, key = W + 'x' + H + camView + P.aspect;
    if (!recording && key !== lastSize) { lastSize = key; R.setSize(W, H, false); composer.setSize(W, H); edCam.aspect = W / H; edCam.updateProjectionMatrix(); }
    evaluate(time);
    const cam = camView || recording ? cinCam : edCam;
    if (!recording) { if (camView) { const [fw, fh, fx, fy] = layoutFrame(); cinCam.aspect = W / H; const k = fh / H; cinCam.fov = 2 * Math.atan(Math.tan((cinCam.fov * PI / 180) / 2) / k) * 180 / PI; cinCam.updateProjectionMatrix(); } else layoutFrame(); }
    gizmo.visible = !camView && !recording && !!gizmo.object; grid.visible = !camView && !recording;
    composer.passes[0].camera = cam; finalPass.uniforms.time.value = time; finalPass.uniforms.vig.value = camView || recording ? .38 : .12; finalPass.uniforms.grain.value = camView || recording ? .04 : 0;
    composer.render();
  }

  // ---------- projet ----------
  const newObj = (asset, extra = {}) => Object.assign({ id: uid(), asset, name: (ASSETS[asset] || { name: 'Caméra' }).name, color: {}, clip: 'Idle', keys: [], base: { p: [0, 0, 0], r: [0, 0, 0], s: [1, 1, 1] } }, extra);
  const K = (t, p, r = [0, 0, 0], s = [1, 1, 1], f) => ({ t, p, r, s, f });
  function defaultProject() { return { v: 1, name: 'Ma cinématique', duration: 12, aspect: '16:9', res: 720, amb: 'night', bloom: true, rain: false, wet: false, objects: [newObj('camera', { id: 'cam', name: 'Caméra', fov: 40, base: { p: [12, 4, 14], r: [-.2, .7, 0], s: [1, 1, 1] } })] }; }
  const TEMPLATES = {
    empty: () => defaultProject(),
    launch: () => { const p = defaultProject(); Object.assign(p, { name: 'Décollage', duration: 12, aspect: '16:9', amb: 'night', bloom: true, wet: true });
      const rk = newObj('rocket', { id: 'rocket', name: 'Fusée', ignite: 2.5, keys: [K(0, [0, 0, 0]), K(4, [0, 0, 0]), K(8, [0, 40, 0]), K(12, [0, 220, 0])] });
      rk.keys.forEach(k => k.ease = 'linear'); rk.keys[1].ease = 'ease'; rk.keys[2].ease = 'ease';
      p.objects.push(newObj('street', { id: 'street', name: 'Rue néon', seed: 21, length: 160, base: { p: [0, 0, -40], r: [0, 0, 0], s: [1, 1, 1] } }), rk,
        newObj('human_m', { name: 'Toi', color: { Shirt: '#21e6ff' }, clip: 'Idle', base: { p: [10, 0, 22], r: [0, PI + .6, 0], s: [1, 1, 1] } }),
        newObj('car_suv', { name: 'Rover de service', color: { Paint: '#f4f4f4' }, base: { p: [-14, 0, 16], r: [0, .7, 0], s: [1, 1, 1] } }));
      for (let i = 0; i < 3; i++) p.objects.push(newObj('lamp', { name: 'Projecteur ' + (i + 1), base: { p: [-12 + i * 12, 0, 10], r: [0, PI, 0], s: [1, 1, 1] } }));
      const cam = p.objects[0]; cam.target = 'rocket'; cam.tgtY = 16; cam.keys = [K(0, [34, 2.2, 66], [0, 0, 0], [1, 1, 1], 30), K(4, [26, 2.4, 52], [0, 0, 0], [1, 1, 1], 34), K(8, [30, 4, 50], [0, 0, 0], [1, 1, 1], 40), K(12, [40, 10, 60], [0, 0, 0], [1, 1, 1], 34)];
      return p; },
    chase: () => { const p = defaultProject(); Object.assign(p, { name: 'Poursuite de nuit', duration: 10, aspect: '2.39', amb: 'night', rain: true, wet: true });
      const car = newObj('car_sedan', { id: 'hero', name: 'Voiture du héros', color: { Paint: '#ff2e93' }, keys: [K(0, [-90, 0, -2.4]), K(4.5, [-20, 0, -2.4]), K(6, [2, 0, 2.2], [0, -.12, 0]), K(10, [96, 0, 2.2])] });
      const cop = newObj('police', { id: 'cop', name: 'Police', keys: [K(0, [-112, 0, 2.2]), K(5, [-35, 0, 2.2]), K(7, [-8, 0, -2.4], [0, .1, 0]), K(10, [70, 0, -2.4])] });
      p.objects.push(newObj('street', { id: 'street', name: 'Rue néon', seed: 7, length: 240, base: { p: [0, 0, 0], r: [0, 0, 0], s: [1, 1, 1] } }), car, cop,
        newObj('car_van', { name: 'Fourgon garé', color: { Paint: '#e8e4dc' }, base: { p: [18, 0, 5.6], r: [0, PI, 0], s: [1, 1, 1] } }),
        newObj('car_suv', { name: 'SUV garé', color: { Paint: '#2a2f3a' }, base: { p: [-34, 0, -5.6], r: [0, 0, 0], s: [1, 1, 1] } }),
        newObj('human_f', { name: 'Passante', color: { Shirt: '#ffd23f' }, clip: 'Walk', keys: [K(0, [-30, .18, 9.5], [0, PI / 2, 0]), K(10, [-14, .18, 9.5], [0, PI / 2, 0])] }),
        newObj('human_m', { name: 'Témoin', color: { Shirt: '#2e6bff' }, clip: 'Idle', base: { p: [8, .18, -9.5], r: [0, 0, 0], s: [1, 1, 1] } }));
      const cam = p.objects[0]; cam.target = 'hero'; cam.tgtY = .7; cam.keys = [K(0, [-97, .9, -7.5], [0, 0, 0], [1, 1, 1], 32), K(3.5, [-42, 1.6, -8.5], [0, 0, 0], [1, 1, 1], 36), K(6.2, [-6, 7, -6.5], [0, 0, 0], [1, 1, 1], 40), K(10, [52, 52, -4], [0, 0, 0], [1, 1, 1], 34)];
      return p; },
    arrival: () => { const p = defaultProject(); Object.assign(p, { name: 'Arrivée à Morro Azul', duration: 12, aspect: '16:9', amb: 'sunset', bloom: true });
      const hero = newObj('human_m', { id: 'hero', name: 'Le héros', color: { Shirt: '#21e6ff', Pants: '#2f4f86' }, clip: 'Walk', keys: [K(0, [-22, .18, 9.5], [0, PI / 2, 0]), K(12, [-6, .18, 9.5], [0, PI / 2, 0])] });
      p.objects.push(newObj('street', { id: 'street', name: 'Rue néon', seed: 3, length: 180, base: { p: [0, 0, 0], r: [0, 0, 0], s: [1, 1, 1] } }), hero);
      for (let i = 0; i < 6; i++) p.objects.push(newObj('palm', { name: 'Palmier ' + (i + 1), base: { p: [-40 + i * 14, .18, 11.2], r: [0, i, 0], s: [1, 1, 1] } }));
      p.objects.push(newObj('car_sports', { name: 'Cabriolet', color: { Paint: '#ffd23f' }, keys: [K(0, [60, 0, 2.2], [0, PI, 0]), K(12, [-70, 0, 2.2], [0, PI, 0])] }), newObj('bench', { name: 'Banc', base: { p: [-10, .18, 11], r: [0, PI, 0], s: [1, 1, 1] } }));
      const cam = p.objects[0]; cam.target = 'hero'; cam.tgtY = 1.3; cam.keys = [K(0, [-14, 1.2, 3], [0, 0, 0], [1, 1, 1], 30), K(6, [-12, 2.2, 15], [0, 0, 0], [1, 1, 1], 34), K(12, [-1, 6, 18], [0, 0, 0], [1, 1, 1], 42)];
      return p; },
    duel: () => { const p = defaultProject(); Object.assign(p, { name: 'Face-à-face', duration: 8, aspect: '2.39', amb: 'night', bloom: true, wet: true });
      p.objects.push(newObj('street', { id: 'street', name: 'Rue néon', seed: 11, length: 120, base: { p: [0, 0, 0], r: [0, 0, 0], s: [1, 1, 1] } }),
        newObj('human_m', { id: 'a', name: 'Rafa', color: { Shirt: '#16141c', Hair: '#0c0c0c' }, clip: 'Idle', base: { p: [-2.2, 0, 0], r: [0, PI / 2, 0], s: [1, 1, 1] } }),
        newObj('human_f', { id: 'b', name: 'Lia', color: { Shirt: '#c8102e' }, clip: 'Punch', speed: .8, base: { p: [2.2, 0, 0], r: [0, -PI / 2, 0], s: [1, 1, 1] } }),
        newObj('car_sedan', { name: 'Voiture phares allumés', color: { Paint: '#101016' }, base: { p: [10, 0, -1], r: [0, PI, 0], s: [1, 1, 1] } }),
        newObj('neon', { name: 'Enseigne', color: { Color: '#21e6ff' }, base: { p: [0, 5, -11.9], r: [0, 0, 0], s: [2, 1, 1] } }),
        newObj('light', { name: 'Lumière rose', color: { Color: '#ff2e93' }, intensity: 4, base: { p: [-6, 2, 4], r: [0, 0, 0], s: [1, 1, 1] } }));
      const cam = p.objects[0]; cam.target = 'b'; cam.tgtY = 1.4; cam.keys = [K(0, [0, 1.5, 9], [0, 0, 0], [1, 1, 1], 30), K(4, [-1.2, 1.6, 5], [0, 0, 0], [1, 1, 1], 28), K(8, [-3.6, 1.65, 2.4], [0, 0, 0], [1, 1, 1], 24)];
      return p; },
  };
  async function loadProject(p) {
    P = Object.assign(defaultProject(), p); P.objects = p.objects || defaultProject().objects; t = 0; sel = null;
    clearScene(); applyAmbience(); P.objects.forEach(build);
    await Promise.all(needFiles(P.objects).map(loadModel)); P.objects.forEach(o => { if (rt[o.id] && rt[o.id].pending) rebuild(o); });
    $('dur').value = P.duration; $('aspect').value = P.aspect; $('res').value = P.res; ui(); save();
  }

  // ---------- édition ----------
  const obj = id => P.objects.find(o => o.id === id);
  function attach() { const u = sel && rt[sel]; if (u && !(obj(sel).asset === 'street' && false)) gizmo.attach(u.holder); else gizmo.detach(); }
  function select(id) { sel = id; attach(); ui(); }
  function readHolder(o) { const h = rt[o.id].holder; return { p: h.position.toArray().map(v => +v.toFixed(3)), r: [h.rotation.x, h.rotation.y, h.rotation.z].map(v => +v.toFixed(4)), s: h.scale.toArray().map(v => +v.toFixed(3)) }; }
  function writeKey(o, tr) {
    if (o.keys.length || P.autoKey !== false) { const f = o.asset === 'camera' ? (sample(o, t).f || o.fov || 40) : undefined; const ex = o.keys.find(k => Math.abs(k.t - t) < .04); if (ex) Object.assign(ex, tr, f ? { f } : {}); else { o.keys.push(Object.assign({ t: +t.toFixed(2) }, tr, f ? { f } : {})); o.keys.sort((a, b) => a.t - b.t); } }
    else o.base = tr;
  }
  function commitTransform() { const o = obj(sel); if (!o) return; writeKey(o, readHolder(o)); ui(); save(); }
  function addAsset(asset) {
    const o = newObj(asset); const fwd = new THREE.Vector3(); edCam.getWorldDirection(fwd); const hit = orbit.target.clone();
    o.base.p = [+hit.x.toFixed(2), asset === 'neon' ? 3 : 0, +hit.z.toFixed(2)];
    if (ASSETS[asset].kind === 'street') { o.seed = Math.floor(Math.random() * 1000); o.length = 160; }
    if (ASSETS[asset].kind === 'human' && ASSETS[asset].slots.length) o.color = { Shirt: ['#ff2e93', '#21e6ff', '#ffd23f', '#3ecf6e', '#f2f2f2'][Math.floor(Math.random() * 5)] };
    P.objects.push(o); build(o); const f = ASSETS[asset].file; if (f && !models[f]) loadModel(f).then(() => rebuild(o));
    select(o.id); save(); toast(o.name + ' ajouté');
  }
  function delSel() { const o = obj(sel); if (!o || o.asset === 'camera') return; scene.remove(rt[o.id].holder); delete rt[o.id]; P.objects = P.objects.filter(x => x !== o); P.objects.forEach(x => { if (x.target === o.id) x.target = null; }); sel = null; gizmo.detach(); ui(); save(); }
  function dupSel() { const o = obj(sel); if (!o || o.asset === 'camera') return; const c = JSON.parse(JSON.stringify(o)); c.id = uid(); c.name = o.name + ' (copie)'; c.base.p = c.base.p.slice(); c.base.p[0] += 3; c.keys.forEach(k => { k.p = k.p.slice(); k.p[0] += 3; }); P.objects.push(c); build(c); select(c.id); save(); }

  // ---------- interface ----------
  function lib() {
    const mk = cat => Object.entries(ASSETS).filter(([, a]) => a.cat === cat).map(([k, a]) => `<button data-add="${k}"><b>${a.name}</b><small>${a.desc}</small></button>`).join('');
    $('libChars').innerHTML = mk('Chars'); $('libCars').innerHTML = mk('Cars'); $('libProps').innerHTML = mk('Props'); $('libPrims').innerHTML = mk('Prims');
  }
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function ui() {
    $('outliner').innerHTML = P.objects.map(o => `<button data-sel="${o.id}" class="${o.id === sel ? 'sel' : ''}">${esc(o.name)}<span>${o.keys.length ? o.keys.length + ' ◆' : ''}</span></button>`).join('');
    const o = obj(sel), I = $('insp');
    if (!o) { I.innerHTML = '<h2>Objet</h2><p class="empty">Choisis un objet dans la scène ou ajoute-en un depuis la bibliothèque.</p>'; }
    else {
      const a = ASSETS[o.asset] || {}, s = sample(o, t), num = (k, i, v, st) => `<input type="number" step="${st}" data-tr="${k}${i}" value="${(+v).toFixed(k === 'r' ? 2 : 2)}" aria-label="${k}${i}">`;
      const deg = v => v * 180 / PI;
      I.innerHTML = `<h2>Objet</h2>
        <div class="field"><label for="oname">Nom</label><input type="text" id="oname" value="${esc(o.name)}"></div>
        <div class="field" style="margin-top:6px"><label>Position</label><div class="vec">${s.p.map((v, i) => num('p', i, v, .1)).join('')}</div></div>
        <div class="field" style="margin-top:6px"><label>Rotation °</label><div class="vec">${s.r.map((v, i) => num('r', i, deg(v), 5)).join('')}</div></div>
        <div class="field" style="margin-top:6px"><label>Échelle</label><div class="vec">${s.s.map((v, i) => num('s', i, v, .1)).join('')}</div></div>
        ${(a.slots || []).length ? `<h2 style="margin-top:12px">Couleurs</h2><div class="colors">${a.slots.map(sl => `<label>${{ Skin: 'Peau', Shirt: 'Haut', Pants: 'Bas', Shoes: 'Chaussures', Hair: 'Cheveux', Paint: 'Carrosserie', Color: 'Couleur' }[sl]}<input type="color" data-col="${sl}" value="${(o.color || {})[sl] || (a.police && sl === 'Paint' ? '#eef0ff' : DEFCOL[sl])}"></label>`).join('')}</div>` : ''}
        ${a.kind === 'human' ? `<div class="field" style="margin-top:10px"><label for="oclip">Animation</label><select id="oclip">${CLIPS.map(c => `<option ${o.clip === c ? 'selected' : ''} value="${c}">${{ Idle: 'Attente', Walk: 'Marche', Run: 'Course', Punch: 'Coup de poing', Death: 'Chute' }[c]}</option>`).join('')}</select></div>
          <div class="field" style="margin-top:6px"><label for="ospeed">Vitesse</label><input type="number" id="ospeed" min=".2" max="3" step=".1" value="${o.speed || 1}"></div>` : ''}
        ${o.asset === 'camera' ? `<div class="field" style="margin-top:10px"><label for="ofov">Focale</label><select id="ofov">${[[24, '24 mm grand-angle'], [32, '35 mm'], [40, '50 mm'], [60, '85 mm portrait'], [80, '135 mm téléobjectif']].map(([v, l]) => `<option value="${v}" ${Math.round(s.f) === v || (o.lens || 40) === v ? 'selected' : ''}>${l}</option>`).join('')}</select></div>
          <div class="field" style="margin-top:6px"><label for="otgt">Viser</label><select id="otgt"><option value="">Rien (rotation libre)</option>${P.objects.filter(x => x.asset !== 'camera' && x.asset !== 'street').map(x => `<option value="${x.id}" ${o.target === x.id ? 'selected' : ''}>${esc(x.name)}</option>`).join('')}</select></div>` : ''}
        ${a.kind === 'street' ? `<div class="field" style="margin-top:10px"><label for="olen">Longueur</label><input type="number" id="olen" min="40" max="600" step="10" value="${o.length || 200}"></div><div class="row" style="margin-top:6px"><button id="reseed">Autres immeubles</button></div>` : ''}
        ${a.kind === 'light' ? `<div class="field" style="margin-top:10px"><label for="oint">Intensité</label><input type="number" id="oint" min="0" max="20" step=".5" value="${o.intensity || 3}"></div>` : ''}
        <div class="row" style="margin-top:12px">${o.asset !== 'camera' ? '<button id="dup">Dupliquer</button><button id="del">Supprimer</button>' : ''}<button id="clrKeys">Effacer les clés</button></div>
        <p class="empty" style="margin-top:8px">${o.keys.length ? o.keys.length + ' image(s) clé. Déplace l’objet à un autre instant : une nouvelle clé se crée.' : 'Sans image clé, l’objet reste immobile.'}</p>`;
    }
    tracks();
  }
  // timeline
  const tlPad = 12; const tl = $('tl');
  const t2x = time => tlPad + time / P.duration * (tl.clientWidth - tlPad * 2);
  const x2t = x => clamp((x - tlPad) / (tl.clientWidth - tlPad * 2) * P.duration, 0, P.duration);
  function tracks() {
    const step = P.duration > 30 ? 5 : P.duration > 12 && tl.clientWidth < 500 ? 2 : 1; let r = '';
    for (let s = 0; s <= P.duration + 1e-6; s += step) r += `<i style="left:${t2x(s)}px">${s}s</i>`;
    $('ruler').innerHTML = r;
    $('tracks').innerHTML = P.objects.map(o => `<div class="track ${o.id === sel ? 'sel' : ''}" data-track="${o.id}"><em>${esc(o.name)}</em>${o.keys.map((k, i) => `<b class="kf ${Math.abs(k.t - t) < .04 ? 'cur' : ''}" data-kf="${o.id}:${i}" style="left:${t2x(k.t)}px" title="${k.t.toFixed(2)} s"></b>`).join('')}</div>`).join('');
    playhead();
  }
  function playhead() { $('ph').style.left = t2x(t) + 'px'; $('tc').textContent = fmtT(t); }
  let drag = null;
  tl.addEventListener('pointerdown', e => {
    const r = tl.getBoundingClientRect(), x = e.clientX - r.left; const kf = e.target.closest('[data-kf]');
    if (kf) { const [id, i] = kf.dataset.kf.split(':'); drag = { kind: 'kf', o: obj(id), k: obj(id).keys[+i] }; select(id); t = drag.k.t; }
    else { const tr = e.target.closest('[data-track]'); if (tr && tr.dataset.track !== sel) select(tr.dataset.track); drag = { kind: 'ph' }; t = x2t(x); }
    playing = false; $('play').textContent = '▶ Lecture'; try { tl.setPointerCapture(e.pointerId); } catch (er) {} playhead(); ui();
  });
  tl.addEventListener('pointermove', e => { if (!drag) return; const r = tl.getBoundingClientRect(), nt = +x2t(e.clientX - r.left).toFixed(2); if (drag.kind === 'kf') { drag.k.t = nt; drag.o.keys.sort((a, b) => a.t - b.t); t = nt; tracks(); } else { t = nt; playhead(); } });
  tl.addEventListener('pointerup', () => { if (drag && drag.kind === 'kf') save(); drag = null; ui(); });

  // ---------- événements ----------
  document.addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b) return; const d = b.dataset;
    if (d.add) addAsset(d.add);
    else if (d.sel) select(d.sel);
    else if (d.mode) { gizmo.setMode(d.mode); document.querySelectorAll('[data-mode]').forEach(x => x.classList.toggle('on', x === b)); }
    else if (d.tab) { document.querySelectorAll('aside').forEach(a => a.classList.toggle('show', a.id === d.tab)); }
    else if (b.id === 'del') delSel(); else if (b.id === 'dup') dupSel();
    else if (b.id === 'clrKeys') { const o = obj(sel); if (o) { if (o.keys.length) o.base = { p: sample(o, t).p, r: sample(o, t).r, s: sample(o, t).s }; o.keys = []; ui(); save(); } }
    else if (b.id === 'reseed') { const o = obj(sel); o.seed = Math.floor(Math.random() * 1000); rebuild(o); save(); }
  });
  $('insp').addEventListener('change', e => {
    const o = obj(sel); if (!o) return; const el = e.target;
    if (el.id === 'oname') o.name = el.value || o.name;
    else if (el.dataset.tr) { const k = el.dataset.tr[0], i = +el.dataset.tr[1], s = sample(o, t), tr = { p: s.p.slice(), r: s.r.slice(), s: s.s.slice() }; tr[k][i] = k === 'r' ? (+el.value) * PI / 180 : +el.value; writeKey(o, tr); }
    else if (el.dataset.col) { o.color = Object.assign({}, o.color, { [el.dataset.col]: el.value }); rebuild(o); }
    else if (el.id === 'oclip') { o.clip = el.value; setClip(o); }
    else if (el.id === 'ospeed') o.speed = +el.value || 1;
    else if (el.id === 'ofov') { o.lens = +el.value; const ks = o.keys.find(k => Math.abs(k.t - t) < .04); if (ks) ks.f = +el.value; else if (o.keys.length) { const s = sample(o, t); o.keys.push({ t: +t.toFixed(2), p: s.p, r: s.r, s: s.s, f: +el.value }); o.keys.sort((a, b) => a.t - b.t); } else o.fov = +el.value; }
    else if (el.id === 'otgt') o.target = el.value || null;
    else if (el.id === 'olen') { o.length = +el.value; rebuild(o); }
    else if (el.id === 'oint') { o.intensity = +el.value; rebuild(o); }
    ui(); save();
  });
  $('tpl').addEventListener('change', async e => { const k = e.target.value; if (!k) return; await loadProject(TEMPLATES[k]()); e.target.value = ''; if (P.objects[0].keys.length) { camView = true; $('camView').classList.add('on'); } toast('Scène « ' + P.name + ' » chargée. Appuie sur Lecture.'); });
  $('play').addEventListener('click', () => { playing = !playing; if (playing && t >= P.duration - .01) t = 0; $('play').textContent = playing ? '❚❚ Pause' : '▶ Lecture'; });
  $('toStart').addEventListener('click', () => { t = 0; playhead(); ui(); });
  $('addKey').addEventListener('click', () => { const o = obj(sel); if (!o) { toast('Choisis d’abord un objet'); return; } const tr = readHolder(o), ex = o.keys.find(k => Math.abs(k.t - t) < .04); if (ex) Object.assign(ex, tr); else { o.keys.push(Object.assign({ t: +t.toFixed(2) }, tr, o.asset === 'camera' ? { f: sample(o, t).f } : {})); o.keys.sort((a, b) => a.t - b.t); } ui(); save(); toast('Clé posée à ' + t.toFixed(2) + ' s'); });
  $('delKey').addEventListener('click', () => { const o = obj(sel); if (!o) return; const i = o.keys.findIndex(k => Math.abs(k.t - t) < .06); if (i < 0) { toast('Pas de clé à cet instant'); return; } o.keys.splice(i, 1); ui(); save(); });
  $('autoKey').addEventListener('click', e => { P.autoKey = P.autoKey === false; e.target.classList.toggle('on', P.autoKey !== false); save(); });
  $('dur').addEventListener('change', e => { P.duration = clamp(+e.target.value || 12, 1, 120); t = Math.min(t, P.duration); ui(); save(); });
  $('aspect').addEventListener('change', e => { P.aspect = e.target.value; lastSize = ''; save(); });
  $('res').addEventListener('change', e => { P.res = +e.target.value; save(); });
  $('amb').addEventListener('change', e => { P.amb = e.target.value; if (P.amb === 'storm') P.rain = true; applyAmbience(); save(); });
  $('bloomBtn').addEventListener('click', () => { P.bloom = !P.bloom; applyAmbience(); save(); });
  $('rainBtn').addEventListener('click', () => { P.rain = !P.rain; applyAmbience(); save(); });
  $('wetBtn').addEventListener('click', () => { P.wet = !P.wet; applyAmbience(); save(); });
  $('camView').addEventListener('click', e => { camView = !camView; e.target.classList.toggle('on', camView); lastSize = ''; });
  $('camHere').addEventListener('click', () => { const o = obj('cam') || P.objects.find(x => x.asset === 'camera'); const tr = { p: edCam.position.toArray().map(v => +v.toFixed(3)), r: [edCam.rotation.x, edCam.rotation.y, edCam.rotation.z].map(v => +v.toFixed(4)), s: [1, 1, 1] }; if (o.target) o.target = null; writeKey(o, tr); ui(); save(); toast('Caméra placée' + (o.keys.length ? ' (clé à ' + t.toFixed(2) + ' s)' : '')); });
  addEventListener('keydown', e => { if (/input|select|textarea/i.test(e.target.tagName)) return; const k = e.key.toLowerCase();
    if (k === ' ') { e.preventDefault(); $('play').click(); } else if (k === 'w') document.querySelector('[data-mode=translate]').click(); else if (k === 'e') document.querySelector('[data-mode=rotate]').click(); else if (k === 'r') document.querySelector('[data-mode=scale]').click();
    else if (k === 'c') $('camView').click(); else if (k === 'k' || k === 'i') $('addKey').click(); else if (k === 'delete' || k === 'backspace') delSel(); });
  // sélection au clic dans la vue
  const ray = new THREE.Raycaster(); let downAt = null;
  cv.addEventListener('pointerdown', e => { downAt = [e.clientX, e.clientY]; });
  cv.addEventListener('pointerup', e => {
    if (!downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 6 || gizmo.dragging || camView) return;
    const r = cv.getBoundingClientRect(); ray.setFromCamera({ x: (e.clientX - r.left) / r.width * 2 - 1, y: -(e.clientY - r.top) / r.height * 2 + 1 }, edCam);
    const hits = ray.intersectObjects(Object.values(rt).map(u => u.holder), true);
    for (const h of hits) { let o = h.object; while (o && !o.userData.oid) o = o.parent; if (o) { const ob = obj(o.userData.oid); if (ob && ob.asset === 'street' && hits.some(x => { let q = x.object; while (q && !q.userData.oid) q = q.parent; return q && obj(q.userData.oid) && obj(q.userData.oid).asset !== 'street'; })) continue; select(o.userData.oid); return; } }
    select(null);
  });

  // ---------- sauvegarde, export ----------
  let saveT = 0; function save() { clearTimeout(saveT); saveT = setTimeout(() => { try { localStorage.setItem('neonstudio.project', JSON.stringify(P)); } catch (e) {} }, 400); }
  let toastT = 0; function toast(m) { const el = $('toast'); el.textContent = m; el.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => { el.hidden = true; }, 2600); }
  async function offer(filename, data) {
    try { const dl = window.claude && window.claude.use ? await window.claude.use('downloads') : null;
      if (dl) { await dl.save({ filename, data }); toast('Fichier prêt : ' + filename); return; } } catch (e) { if (e && e.code === 'declined') return; if (e && e.code && e.code !== 'unavailable') { toast('Enregistrement impossible (' + e.code + ')'); return; } }
    const url = URL.createObjectURL(data instanceof Blob ? data : new Blob([data])); const a = document.createElement('a'); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 4000);
  }
  $('saveBtn').addEventListener('click', () => offer((P.name || 'projet').replace(/[^\w\- ]+/g, '').trim().replace(/\s+/g, '-').toLowerCase() + '.json', JSON.stringify(P, null, 1)));
  $('loadBtn').addEventListener('click', () => $('loadIn').click());
  $('loadIn').addEventListener('change', async e => { const f = e.target.files[0]; if (!f) return; try { await loadProject(JSON.parse(await f.text())); toast('Projet chargé'); } catch (er) { toast('Ce fichier n’est pas un projet Néon Studio'); } e.target.value = ''; });
  function beginOut() { const [w, h] = outSize(); recording = true; R.setPixelRatio(1); R.setSize(w, h, false); composer.setSize(w, h); bloomPass.resolution.set(w, h); cinCam.aspect = w / h; cinCam.updateProjectionMatrix(); return [w, h]; }
  function endOut() { recording = false; R.setPixelRatio(Math.min(devicePixelRatio || 1, lowEnd ? 1.5 : 2)); lastSize = ''; }
  $('snap').addEventListener('click', () => { beginOut(); render(t); cv.toBlob(b => { endOut(); offer('neon-studio-' + Math.round(t * 100) + '.png', b); }, 'image/png'); });
  $('recBtn').addEventListener('click', async () => {
    if (recording) return; if (!window.MediaRecorder || !cv.captureStream) { toast('Ce navigateur ne sait pas enregistrer la vidéo : utilise le rendu cloud.'); return; }
    const types = ['video/mp4;codecs=avc1', 'video/mp4', 'video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm'], mime = types.find(x => MediaRecorder.isTypeSupported(x)) || '';
    const [w, h] = beginOut(), fps = 30, manual = (() => { const s = cv.captureStream(0), tr = s.getVideoTracks()[0]; return tr && tr.requestFrame ? { s, tr } : null; })();
    const stream = manual ? manual.s : cv.captureStream(fps), chunks = [];
    const rec = new MediaRecorder(stream, mime ? { mimeType: mime, videoBitsPerSecond: h >= 1000 ? 14e6 : 7e6 } : {});
    rec.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
    const done = new Promise(r => { rec.onstop = r; }); rec.start(250); playing = false;
    const ov = $('rec'); ov.hidden = false; const N = Math.round(P.duration * fps), t0 = performance.now();
    for (let f = 0; f <= N; f++) { const tt = f / fps; render(tt); if (manual) manual.tr.requestFrame(); ov.textContent = '● ENREGISTREMENT ' + w + '×' + h + ' · ' + fmtT(tt) + ' / ' + fmtT(P.duration); const wait = t0 + (f + 1) * 1000 / fps - performance.now(); await new Promise(r => setTimeout(r, Math.max(0, wait))); }
    rec.stop(); await done; ov.hidden = true; endOut();
    const ext = /mp4/.test(mime) ? 'mp4' : 'webm'; offer((P.name || 'cinematique').replace(/[^\w\- ]+/g, '').trim().replace(/\s+/g, '-').toLowerCase() + '.' + ext, new Blob(chunks, { type: mime || 'video/webm' }));
  });

  // ---------- boucle ----------
  let last = performance.now();
  function frame(now) { const dt = Math.min(.1, (now - last) / 1000); last = now; if (!recording) { if (playing) { t += dt; if (t >= P.duration) { t = P.duration; playing = false; $('play').textContent = '▶ Lecture'; } playhead(); } orbit.update(); render(t); } requestAnimationFrame(frame); }
  addEventListener('resize', () => { lastSize = ''; tracks(); });

  // ---------- rendu cloud (piloté par tools/studio/render.js) ----------
  window.STUDIO = { load: async p => { await loadProject(p); camView = true; return P.duration; }, frame: (time, w, h) => { recording = true; R.setPixelRatio(1); R.setSize(w, h, false); composer.setSize(w, h); bloomPass.resolution.set(w, h); cinCam.aspect = w / h; cinCam.updateProjectionMatrix(); render(time); return true; }, templates: Object.keys(TEMPLATES), template: k => TEMPLATES[k]() };

  // ---------- démarrage ----------
  lib();
  let saved = null; try { saved = JSON.parse(localStorage.getItem('neonstudio.project') || 'null'); } catch (e) {}
  loadProject(saved && saved.objects ? saved : TEMPLATES.chase()).then(() => { if (!saved) { camView = true; $('camView').classList.add('on'); } });
  if (lowEnd) document.querySelector('#pLib').classList.add('show');
  requestAnimationFrame(frame);
})();
