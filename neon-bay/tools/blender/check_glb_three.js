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
const HUMAN_CLIPS = ['Idle', 'Walk', 'Run', 'Punch', 'Death', 'Aim', 'AimRifle', 'Crouch'];
const LOOPS = ['Idle', 'Walk', 'Run', 'Aim', 'AimRifle', 'Crouch'];
// weapon id -> [min length, max length] in metres along X
const WEAPON_LEN = { pistol: [0.17, 0.26], uzi: [0.35, 0.55], shotgun: [0.9, 1.15], rifle: [0.82, 1.0],
  sniper: [1.1, 1.3], rocket: [1.0, 1.2], minigun: [0.85, 1.1], lmg: [0.95, 1.15], gl: [0.6, 0.85], rail: [0.9, 1.1] };
const WEAPON_LENS = ['rifle', 'sniper', 'rocket', 'gl', 'rail'];
const CONTRACT = {
  car: { mats: ['Paint', 'Glass', 'Tyre', 'Rim', 'LightFront', 'LightRear', 'Trim'],
         nodes: ['Wheel_FL', 'Wheel_FR', 'Wheel_RL', 'Wheel_RR'], maxTris: 4200 },
  human: { mats: ['Skin', 'Shirt', 'Pants', 'Shoes', 'Hair', 'Eyes'], clips: HUMAN_CLIPS,
           // three.js strips '.' from node names: UpperArm.L -> UpperArmL
           nodes: ['Hips', 'Spine', 'Chest', 'Neck', 'Head', 'UpperArmL', 'UpperArmR', 'LowerArmL', 'LowerArmR',
                   'HandL', 'HandR', 'UpperLegL', 'UpperLegR', 'LowerLegL', 'LowerLegR', 'FootL', 'FootR'],
           maxTris: 9000 },
  weapon: { mats: ['Body', 'Metal', 'Grip', 'Glow'], maxTris: 2500, maxBytes: 120 * 1024 },
  lamp: { mats: ['Bulb'], maxTris: 1500 },
  prop: { mats: [], maxTris: 1500 },
};

function contractFor(name) {
  if (name.startsWith('car_')) return CONTRACT.car;
  if (name.startsWith('human_')) return CONTRACT.human;
  if (name.startsWith('w_')) return CONTRACT.weapon;
  if (name === 'lamp') return CONTRACT.lamp;
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
      const meshes = [], mats = new Set(), nodes = [];
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
        ms.forEach(m => mats.add(m.name));
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
      return {
        meshes, mats: [...mats], tris, skinned, nodes, loopErr, human,
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
      if (!(info.max[0] > -info.min[0])) errs.push('barrel not towards +X');
      if (!(info.min[0] < 0 && info.min[1] < 0 && info.max[1] > 0)) errs.push('origin not inside the grip area');
    }
    if (c === CONTRACT.human) {
      const h = name === 'human_f' ? [1.66, 1.76] : [1.75, 1.85];
      if (info.size[1] < h[0] || info.size[1] > h[1]) errs.push('height ' + info.size[1] + ' outside ' + h);
      if (Math.abs(info.min[1]) > 0.005) errs.push('feet not on y=0 (min y ' + info.min[1] + ')');
      if (!info.human || !(info.human.handLx > 0 && info.human.handRx < 0)) errs.push('not facing +Z (HandL must be at +X)');
    }
    console.log(`\n== ${name}.glb  ${(buf.length / 1024).toFixed(1)} KB  ${info.tris} tris  size(x,y,z)=${info.size} min=${info.min} max=${info.max}`);
    console.log('  meshes   :', info.meshes.join(', '));
    console.log('  materials:', info.mats.join(', '));
    if (info.skinned) console.log('  skinned meshes:', info.skinned);
    if (info.clips.length) console.log('  clips    :', info.clips.join(', '));
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
