/* Pilote du serveur de voix Python (voix/serveur_voix.py) : un processus par interpréteur Python,
   gardé en vie pour ne charger les modèles qu'une fois. Les demandes passent une par une. */
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline";
import { randomBytes } from "node:crypto";

const SCRIPT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "voix", "serveur_voix.py");

export class VoiceWorker {
  constructor(python, { script = SCRIPT, timeoutMs = 15 * 60_000 } = {}) {
    this.python = python;
    this.script = script;
    this.timeoutMs = timeoutMs;
    this.proc = null;
    this.ready = null;
    this.pending = new Map();
    this.chain = Promise.resolve();
    this.stderr = "";
  }

  start() {
    if (this.ready) return this.ready;
    this.ready = new Promise((resolve, reject) => {
      const p = spawn(this.python, [this.script], { stdio: ["pipe", "pipe", "pipe"], env: { ...process.env, PYTHONUTF8: "1", PYTHONIOENCODING: "utf-8" } });
      this.proc = p;
      p.stderr.on("data", (d) => { this.stderr = (this.stderr + d).slice(-4000); });
      const rl = createInterface({ input: p.stdout });
      rl.on("line", (line) => {
        let msg;
        try { msg = JSON.parse(line); } catch { return; }
        if (msg.pret) return resolve();
        const job = this.pending.get(msg.id);
        if (!job) return;
        this.pending.delete(msg.id);
        clearTimeout(job.timer);
        msg.ok ? job.resolve() : job.reject(new Error(msg.erreur || "Erreur de voix"));
      });
      const fail = (why) => {
        const err = new Error(why + (this.stderr ? " — " + this.stderr.trim().split(/\r?\n/).slice(-1)[0] : ""));
        reject(err);
        for (const job of this.pending.values()) { clearTimeout(job.timer); job.reject(err); }
        this.pending.clear();
        this.proc = null;
        this.ready = null;
      };
      p.on("error", (e) => fail("Serveur de voix introuvable : " + e.message));
      p.on("exit", (code) => fail("Serveur de voix arrêté (" + code + ")"));
    });
    return this.ready;
  }

  /* Envoie une demande ; la suivante attend la fin de celle-ci. */
  request(req) {
    const run = async () => {
      await this.start();
      const id = randomBytes(6).toString("hex");
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          this.pending.delete(id);
          reject(new Error("Voix trop longue à produire (délai dépassé)."));
          this.stop();
        }, this.timeoutMs);
        this.pending.set(id, { resolve, reject, timer });
        this.proc.stdin.write(JSON.stringify({ ...req, id }) + "\n");
      });
    };
    const result = this.chain.then(run, run);
    this.chain = result.catch(() => {});
    return result;
  }

  stop() {
    if (this.proc) { this.proc.kill(); this.proc = null; this.ready = null; }
  }
}

const workers = new Map();
export function workerFor(python) {
  if (!workers.has(python)) workers.set(python, new VoiceWorker(python));
  return workers.get(python);
}
export function stopAllWorkers() {
  for (const w of workers.values()) w.stop();
  workers.clear();
}
