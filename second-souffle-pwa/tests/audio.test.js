/* Tests des adaptations du texte des voix off selon le genre de la voix. Lancer : node tests/audio.test.js */
const assert = require("assert"), fs = require("fs"), path = require("path");
const { adapt, FEMALE } = require("../tools/audio-fixes.js");
const csv = fs.readFileSync(path.join(__dirname, "..", "docs", "voiceover-manifest.csv"), "utf8");
let failures = 0;
function test(n, f) { try { f(); console.log("ok   " + n); } catch (e) { failures++; console.log("FAIL " + n + "\n     " + e.message); } }

test("la voix d'homme ne change aucun texte", () => { assert.strictEqual(adapt("Je suis Léo", "fr", "m"), "Je suis Léo"); });
test("la voix de femme change le prénom et les accords", () => {
  assert.strictEqual(adapt("Bienvenue. Je suis Léo, votre guide.", "fr", "f"), "Bienvenue. Je suis Léa, votre guide.");
  assert.strictEqual(adapt("Content de vous revoir.", "fr", "f"), "Contente de vous revoir.");
  assert.strictEqual(adapt("Obrigado por me dizer.", "pt", "f"), "Obrigada por me dizer.");
  assert.strictEqual(adapt("Sou um guia virtual, não um médico.", "pt", "f"), "Sou uma guia virtual, não uma médica.");
});
test("chaque adaptation correspond à une vraie phrase du manifeste (sinon elle ne sert à rien)", () => {
  Object.keys(FEMALE).forEach(l => FEMALE[l].forEach(p => assert.ok(csv.includes(p[0]), l + " : " + p[0])));
});
test("aucune phrase du manifeste ne garde « Léo » ou un accord masculin pour une voix de femme", () => {
  csv.split("\n").forEach(line => {
    const m = /^[^,]*,[^,]*,(fr|en|pt),(.*)$/.exec(line); if (!m) return;
    const t = adapt(m[2], m[1], "f");
    assert.ok(!/\bLéo\b/.test(t), "Léo restant : " + t.slice(0, 80));
    assert.ok(!/Content de vous revoir|Obrigado por me dizer|um guia virtual|seu guia virtual/.test(t), "accord masculin restant : " + t.slice(0, 80));
  });
});
console.log(failures ? "\n" + failures + " test(s) en échec" : "\nTous les tests passent");
process.exit(failures ? 1 : 0);
