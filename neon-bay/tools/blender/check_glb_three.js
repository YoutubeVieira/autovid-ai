// Neon Bay - checks that the generated .glb files load in three.js r128 (vendor/).
//   node tools/blender/check_glb_three.js            # every models/*.glb
//   node tools/blender/check_glb_three.js car_sedan  # some models
// Loads each file in headless Chromium through THREE.GLTFLoader.parse (bytes read in Node),
// prints meshes, materials, triangle count, bones and animation clips, and checks the
// naming contracts. Exit code 1 if a contract is broken.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..', '..');
const MODELS = path.join(ROOT, 'models');
const CONTRACT = {
  car: { mats: ['Paint', 'Glass', 'Tyre', 'Rim', 'LightFront', 'LightRear', 'Trim'],
         nodes: ['Wheel_FL', 'Wheel_FR', 'Wheel_RL', 'Wheel_RR'], maxTris: 4200 },
  human: { mats: ['Skin', 'Shirt', 'Pants', 'Shoes', 'Hair'], clips: ['Idle', 'Walk', 'Run', 'Punch', 'Death'],
           // three.js strips '.' from node names: UpperArm.L -> UpperArmL
           nodes: ['Hips', 'Spine', 'Chest', 'Neck', 'Head', 'UpperArmL', 'UpperArmR', 'LowerArmL', 'LowerArmR',
                   'HandL', 'HandR', 'UpperLegL', 'UpperLegR', 'LowerLegL', 'LowerLegR', 'FootL', 'FootR'],
           maxTris: 6200 },
  lamp: { mats: ['Bulb'], maxTris: 1500 },
  prop: { mats: [], maxTris: 1500 },
};

function contractFor(name) {
  if (name.startsWith('car_')) return CONTRACT.car;
  if (name.startsWith('human_')) return CONTRACT.human;
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
    const info = await page.evaluate(async (b64) => {
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
      return {
        meshes, mats: [...mats], tris, skinned, nodes,
        clips: gltf.animations.map(a => a.name + ':' + a.duration.toFixed(2) + 's/' + a.tracks.length + 'tr'),
        clipNames: gltf.animations.map(a => a.name),
        size: box.getSize(new THREE.Vector3()).toArray().map(v => +v.toFixed(2)),
        min: box.min.toArray().map(v => +v.toFixed(2)),
      };
    }, buf.toString('base64'));
    const c = contractFor(name);
    const errs = [];
    c.mats.forEach(m => { if (!info.mats.includes(m)) errs.push('missing material ' + m); });
    (c.nodes || []).forEach(n => { if (!info.nodes.includes(n)) errs.push('missing node ' + n); });
    (c.clips || []).forEach(n => { if (!info.clipNames.includes(n)) errs.push('missing clip ' + n); });
    if (info.tris > c.maxTris) errs.push('too many triangles ' + info.tris);
    console.log(`\n== ${name}.glb  ${(buf.length / 1024).toFixed(1)} KB  ${info.tris} tris  size(x,y,z)=${info.size} min=${info.min}`);
    console.log('  meshes   :', info.meshes.join(', '));
    console.log('  materials:', info.mats.join(', '));
    if (info.skinned) console.log('  skinned meshes:', info.skinned);
    if (info.clips.length) console.log('  clips    :', info.clips.join(', '));
    console.log(errs.length ? '  FAIL: ' + errs.join('; ') : '  OK');
    if (errs.length) failed++;
  }
  console.log(`\nTotal glb size: ${(totalBytes / 1024 / 1024).toFixed(2)} MB, ${files.length} files, ${failed} failing`);
  await browser.close();
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
