// Neon Bay - checks that the generated .glb files load in three.js r128 (vendor/).
//   node tools/blender/check_glb_three.js            # every models/*.glb
//   node tools/blender/check_glb_three.js car_sedan  # some models
// Loads each file in headless Chromium through THREE.GLTFLoader.parse (bytes read in Node),
// prints meshes, materials, triangle count, bones and animation clips, and checks the
// naming / size / orientation contracts. Exit code 1 if a contract is broken.
// For humans it also prints, for the Aim and AimRifle clips, the transform to give a weapon
// (w_*.glb: barrel +X, up +Y, origin = grip) parented to the HandR bone so that it points
// forward (+Z of the character) with its grip in the palm.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..', '..');
const MODELS = path.join(ROOT, 'models');
// v4: every human also has Dance, Dance2 (baile funk), Sit and Workout (prison yard)
const HUMAN_CLIPS = ['Idle', 'Walk', 'Run', 'Punch', 'Death', 'Aim', 'AimRifle', 'Crouch', 'Dance', 'Dance2', 'Sit', 'Workout'];
const LOOPS = ['Idle', 'Walk', 'Run', 'Aim', 'AimRifle', 'Crouch', 'Dance', 'Dance2', 'Sit', 'Workout', 'Fly'];
// animals (gen_animals.py): face +X, materials Fur / Fur2 / Eye, clips per species, <= 4000 tris
const ANIMAL_CLIPS = { dog: ['Idle', 'Walk', 'Run', 'Sit'], cat: ['Idle', 'Walk', 'Sit'], bird: ['Idle', 'Fly'],
  parrot: ['Idle', 'Fly'], crab: ['Idle', 'Walk'] };
// weapon id -> [min length, max length] in metres along X
const WEAPON_LEN = { pistol: [0.17, 0.26], uzi: [0.35, 0.55], shotgun: [0.9, 1.15], rifle: [0.82, 1.0],
  sniper: [1.1, 1.3], rocket: [1.0, 1.2], minigun: [0.85, 1.1], lmg: [0.95, 1.15], gl: [0.6, 0.85], rail: [0.9, 1.1] };
const WEAPON_LENS = ['rifle', 'sniper', 'rocket', 'gl', 'rail'];
const WEAPON_TRIS = { pistol: 4000, uzi: 9000, shotgun: 9000, rifle: 9000, sniper: 9000, rail: 9000,
  rocket: 12000, minigun: 12000, lmg: 12000, gl: 12000 };
const CONTRACT = {
  // v3 cars: <= 9000 tris, <= 700 KB, 7 materials (= draw calls); every node matching /^Wheel/ (the game
  // spins them all) must be one of the listed wheels, at the hub, unrotated
  car: { mats: ['Paint', 'Glass', 'Tyre', 'Rim', 'LightFront', 'LightRear', 'Trim'],
         nodes: ['Wheel_FL', 'Wheel_FR', 'Wheel_RL', 'Wheel_RR'], maxTris: 9000, maxBytes: 700 * 1024, maxMats: 7,
         len: [4.3, 4.95] },
  // new vehicles: <= 12000 tris, <= 900 KB
  car_police: { mats: ['Paint', 'Glass', 'Tyre', 'Rim', 'LightFront', 'LightRear', 'Trim', 'Livery', 'SirenRed', 'SirenBlue'],
         nodes: ['Wheel_FL', 'Wheel_FR', 'Wheel_RL', 'Wheel_RR', 'Lightbar'], maxTris: 12000, maxBytes: 900 * 1024,
         maxMats: 10, len: [4.3, 4.9] },
  army_jeep: { mats: ['Paint', 'Glass', 'Tyre', 'Rim', 'LightFront', 'LightRear', 'Trim'],
         nodes: ['Wheel_FL', 'Wheel_FR', 'Wheel_RL', 'Wheel_RR'], maxTris: 12000, maxBytes: 900 * 1024, maxMats: 8,
         len: [3.5, 4.2] },
  army_truck: { mats: ['Paint', 'Glass', 'Tyre', 'Rim', 'LightFront', 'LightRear', 'Trim', 'Canvas'],
         nodes: ['Wheel_FL', 'Wheel_FR', 'Wheel_ML', 'Wheel_MR', 'Wheel_RL', 'Wheel_RR'], maxTris: 12000,
         maxBytes: 900 * 1024, maxMats: 8, len: [6.8, 7.8] },
  army_apc: { mats: ['Paint', 'Glass', 'Tyre', 'Rim', 'LightFront', 'LightRear', 'Trim'],
         nodes: ['Wheel_FL', 'Wheel_FR', 'Wheel_F2L', 'Wheel_F2R', 'Wheel_R2L', 'Wheel_R2R', 'Wheel_RL', 'Wheel_RR',
                 'Turret', 'Gun'], maxTris: 12000, maxBytes: 900 * 1024, maxMats: 8, len: [6.6, 8.0] },
  // landmarks + sports (gen_landmarks.py): real scale, metres; <= 15000 tris / 900 KB for monuments,
  // <= 4000 tris per sports prop (ring and stand <= 8000)
  lm_statue: { mats: ['Patina', 'Glow', 'Stone'], maxTris: 15000, maxBytes: 900 * 1024 },
  lm_palace: { mats: ['Marble', 'Stone', 'Grass', 'Glass', 'Flag', 'FlagStar', 'Metal', 'Water'], maxTris: 15000,
               maxBytes: 900 * 1024 },
  prop_basket_hoop: { mats: ['Metal', 'Board', 'HoopRed', 'Rope'], maxTris: 4000, maxBytes: 300 * 1024 },
  prop_basket_court: { mats: ['CourtFloor'], maxTris: 4000, maxBytes: 300 * 1024, textured: ['CourtFloor'] },
  prop_soccer_goal: { mats: ['GoalPost', 'Rope'], maxTris: 4000, maxBytes: 300 * 1024 },
  prop_soccer_field: { mats: ['Pitch'], maxTris: 4000, maxBytes: 300 * 1024, textured: ['Pitch'] },
  prop_boxing_ring: { mats: ['Canvas', 'Rope', 'Metal', 'Glow', 'CornerRed', 'CornerBlue'], maxTris: 8000,
                      maxBytes: 500 * 1024 },
  prop_ball_basket: { mats: ['Rubber', 'Seam'], maxTris: 4000, maxBytes: 300 * 1024 },
  prop_ball_soccer: { mats: ['BallWhite', 'BallBlack'], maxTris: 4000, maxBytes: 300 * 1024 },
  prop_stadium_stand: { mats: ['Concrete', 'SeatA', 'SeatB'], maxTris: 8000, maxBytes: 500 * 1024 },
  human: { mats: ['Skin', 'Shirt', 'Pants', 'Shoes', 'Hair', 'Eyes'], clips: HUMAN_CLIPS,
           // three.js strips '.' from node names: UpperArm.L -> UpperArmL
           nodes: ['Hips', 'Spine', 'Chest', 'Neck', 'Head', 'UpperArmL', 'UpperArmR', 'LowerArmL', 'LowerArmR',
                   'HandL', 'HandR', 'UpperLegL', 'UpperLegR', 'LowerLegL', 'LowerLegR', 'FootL', 'FootR',
                   // v3 finger bones (children of HandL / HandR)
                   'ThumbL', 'ThumbR', 'Thumb2L', 'Thumb2R', 'FingersL', 'FingersR', 'Fingers2L', 'Fingers2R'],
           // baked textures: colour map on these slots (x material.color), fabric normal maps
           textured: ['Skin', 'Shirt', 'Pants', 'Shoes'], normals: ['Shirt', 'Pants'],
           maxTris: 9000, maxBytes: 1024 * 1024 },   // v4: 1 MB (12 clips + new accessories)
  // v3 weapons: pistol <= 4000 tris, rifles <= 9000, heavy weapons <= 12000 (WEAPON_TRIS), <= 600 KB each
  weapon: { mats: ['Body', 'Metal', 'Grip', 'Glow'], maxTris: 12000, maxBytes: 600 * 1024 },
  lamp: { mats: ['Bulb'], maxTris: 1500 },
  animal: { mats: ['Fur', 'Fur2', 'Eye'], maxTris: 4000, maxBytes: 600 * 1024 },
  // beach / party / prison set dressing (gen_scene_props.py): static, <= 3000 tris
  sceneprop: { mats: [], maxTris: 3000, maxBytes: 400 * 1024 },
  prop: { mats: [], maxTris: 1500 },
};

function contractFor(name) {
  if (CONTRACT[name]) return CONTRACT[name];
  if (name.startsWith('car_')) return CONTRACT.car;
  if (name.startsWith('human_')) return CONTRACT.human;
  if (name.startsWith('w_')) return CONTRACT.weapon;
  if (name === 'lamp') return CONTRACT.lamp;
  if (name.startsWith('animal_')) return CONTRACT.animal;
  if (name.startsWith('prop_')) return CONTRACT.sceneprop;
  return CONTRACT.prop;
}

(async () => {
  const want = process.argv.slice(2);
  const files = fs.readdirSync(MODELS).filter(f => f.endsWith('.glb') && f !== 'robot.glb')
    .map(f => f.replace(/\.glb$/, '')).filter(n => !want.length || want.includes(n)).sort();
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('console', m => { if (m.type() === 'error') console.log('[page]', m.text()); });
  await page.setContent('<html><body></body></html>');
  await page.addScriptTag({ path: path.join(ROOT, 'vendor', 'three.min.js') });
  await page.addScriptTag({ path: path.join(ROOT, 'vendor', 'GLTFLoader.js') });
  let failed = 0, totalBytes = 0;
  for (const name of files) {
    const buf = fs.readFileSync(path.join(MODELS, name + '.glb'));
    totalBytes += buf.length;
    const info = await page.evaluate(async ({ b64, loops }) => {
      const bin = atob(b64), u8 = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
      const gltf = await new Promise((res, rej) => new THREE.GLTFLoader().parse(u8.buffer, '', res, rej));
      const meshes = [], mats = new Set(), nodes = [], texd = {};
      let tris = 0, skinned = 0;
      const box = new THREE.Box3().setFromObject(gltf.scene);
      gltf.scene.traverse(o => {
        nodes.push(o.name);
        if (!o.isMesh) return;
        if (o.isSkinnedMesh) skinned++;
        const g = o.geometry;
        const t = g.index ? g.index.count / 3 : g.attributes.position.count / 3;
        tris += t;
        const ms = Array.isArray(o.material) ? o.material : [o.material];
        ms.forEach(m => { mats.add(m.name);
          if (m.map) texd[m.name] = (texd[m.name] || '') + 'map' + m.map.image.width + 'x' + m.map.image.height;
          if (m.normalMap) texd[m.name] = (texd[m.name] || '') + '+normal'; });
        meshes.push(o.name + '(' + ms.map(m => m.name).join('/') + ')');
      });
      // loop clips must end on their first pose
      const loopErr = [];
      gltf.animations.forEach(a => {
        if (!loops.includes(a.name)) return;
        let worst = 0;
        a.tracks.forEach(tr => {
          const n = tr.getValueSize(), v = tr.values, last = v.length - n;
          for (let i = 0; i < n; i++) worst = Math.max(worst, Math.abs(v[i] - v[last + i]));
        });
        if (worst > 2e-3) loopErr.push(a.name + ' (' + worst.toFixed(4) + ')');
      });
      // humans: orientation + weapon attach transforms on HandR
      let human = null;
      const hand = gltf.scene.getObjectByName('HandR');
      if (hand && gltf.animations.length) {
        const V = (x, y, z) => new THREE.Vector3(x, y, z);
        const r3 = v => v.toArray().map(x => +x.toFixed(3));
        gltf.scene.updateMatrixWorld(true);
        const handL = gltf.scene.getObjectByName('HandL'), fore = gltf.scene.getObjectByName('LowerArmR');
        const head = gltf.scene.getObjectByName('Head');
        const pH = hand.getWorldPosition(V()), pL = handL.getWorldPosition(V()), pF = fore.getWorldPosition(V());
        const qRest = hand.getWorldQuaternion(new THREE.Quaternion());
        const along = pH.clone().sub(pF).normalize();
        const localY = V(0, 1, 0).applyQuaternion(qRest);
        // palm of the right hand faces +X (the body) in the A-pose
        const inv = qRest.clone().invert();
        const palmL = V(1, 0, 0).applyQuaternion(inv);
        palmL.sub(V(0, 1, 0).multiplyScalar(palmL.y)).normalize();
        const gripLocal = V(0, 0.078, 0).add(palmL.clone().multiplyScalar(0.018));
        const W = new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), -Math.PI / 2); // weapon +X -> +Z
        const attach = {};
        const mixer = new THREE.AnimationMixer(gltf.scene);
        for (const clip of ['Aim', 'AimRifle']) {
          const c = gltf.animations.find(a => a.name === clip);
          if (!c) continue;
          mixer.stopAllAction();
          mixer.clipAction(c).reset().play();
          mixer.setTime(0);
          gltf.scene.updateMatrixWorld(true);
          const qW = hand.getWorldQuaternion(new THREE.Quaternion());
          const q = qW.clone().invert().multiply(W);
          const e = new THREE.Euler().setFromQuaternion(q, 'XYZ');
          const gw = hand.localToWorld(gripLocal.clone());
          const palmLeft = handL.localToWorld(V(0, 0.075, 0));
          attach[clip] = { pos: r3(gripLocal), quat: q.toArray().map(x => +x.toFixed(4)),
            eulerXYZdeg: [e.x, e.y, e.z].map(x => +(x * 180 / Math.PI).toFixed(1)),
            gripWorld: r3(gw), leftPalmWorld: r3(palmLeft), handsGap: +gw.distanceTo(palmLeft).toFixed(3) };
        }
        mixer.stopAllAction();
        human = { handLx: +pL.x.toFixed(3), handRx: +pH.x.toFixed(3), headY: +head.getWorldPosition(V()).y.toFixed(3),
          boneYalongHand: +along.dot(localY).toFixed(3), attach };
      }
      // vehicles: every node the game would spin (/^Wheel/) with its hub position and rotation
      const wheels = [];
      gltf.scene.updateMatrixWorld(true);
      gltf.scene.traverse(o => { if (/^Wheel/i.test(o.name)) {
        const wb = new THREE.Box3().setFromObject(o), p = o.getWorldPosition(new THREE.Vector3());
        wheels.push({ name: o.name, pos: p.toArray().map(v => +v.toFixed(3)), rot: +(Math.abs(o.rotation.x) + Math.abs(o.rotation.y) + Math.abs(o.rotation.z)).toFixed(4),
          r: +((wb.max.y - wb.min.y) / 2).toFixed(3), minY: +wb.min.y.toFixed(3), parent: o.parent ? o.parent.name : '' }); } });
      return {
        meshes, mats: [...mats], texd, tris, skinned, nodes, loopErr, human, wheels,
        clips: gltf.animations.map(a => a.name + ':' + a.duration.toFixed(2) + 's/' + a.tracks.length + 'tr'),
        clipNames: gltf.animations.map(a => a.name),
        size: box.getSize(new THREE.Vector3()).toArray().map(v => +v.toFixed(3)),
        min: box.min.toArray().map(v => +v.toFixed(3)),
        max: box.max.toArray().map(v => +v.toFixed(3)),
      };
    }, { b64: buf.toString('base64'), loops: LOOPS });
    const c = contractFor(name);
    const errs = [];
    c.mats.forEach(m => { if (!info.mats.includes(m)) errs.push('missing material ' + m); });
    (c.nodes || []).forEach(n => { if (!info.nodes.includes(n)) errs.push('missing node ' + n); });
    (c.clips || []).forEach(n => { if (!info.clipNames.includes(n)) errs.push('missing clip ' + n); });
    if (info.tris > c.maxTris) errs.push('too many triangles ' + info.tris);
    if (c.maxBytes && buf.length > c.maxBytes) errs.push('file too big ' + buf.length);
    if (info.loopErr.length) errs.push('loop clips do not close: ' + info.loopErr.join(', '));
    if (c === CONTRACT.weapon) {
      const id = name.slice(2), len = WEAPON_LEN[id];
      if (WEAPON_LENS.includes(id) && !info.mats.includes('Lens')) errs.push('missing material Lens');
      if (info.clipNames.length) errs.push('weapons must not be animated');
      if (len && (info.size[0] < len[0] || info.size[0] > len[1])) errs.push('length ' + info.size[0] + ' outside ' + len);
      if (WEAPON_TRIS[id] && info.tris > WEAPON_TRIS[id]) errs.push('too many triangles for ' + id + ': ' + info.tris + ' > ' + WEAPON_TRIS[id]);
      if (!(info.max[0] > -info.min[0])) errs.push('barrel not towards +X');
      if (!(info.min[0] < 0 && info.min[1] < 0 && info.max[1] > 0)) errs.push('origin not inside the grip area');
    }
    if (c.maxMats && info.mats.length > c.maxMats) errs.push('too many materials ' + info.mats.length);
    if (c.textured && c !== CONTRACT.human)    // printed maps (court / pitch): 512 px colour texture
      c.textured.forEach(m => { if (!/map512x512/.test(info.texd[m] || '')) errs.push('no 512x512 texture on ' + m); });
    // hand-held props (gen_scene_props.py) have their origin at the grip, not on the ground
    if (/^prop_/.test(name) && !['prop_rescue_tube', 'prop_dumbbell'].includes(name) && Math.abs(info.min[1]) > 0.01)
      errs.push('not on the ground (min y ' + info.min[1] + ')');
    if (c.len) {
      if (info.size[0] < c.len[0] || info.size[0] > c.len[1]) errs.push('length ' + info.size[0] + ' outside ' + c.len);
      if (Math.abs(info.min[1]) > 0.01) errs.push('not on the ground (min y ' + info.min[1] + ')');
      if (!(info.max[0] > 0 && info.min[0] < 0)) errs.push('origin not inside the vehicle');
      const wn = (c.nodes || []).filter(n => /^Wheel/.test(n));
      info.wheels.forEach(w => {
        if (!wn.includes(w.name)) errs.push('unexpected node matching /^Wheel/: ' + w.name);
        if (w.rot > 1e-4) errs.push(w.name + ' is rotated');
        if (Math.abs(w.minY) > 0.01) errs.push(w.name + ' does not touch the ground (' + w.minY + ')');
        if (Math.abs(w.pos[1] - w.r) > 0.02) errs.push(w.name + ' origin not at the hub');
      });
      // front axle towards +X, left wheels at -Z (glTF)
      const fl = info.wheels.find(w => w.name === 'Wheel_FL'), rl = info.wheels.find(w => w.name === 'Wheel_RL');
      if (fl && rl && !(fl.pos[0] > rl.pos[0] && fl.pos[2] < 0)) errs.push('front not towards +X / left not at -Z');
    }
    if (c === CONTRACT.animal) {
      const id = name.slice(7);
      (ANIMAL_CLIPS[id] || []).forEach(n => { if (!info.clipNames.includes(n)) errs.push('missing clip ' + n); });
      if (!info.skinned) errs.push('animal must be skinned');
      if (Math.abs(info.min[1]) > 0.01) errs.push('not on the ground (min y ' + info.min[1] + ')');
      if (!(info.size[0] >= info.size[2] * 0.6 || id === 'crab' || id === 'bird' || id === 'parrot')) errs.push('not facing +X');
    }
    if (c === CONTRACT.sceneprop && info.clipNames.length) errs.push('props must be static');
    if (c === CONTRACT.human) {
      // human_f / human_f2: 1.71 m (+ hair); human_m: 1.80 m; human_m2: 1.765 m + cap
      const h = name.startsWith('human_f') ? [1.66, 1.76] : [1.75, 1.85];
      c.textured.forEach(m => { if (!/map512x512/.test(info.texd[m] || '')) errs.push('no 512x512 texture on ' + m); });
      c.normals.forEach(m => { if (!/normal/.test(info.texd[m] || '')) errs.push('no normal map on ' + m); });
      if (['human_m2', 'human_m3', 'human_m4'].includes(name) && !info.mats.includes('Hat')) errs.push('missing material Hat');
      if (info.size[1] < h[0] || info.size[1] > h[1]) errs.push('height ' + info.size[1] + ' outside ' + h);
      if (Math.abs(info.min[1]) > 0.005) errs.push('feet not on y=0 (min y ' + info.min[1] + ')');
      if (!info.human || !(info.human.handLx > 0 && info.human.handRx < 0)) errs.push('not facing +Z (HandL must be at +X)');
    }
    console.log(`\n== ${name}.glb  ${(buf.length / 1024).toFixed(1)} KB  ${info.tris} tris  size(x,y,z)=${info.size} min=${info.min} max=${info.max}`);
    console.log('  meshes   :', info.meshes.join(', '));
    console.log('  materials:', info.mats.join(', '));
    if (info.skinned) console.log('  skinned meshes:', info.skinned);
    if (info.clips.length) console.log('  clips    :', info.clips.join(', '));
    if (c.len) console.log('  wheels   :', info.wheels.map(w => w.name + '@' + w.pos + ' R=' + w.r + ' (' + w.parent + ')').join(', '));
    if (c.len) { const ex = info.nodes.filter(n => /^(Lightbar|Turret|Gun)$/.test(n)); if (ex.length) console.log('  nodes    :', ex.join(', ')); }
    if (Object.keys(info.texd).length) console.log('  textures :', Object.entries(info.texd).map(([k, v]) => k + ':' + v).join(', '));
    if (info.human) {
      console.log('  bones    : HandL.x=' + info.human.handLx + ' HandR.x=' + info.human.handRx +
        ' Head.y=' + info.human.headY + '  (HandR local +Y along the hand: dot=' + info.human.boneYalongHand + ')');
      for (const [clip, a] of Object.entries(info.human.attach))
        console.log(`  weapon on HandR in ${clip}: position ${a.pos}  quaternion ${a.quat}  euler XYZ(deg) ${a.eulerXYZdeg}` +
          `  | grip at ${a.gripWorld}, left palm at ${a.leftPalmWorld} (gap ${a.handsGap} m)`);
    }
    console.log(errs.length ? '  FAIL: ' + errs.join('; ') : '  OK');
    if (errs.length) failed++;
  }
  console.log(`\nTotal glb size: ${(totalBytes / 1024 / 1024).toFixed(2)} MB, ${files.length} files, ${failed} failing`);
  await browser.close();
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
