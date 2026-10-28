/* Logique pure (sans écran) : composition de la séance, semaine, réponses du coach, tri d'urgence.
   Utilisable dans le navigateur et dans Node (tests). */
(function (g) {
  var D = g.SS.data;

  function norm(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function hits(e, picked) {
    return e.z.filter(function (z) { return picked && picked[z]; });
  }

  function goalWeights(goals) {
    var w = {};
    (goals || []).forEach(function (id) {
      var g = D.GOALS.filter(function (x) { return x.id === id; })[0];
      if (g) g.tags.forEach(function (tag, i) { w[tag] = (w[tag] || 0) + (i === 0 ? 2 : 1); });
    });
    return w;
  }
  function score(e, w) { return (e.t || []).reduce(function (s, tag) { return s + (w[tag] || 0); }, 0); }

  /* Une séance de 5 mouvements : échauffement, bas du corps, haut du corps, centre, étirements.
     Dans chaque catégorie, les exercices qui correspondent le mieux aux objectifs passent en premier ;
     le choix tourne selon le jour. Si l'exercice choisi sollicite une zone signalée, on prend le suivant. */
  function buildSession(picked, dayIndex, goals) {
    var slots = ["warm", "lower", "upper", "core", "stretch"], w = goalWeights(goals);
    return slots.map(function (cat) {
      var pool = D.EX.filter(function (e) { return e.cat === cat && e.v1; });
      var sorted = pool.map(function (e, i) { return { e: e, i: i, s: score(e, w) }; })
        .sort(function (a, b) { return b.s - a.s || a.i - b.i; }).map(function (x) { return x.e; });
      var max = score(sorted[0], w);
      var top = sorted.filter(function (e) { return score(e, w) === max; });
      if (top.length < 2) top = sorted.slice(0, 2);
      var preferred = top[((dayIndex % top.length) + top.length) % top.length];
      var order = [preferred].concat(sorted.filter(function (e) { return e !== preferred; }));
      var chosen = null;
      for (var k = 0; k < order.length && !chosen; k++) if (!hits(order[k], picked).length) chosen = order[k];
      if (!chosen) {
        chosen = D.EX.filter(function (e) { return e.cat === cat && !hits(e, picked).length; })[0] || D.BY_ID["respiration"];
      }
      return { ex: chosen, swapped: chosen !== preferred, was: chosen !== preferred ? preferred : null };
    });
  }

  /* Jours de lumière conseillés par semaine : moyenne des objectifs choisis (3 par défaut). */
  function defaultTarget(goals) {
    var ws = (goals || []).map(function (id) { var g = D.GOALS.filter(function (x) { return x.id === id; })[0]; return g ? g.week : null; })
      .filter(function (x) { return x; });
    if (!ws.length) return 3;
    return Math.round(ws.reduce(function (a, b) { return a + b; }, 0) / ws.length);
  }

  /* Repères alimentaires cochés pour une date. */
  function foodCount(food, key) {
    var d = (food || {})[key] || {};
    return D.FOOD_CHECKS.filter(function (c) { return d[c]; }).length;
  }
  function foodWeek(food, today) {
    var days = weekDays({}, today), n = 0;
    days.forEach(function (d) { if (foodCount(food, d.key) >= 3) n++; });
    return n;
  }
  function weightSummary(list) {
    if (!list || !list.length) return null;
    var sorted = list.slice().sort(function (a, b) { return a.d < b.d ? -1 : 1; });
    var first = sorted[0].kg, last = sorted[sorted.length - 1].kg;
    return { first: first, last: last, delta: Math.round((last - first) * 10) / 10, n: sorted.length };
  }
  function parseWeight(text) {
    var v = parseFloat(String(text).replace(",", "."));
    return isFinite(v) && v >= 25 && v <= 300 ? Math.round(v * 10) / 10 : null;
  }

  function dateKey(d) {
    var m = d.getMonth() + 1, day = d.getDate();
    return d.getFullYear() + "-" + (m < 10 ? "0" : "") + m + "-" + (day < 10 ? "0" : "") + day;
  }

  function dayOfYear(d) {
    var start = new Date(d.getFullYear(), 0, 0);
    return Math.floor((d - start) / 86400000);
  }

  /* Les 7 jours de la semaine (lundi en premier) avec leur état : séance, repos, aujourd'hui, à venir. */
  function weekDays(log, today) {
    var dow = (today.getDay() + 6) % 7;
    var monday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - dow);
    var out = [];
    for (var i = 0; i < 7; i++) {
      var d = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + i);
      var key = dateKey(d);
      var st = "";
      if (log[key] === "s") st = "s";
      else if (log[key] === "r") st = "r";
      else if (key === dateKey(today)) st = "now";
      else if (d > today) st = "next";
      out.push({ key: key, dow: i, status: st });
    }
    return out;
  }

  function lightCount(days) {
    return days.filter(function (d) { return d.status === "s" || d.status === "r"; }).length;
  }

  function monthCounts(log, today) {
    var prefix = dateKey(today).slice(0, 7);
    var s = 0, r = 0;
    Object.keys(log).forEach(function (k) {
      if (k.indexOf(prefix) !== 0) return;
      if (log[k] === "s") s++;
      else if (log[k] === "r") r++;
    });
    return { s: s, r: r };
  }

  var RE_KNEE = /genou|knee|joelho/;
  var RE_BACK = /\bdos\b|mal au dos|lombaire|back|costas|lombar/;
  var RE_TIME = /temps|time|minute|tempo|pressa/;
  var RE_SLEEP = /dor[mts]|durm|sommeil|fatigu|sleep|tired|sono|cansa/;
  var RE_BELLY = /ventre|poids|belly|weight|barriga|peso/;
  var RE_FOOD = /manger|repas|aliment|nourrit|eat|meal|food|diet|comer|refei|aliment/;
  var RE_URGENT = /douleur forte|poitrine|vertige|malaise|engourdi|fourmill|chest|dizz|numb|tingl|severe pain|peito|tontur|dormencia|formigamento|dor forte/;

  /* Réponse du coach IA (mode démonstration) : clé de texte et zone à ajouter à la carte. */
  function replyFor(text) {
    var n = norm(text);
    if (RE_KNEE.test(n)) return { key: "ai.r.knee", zone: "genoux" };
    if (RE_BACK.test(n)) return { key: "ai.r.back", zone: "dos" };
    if (RE_TIME.test(n)) return { key: "ai.r.time", zone: null };
    if (RE_SLEEP.test(n)) return { key: "ai.r.sleep", zone: null };
    if (RE_FOOD.test(n)) return { key: "ai.r.food", zone: null };
    if (RE_BELLY.test(n)) return { key: "ai.r.belly", zone: null };
    return { key: "ai.r.default", zone: null };
  }

  function isUrgent(text) {
    return RE_URGENT.test(norm(text));
  }

  function topicOf(text) {
    var n = norm(text);
    if (RE_KNEE.test(n)) return "genoux";
    return RE_BACK.test(n) ? "dos" : "genoux";
  }


  /* ---------- lecteur de séance (machine d'états) ---------- */
  var DURS = [20, 30, 45, 60, 90];
  var LEVELS = {
    soft: { dur: 30, rest: 20, rounds: 1 },
    std: { dur: 45, rest: 10, rounds: 2 },
    hard: { dur: 60, rest: 10, rounds: 3 }
  };

  function levelOf(cfg) {
    for (var k in LEVELS) {
      var l = LEVELS[k];
      if (l.dur === cfg.dur && l.rest === cfg.rest && l.rounds === cfg.rounds) return k;
    }
    return "custom";
  }
  function sequence(items, rounds) {
    var out = [];
    for (var r = 0; r < rounds; r++) out = out.concat(items);
    return out;
  }
  /* Durée totale en secondes : exercices + pauses entre deux exercices (pas après le dernier). */
  function totalSeconds(n, dur, rest) { return n * dur + Math.max(0, n - 1) * rest; }
  function shiftDur(dur, dir) {
    var i = DURS.indexOf(dur);
    if (i < 0) i = 2;
    return DURS[Math.max(0, Math.min(DURS.length - 1, i + dir))];
  }

  function newPlayer(seq, dur, rest) {
    return { seq: seq, idx: 0, phase: "work", left: dur, paused: false, dur: dur, rest: rest, done: false };
  }
  function startWork(p, idx) { p.idx = idx; p.phase = "work"; p.left = p.dur; return p; }
  function advance(p) {
    if (p.phase === "work") {
      if (p.idx >= p.seq.length - 1) { p.done = true; return p; }
      if (p.rest > 0) { p.phase = "rest"; p.left = p.rest; return p; }
      return startWork(p, p.idx + 1);
    }
    return startWork(p, p.idx + 1);
  }
  function tick(p) {
    if (p.paused || p.done) return p;
    p.left--;
    if (p.left <= 0) advance(p);
    return p;
  }
  /* Suivant : va directement au prochain exercice (saute aussi la pause en cours). */
  function next(p) {
    if (p.idx >= p.seq.length - 1) { p.done = true; return p; }
    return startWork(p, p.idx + 1);
  }
  /* Précédent : pendant une pause, revient à l'exercice qui vient de finir ; sinon exercice d'avant. */
  function prev(p) {
    if (p.phase === "rest") return startWork(p, p.idx);
    return startWork(p, Math.max(0, p.idx - 1));
  }
  function redo(p) { return p.phase === "rest" ? startWork(p, p.idx) : startWork(p, p.idx); }
  function plus(p, s) { p.left = Math.min(300, p.left + (s || 10)); return p; }
  function jump(p, i) { return startWork(p, Math.max(0, Math.min(p.seq.length - 1, i))); }
  function togglePause(p) { p.paused = !p.paused; return p; }

  g.SS.logic = {
    DURS: DURS, LEVELS: LEVELS, levelOf: levelOf, sequence: sequence, totalSeconds: totalSeconds, shiftDur: shiftDur,
    newPlayer: newPlayer, tick: tick, next: next, prev: prev, redo: redo, plus: plus, jump: jump, togglePause: togglePause,
    buildSession: buildSession, goalWeights: goalWeights, defaultTarget: defaultTarget, foodCount: foodCount, foodWeek: foodWeek, weightSummary: weightSummary, parseWeight: parseWeight, hits: hits, dateKey: dateKey, dayOfYear: dayOfYear,
    weekDays: weekDays, lightCount: lightCount, monthCounts: monthCounts,
    replyFor: replyFor, isUrgent: isUrgent, topicOf: topicOf
  };
})(typeof window !== "undefined" ? window : globalThis);
