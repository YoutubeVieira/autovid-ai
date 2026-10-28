/* Tests de la logique pure. Lancer : node tests/logic.test.js */
var assert = require("assert");
require("../js/i18n.js");
require("../js/data.js");
require("../js/logic.js");

var SS = globalThis.SS, L = SS.logic, D = SS.data, I = SS.i18n;
var failures = 0;
function test(name, fn) {
  try { fn(); console.log("ok   " + name); }
  catch (e) { failures++; console.log("FAIL " + name + "\n     " + e.message); }
}

test("28 exercices, 19 pour la version 1", function () {
  assert.strictEqual(D.EX.length, 28);
  assert.strictEqual(D.EX.filter(function (e) { return e.v1; }).length, 19);
});

test("chaque exercice a un nom dans les trois langues", function () {
  D.EX.forEach(function (e) {
    ["fr", "en", "pt"].forEach(function (l) { assert.ok(e.n[l], e.id + " sans nom " + l); });
  });
});

test("chaque exercice de la version 1 a une consigne dans les trois langues", function () {
  D.EX.filter(function (e) { return e.v1; }).forEach(function (e) {
    ["fr", "en", "pt"].forEach(function (l) { assert.ok(e.c[l], e.id + " sans consigne " + l); });
  });
});

test("toutes les clés de texte existent dans les trois langues", function () {
  Object.keys(I.S).forEach(function (k) {
    assert.strictEqual(I.S[k].length, 3, k);
    I.S[k].forEach(function (v, i) { assert.ok(v !== undefined && v !== "", k + " langue " + i); });
  });
});

test("aucune zone signalée : 5 mouvements, aucun remplacé", function () {
  var s = L.buildSession({}, 3);
  assert.strictEqual(s.length, 5);
  assert.strictEqual(s.filter(function (x) { return x.swapped; }).length, 0);
});

test("une zone signalée n'est jamais sollicitée par la séance", function () {
  D.ZONES.forEach(function (z) {
    for (var day = 0; day < 10; day++) {
      var picked = {}; picked[z] = true;
      L.buildSession(picked, day).forEach(function (x) {
        assert.ok(x.ex.z.indexOf(z) < 0, x.ex.id + " sollicite " + z + " le jour " + day);
      });
    }
  });
});

test("toutes les zones signalées : la séance reste possible et sans zone sensible", function () {
  var picked = {};
  D.ZONES.forEach(function (z) { picked[z] = true; });
  var s = L.buildSession(picked, 0);
  assert.strictEqual(s.length, 5);
  s.forEach(function (x) { assert.strictEqual(L.hits(x.ex, picked).length, 0, x.ex.id); });
});

test("un exercice remplacé indique l'exercice d'origine", function () {
  var s = L.buildSession({ genoux: true }, 0);
  s.forEach(function (x) { if (x.swapped) assert.ok(x.was && x.was !== x.ex); });
});

test("semaine : lundi en premier, séance et repos comptent comme lumière", function () {
  var today = new Date(2026, 9, 28); // mercredi 28 octobre 2026
  var log = {}; log["2026-10-26"] = "s"; log["2026-10-27"] = "r";
  var w = L.weekDays(log, today);
  assert.strictEqual(w.length, 7);
  assert.strictEqual(w[0].key, "2026-10-26");
  assert.strictEqual(w[2].status, "now");
  assert.strictEqual(w[3].status, "next");
  assert.strictEqual(L.lightCount(w), 2);
});

test("décompte du mois", function () {
  var log = { "2026-10-02": "s", "2026-10-05": "s", "2026-10-06": "r", "2026-09-30": "s" };
  var c = L.monthCounts(log, new Date(2026, 9, 28));
  assert.strictEqual(c.s, 2);
  assert.strictEqual(c.r, 1);
});

test("réponses du coach dans les trois langues", function () {
  assert.strictEqual(L.replyFor("J'ai mal au genou").key, "ai.r.knee");
  assert.strictEqual(L.replyFor("My knee hurts").key, "ai.r.knee");
  assert.strictEqual(L.replyFor("Meu joelho dói").key, "ai.r.knee");
  assert.strictEqual(L.replyFor("Je manque de temps").key, "ai.r.time");
  assert.strictEqual(L.replyFor("I'm short on time").key, "ai.r.time");
  assert.strictEqual(L.replyFor("Estou sem tempo").key, "ai.r.time");
  assert.strictEqual(L.replyFor("Je dors mal").key, "ai.r.sleep");
  assert.strictEqual(L.replyFor("I sleep badly").key, "ai.r.sleep");
  assert.strictEqual(L.replyFor("Durmo mal").key, "ai.r.sleep");
  assert.strictEqual(L.replyFor("Je veux perdre du ventre").key, "ai.r.belly");
  assert.strictEqual(L.replyFor("Quero perder barriga").key, "ai.r.belly");
  assert.strictEqual(L.replyFor("J'ai mal au dos").key, "ai.r.back");
  assert.strictEqual(L.replyFor("bonjour").key, "ai.r.default");
});

test("tri d'urgence : symptômes graves reconnus, douleur ordinaire non", function () {
  assert.ok(L.isUrgent("J'ai une douleur forte dans la poitrine"));
  assert.ok(L.isUrgent("I feel dizzy"));
  assert.ok(L.isUrgent("Sinto formigamento no braço"));
  assert.ok(!L.isUrgent("Mon genou tire quand je descends les escaliers"));
});

test("sujet de la fiche : genou par défaut, dos si mentionné", function () {
  assert.strictEqual(L.topicOf("mon dos tire"), "dos");
  assert.strictEqual(L.topicOf("mon genou tire"), "genoux");
  assert.strictEqual(L.topicOf("ça tire"), "genoux");
});


test("durée totale : pauses seulement entre deux exercices", function () {
  assert.strictEqual(L.totalSeconds(10, 45, 10), 540);
  assert.strictEqual(L.totalSeconds(5, 30, 0), 150);
});

test("niveaux : reconnaissance et réglage personnalisé", function () {
  assert.strictEqual(L.levelOf({ dur: 45, rest: 10, rounds: 2 }), "std");
  assert.strictEqual(L.levelOf({ dur: 30, rest: 20, rounds: 1 }), "soft");
  assert.strictEqual(L.levelOf({ dur: 90, rest: 0, rounds: 3 }), "custom");
});

test("durées proposées : 20, 30, 45, 60, 90 secondes, avec bornes", function () {
  assert.deepStrictEqual(L.DURS, [20, 30, 45, 60, 90]);
  assert.strictEqual(L.shiftDur(45, 1), 60);
  assert.strictEqual(L.shiftDur(30, -1), 20);
  assert.strictEqual(L.shiftDur(20, -1), 20);
  assert.strictEqual(L.shiftDur(90, 1), 90);
});

function mk(n, dur, rest) { var seq = []; for (var i = 0; i < n; i++) seq.push({ ex: D.EX[i] }); return L.newPlayer(seq, dur, rest); }

test("lecteur : exercice, pause, exercice suivant, fin", function () {
  var p = mk(2, 3, 2);
  for (var i = 0; i < 3; i++) L.tick(p);
  assert.strictEqual(p.phase, "rest"); assert.strictEqual(p.left, 2);
  L.tick(p); L.tick(p);
  assert.strictEqual(p.phase, "work"); assert.strictEqual(p.idx, 1); assert.strictEqual(p.left, 3);
  for (i = 0; i < 3; i++) L.tick(p);
  assert.ok(p.done);
});

test("lecteur : sans pause, enchaîne directement", function () {
  var p = mk(2, 2, 0);
  L.tick(p); L.tick(p);
  assert.strictEqual(p.phase, "work"); assert.strictEqual(p.idx, 1);
});

test("lecteur : la pause (mise en pause) arrête le décompte", function () {
  var p = mk(2, 5, 2);
  L.togglePause(p); L.tick(p); L.tick(p);
  assert.strictEqual(p.left, 5);
  L.togglePause(p); L.tick(p);
  assert.strictEqual(p.left, 4);
});

test("lecteur : suivant saute l'exercice et la pause", function () {
  var p = mk(3, 5, 5);
  L.next(p);
  assert.strictEqual(p.idx, 1); assert.strictEqual(p.phase, "work");
  for (var i = 0; i < 5; i++) L.tick(p);
  assert.strictEqual(p.phase, "rest");
  L.next(p);
  assert.strictEqual(p.idx, 2); assert.strictEqual(p.phase, "work");
  L.next(p);
  assert.ok(p.done);
});

test("lecteur : précédent revient en arrière, refaire recommence", function () {
  var p = mk(3, 5, 5);
  L.jump(p, 2); L.tick(p);
  L.prev(p);
  assert.strictEqual(p.idx, 1); assert.strictEqual(p.left, 5);
  L.prev(p); L.prev(p);
  assert.strictEqual(p.idx, 0);
  L.tick(p); L.tick(p); L.redo(p);
  assert.strictEqual(p.idx, 0); assert.strictEqual(p.left, 5);
});

test("lecteur : précédent pendant une pause revient à l'exercice qui vient de finir", function () {
  var p = mk(3, 2, 4);
  L.tick(p); L.tick(p);
  assert.strictEqual(p.phase, "rest");
  L.prev(p);
  assert.strictEqual(p.phase, "work"); assert.strictEqual(p.idx, 0);
});

test("lecteur : +10 s ajoute du temps, plafonné à 300 s ; saut borné", function () {
  var p = mk(3, 30, 5);
  L.plus(p, 10);
  assert.strictEqual(p.left, 40);
  p.left = 295; L.plus(p, 10);
  assert.strictEqual(p.left, 300);
  L.jump(p, 99); assert.strictEqual(p.idx, 2);
  L.jump(p, -4); assert.strictEqual(p.idx, 0);
});

test("séquence : les tours répètent les 5 exercices", function () {
  var items = L.buildSession({}, 0);
  assert.strictEqual(L.sequence(items, 3).length, 15);
});

console.log(failures ? "\n" + failures + " test(s) en échec" : "\nTous les tests passent");
process.exit(failures ? 1 : 0);
