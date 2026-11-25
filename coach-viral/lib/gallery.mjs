/* Galerie « Mes vidéos » : garde la liste des vidéos fabriquées par chaque utilisateur, même après un redémarrage. */
import { mkdir, readFile, writeFile, rm, stat } from "node:fs/promises";
import path from "node:path";

const NAME = /^[a-f0-9]{24}(?:-voix)?\.(?:mp4|mp3|wav)$/;

/* Noms des fichiers produits contenus dans le résultat d'une fabrication. */
export function filesOf(resultat) {
  if (!resultat || typeof resultat !== "object") return [];
  const out = new Set();
  for (const v of Object.values(resultat)) if (typeof v === "string" && NAME.test(v)) out.add(v);
  for (const c of resultat.clips || []) if (NAME.test(c?.video || "")) out.add(c.video);
  return [...out];
}

export class Gallery {
  constructor({ dir, filesDir, keepDays = 30 }) {
    this.dir = dir;
    this.filesDir = filesDir;
    this.keepDays = keepDays;
    this.locks = new Map();
  }
  file(uid) { return path.join(this.dir, uid + ".json"); }
  async read(uid) {
    try { return JSON.parse(await readFile(this.file(uid), "utf8")); } catch { return []; }
  }
  /* Écritures une par une pour un même utilisateur (deux vidéos peuvent finir en même temps). */
  async update(uid, change) {
    const prev = this.locks.get(uid) || Promise.resolve();
    const next = prev.then(async () => {
      const list = change(await this.read(uid));
      await mkdir(this.dir, { recursive: true });
      await writeFile(this.file(uid), JSON.stringify(list, null, 1));
      return list;
    });
    this.locks.set(uid, next.catch(() => {}));
    return next;
  }
  add(uid, entry) {
    const fichiers = filesOf(entry.resultat);
    if (!fichiers.length) return Promise.resolve(null);
    const item = { id: entry.id, type: entry.type, titre: String(entry.titre || "").slice(0, 120), date: new Date().toISOString(), fichiers, resultat: entry.resultat };
    return this.update(uid, (list) => [item, ...list.filter((x) => x.id !== item.id)].slice(0, 200));
  }
  async owns(uid, name) {
    return (await this.read(uid)).some((x) => x.fichiers.includes(name));
  }
  /* Liste les vidéos dont les fichiers existent encore. */
  async list(uid) {
    const out = [];
    for (const x of await this.read(uid)) {
      const ok = await Promise.all(x.fichiers.map((f) => stat(path.join(this.filesDir, f)).then(() => true, () => false)));
      if (ok.every(Boolean)) out.push(x);
    }
    return out;
  }
  async remove(uid, id) {
    let removed = null;
    await this.update(uid, (list) => list.filter((x) => (x.id === id ? ((removed = x), false) : true)));
    if (removed) await Promise.all(removed.fichiers.map((f) => rm(path.join(this.filesDir, f), { force: true })));
    return Boolean(removed);
  }
}
