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

  /* Une séance de 5 mouvements : échauffement, bas du corps, haut du corps, centre, étirements.
     Pour chaque créneau, on part d'un exercice qui change selon le jour, puis on le remplace
     par le suivant de la même catégorie si une zone signalée est sollicitée. */
  function buildSession(picked, dayIndex) {
    var slots = ["warm", "lower", "upper", "core", "stretch"];
    return slots.map(function (cat) {
      var pool = D.EX.filter(function (e) { return e.cat === cat && e.v1; });
      var start = ((dayIndex % pool.length) + pool.length) % pool.length;
      var preferred = pool[start];
      var chosen = null;
      for (var k = 0; k < pool.length && !chosen; k++) {
        var cand = pool[(start + k) % pool.length];
        if (!hits(cand, picked).length) chosen = cand;
      }
      if (!chosen) {
        chosen = D.EX.filter(function (e) { return e.cat === cat && !hits(e, picked).length; })[0] || D.BY_ID["respiration"];
      }
      return { ex: chosen, swapped: chosen !== preferred, was: chosen !== preferred ? preferred : null };
    });
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
  var RE_URGENT = /douleur forte|poitrine|vertige|malaise|engourdi|fourmill|chest|dizz|numb|tingl|severe pain|peito|tontur|dormencia|formigamento|dor forte/;

  /* Réponse du coach IA (mode démonstration) : clé de texte et zone à ajouter à la carte. */
  function replyFor(text) {
    var n = norm(text);
    if (RE_KNEE.test(n)) return { key: "ai.r.knee", zone: "genoux" };
    if (RE_BACK.test(n)) return { key: "ai.r.back", zone: "dos" };
    if (RE_TIME.test(n)) return { key: "ai.r.time", zone: null };
    if (RE_SLEEP.test(n)) return { key: "ai.r.sleep", zone: null };
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
    buildSession: buildSession, hits: hits, dateKey: dateKey, dayOfYear: dayOfYear,
    weekDays: weekDays, lightCount: lightCount, monthCounts: monthCounts,
    replyFor: replyFor, isUrgent: isUrgent, topicOf: topicOf
  };
})(typeof window !== "undefined" ? window : globalThis);
