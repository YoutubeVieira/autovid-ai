import { test, after } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { VoiceWorker } from "../lib/voiceworker.mjs";
import { mediaDuration } from "../lib/render.mjs";

const PY = process.env.PYTHON || "python3";
const w = new VoiceWorker(PY);
after(() => w.stop());

test("serveur de voix : plusieurs demandes à la suite, un seul processus", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "vw-"));
  await w.start();
  const pid = w.proc.pid;
  const outs = [0, 1, 2].map((i) => path.join(dir, `v${i}.wav`));
  await Promise.all(outs.map((sortie, i) => w.request({ moteur: "test", texte: "un deux trois ".repeat(i + 1), sortie })));
  for (const o of outs) assert.ok((await stat(o)).size > 1000);
  assert.ok((await mediaDuration(outs[2])) > (await mediaDuration(outs[0])));
  assert.equal(w.proc.pid, pid, "le même processus a servi toutes les demandes");
});

test("serveur de voix : une erreur n'arrête pas le serveur, et il redémarre après un arrêt", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "vw-"));
  await assert.rejects(w.request({ moteur: "inconnu", texte: "x", sortie: path.join(dir, "x.wav") }), /Moteur inconnu/);
  await w.request({ moteur: "test", texte: "encore là", sortie: path.join(dir, "a.wav") });
  w.proc.kill();
  await new Promise((r) => setTimeout(r, 200));
  await w.request({ moteur: "test", texte: "redémarré", sortie: path.join(dir, "b.wav") });
  assert.ok((await stat(path.join(dir, "b.wav"))).size > 1000);
});

test("serveur de voix introuvable : erreur claire", async () => {
  const bad = new VoiceWorker("python-qui-n-existe-pas");
  await assert.rejects(bad.start(), /introuvable/);
});
