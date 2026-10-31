#!/usr/bin/env node
/* Tests sans réseau ni navigateur : WAV, découpe des sous-titres, validité des projets. Usage : node tools/test.mjs */
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { root, wav, readWav, wavSeconds, chunkWords, chunkTimings } from "./lib.mjs";

const pcm = Buffer.alloc(24000 * 2); // 1 s de silence à 24 kHz
assert.strictEqual(wavSeconds(wav(pcm, 24000)), 1);
assert.strictEqual(readWav(wav(pcm, 22050)).rate, 22050);

assert.deepStrictEqual(chunkWords("Em maio de 1940, a Alemanha invade a França."), ["Em maio de", "1940, a Alemanha", "invade a França."]);
const t = chunkTimings(["um dois", "três"], 3);
assert.strictEqual(t[0].from, 0);
assert.ok(Math.abs(t.at(-1).to - 3) < 0.01, "les sous-titres couvrent toute la durée");
assert.ok(t.every((c, i) => i === 0 || c.from >= t[i - 1].to - 1e-9), "sous-titres ordonnés");

const geo = JSON.parse(fs.readFileSync(path.join(root, "public/geo/europe.json"), "utf8"));
const ids = new Set(geo.features.map(f => f.properties.id));

for (const f of fs.readdirSync(path.join(root, "projects")).filter(f => f.endsWith(".json"))) {
  const p = JSON.parse(fs.readFileSync(path.join(root, "projects", f), "utf8"));
  const seen = new Set();
  for (const s of p.scenes) {
    assert.ok(!seen.has(s.id), f + " : scène en double " + s.id); seen.add(s.id);
    assert.ok(s.text && s.camera && s.camera.zoom > 0, f + " : scène " + s.id + " incomplète");
    for (const iso of Object.keys(s.fills || {})) assert.ok(ids.has(iso), f + " : pays inconnu " + iso);
  }
}
console.log("Tests OK");
