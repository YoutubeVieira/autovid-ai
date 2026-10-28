/* Second Souffle : interface. Tout l'état utilisateur reste sur l'appareil (localStorage). */
(function () {
  "use strict";
  var SS = window.SS, I = SS.i18n, D = SS.data, L = SS.logic;
  var t = I.t, pick = I.pick;
  var KEY = "ss.v1";

  /* ---------- état ---------- */
  function fresh() {
    return {
      lang: null, amb: "commun", tz: 1, onboarded: false, age: "a", goal: "energy",
      zones: {}, log: {}, demo: "f", plan: "year", addon: false, dur: 45, rest: 10, rounds: 2, sound: true,
      pro: { msgs: [], relay: ["on", "", "", ""], replied: false, topic: "genoux", waiting: false }
    };
  }
  function load() {
    var s = fresh();
    try {
      var raw = localStorage.getItem(KEY);
      if (raw) { var o = JSON.parse(raw); for (var k in o) s[k] = o[k]; }
    } catch (e) { /* stockage indisponible : l'app fonctionne sans */ }
    return s;
  }
  var S = load();
  function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* ignoré */ } }

  var ui = {
    screen: S.onboarded ? "home" : "welcome", coachTab: "ai", ai: [], libF: "all",
    layer: "muscles", azone: null, sess: null, angle: "face", timer: null, resetAsk: false,
    fbMsg: "", toastTimer: null, custom: false
  };

  I.setLang(S.lang || I.guess(navigator.language));

  /* ---------- utilitaires ---------- */
  function $(sel, root) { return (root || document).querySelector(sel); }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function zlist(zs) { return zs.map(function (z) { return t("zone." + z).toLowerCase(); }).join(", "); }
  function pickedList() { return D.ZONES.filter(function (z) { return S.zones[z]; }); }
  function today() { return new Date(); }
  function exName(e) { return pick(e.n); }

  function toast(msg) {
    var old = $(".toast"); if (old) old.remove();
    var d = document.createElement("div");
    d.className = "toast"; d.setAttribute("role", "status"); d.textContent = msg;
    document.body.appendChild(d);
    clearTimeout(ui.toastTimer);
    ui.toastTimer = setTimeout(function () { d.remove(); }, 3200);
  }

  function applyPrefs() {
    var r = document.documentElement;
    r.setAttribute("data-amb", S.amb);
    r.lang = I.state.lang === "pt" ? "pt-BR" : I.state.lang;
    r.style.setProperty("--tz", S.tz);
    document.title = t("app.name");
  }

  /* ---------- briques d'écran ---------- */
  function chip(label, act, v, pressed) {
    return '<button class="chip" data-act="' + act + '" data-v="' + esc(v) + '" aria-pressed="' + !!pressed + '">' + esc(label) + "</button>";
  }
  function guideRow(sub) {
    return '<div class="guide"><img src="img/leo.webp" alt=""><p><b>' + t("guide.name") + "</b><br><span class=\"muted\">" + sub + "</span></p></div>";
  }
  function hero(src, alt) { return '<img class="hero" src="img/' + src + '.webp" alt="' + esc(alt) + '">'; }
  function backChip(to) { return '<button class="chip back" data-act="go" data-v="' + to + '">‹ ' + t("common.back") + "</button>"; }

  var POS = {
    cou: [[100, 70]], epaules: [[62, 98], [138, 98]], dos: [[100, 135]],
    poignets: [[34, 170], [166, 170]], hanches: [[100, 182]], genoux: [[82, 250], [118, 250]]
  };

  function bodyMap() {
    var s = '<svg class="body" viewBox="0 0 200 300" role="img" aria-label="' + esc(t("body.title")) + '"><g class="sil">' +
      '<circle cx="100" cy="38" r="20"/><rect x="72" y="62" width="56" height="130" rx="26"/><rect x="40" y="76" width="22" height="100" rx="11"/><rect x="138" y="76" width="22" height="100" rx="11"/>' +
      '<rect x="74" y="190" width="24" height="96" rx="12"/><rect x="102" y="190" width="24" height="96" rx="12"/></g>';
    D.ZONES.forEach(function (z) {
      POS[z].forEach(function (p) {
        s += '<circle class="z' + (S.zones[z] ? " on" : "") + '" data-act="zone" data-v="' + z + '" cx="' + p[0] + '" cy="' + p[1] + '" r="13"/>';
      });
    });
    s += '</svg><div class="chips" style="margin-top:8px">';
    D.ZONES.forEach(function (z) { s += chip(t("zone." + z), "zone", z, S.zones[z]); });
    return s + "</div>";
  }

  function ambCards() {
    return '<div class="ambs">' + D.AMBS.map(function (a) {
      return '<button class="ambcard" data-act="amb" data-v="' + a.id + '" aria-pressed="' + (S.amb === a.id) + '"><span class="sws">' +
        a.sw.map(function (h) { return '<i style="background:' + h + '"></i>'; }).join("") +
        '</span><span><b>' + t("amb." + a.id) + '</b><br><span class="muted small">' + t("amb." + a.id + ".sub") + "</span></span></button>";
    }).join("") + "</div>";
  }

  function swapLabel(items) {
    var n = items.filter(function (x) { return x.swapped; }).length;
    return n === 0 ? t("plan.adapted") : n === 1 ? t("plan.one") : t("plan.many", { n: n });
  }

  function cfg() { return { dur: S.dur, rest: S.rest, rounds: S.rounds }; }
  function minutes() { return Math.max(1, Math.round(L.totalSeconds(5 * S.rounds, S.dur, S.rest) / 60)); }
  function levelBlock(forceOpen) {
    var cur = L.levelOf(cfg()), open = forceOpen || ui.custom || cur === "custom";
    var h = '<div class="stack tight"><b>' + t("lvl.title") + '</b><div class="chips">' +
      ["soft", "std", "hard"].map(function (k) { return chip(t("lvl." + k), "level", k, cur === k); }).join("") +
      (forceOpen ? "" : chip(t("lvl.edit"), "custom", "1", open)) + "</div>" +
      '<p class="muted small">' + t("lvl.sub", { d: S.dur, r: S.rest, n: S.rounds, m: minutes() }) + "</p>";
    if (open) {
      h += '<b class="small">' + t("set.durLabel") + '</b><div class="chips">' + L.DURS.map(function (d) { return chip(t("set.sec", { n: d }), "dur", d, S.dur === d); }).join("") + "</div>" +
        '<b class="small">' + t("set.restLabel") + '</b><div class="chips">' + [0, 10, 20, 30].map(function (r) { return chip(r === 0 ? t("set.none") : t("set.sec", { n: r }), "restlen", r, S.rest === r); }).join("") + "</div>" +
        '<b class="small">' + t("set.roundsLabel") + '</b><div class="chips">' + [1, 2, 3].map(function (n) { return chip(String(n), "rounds", n, S.rounds === n); }).join("") + "</div>";
    }
    return h + "</div>";
  }

  /* ---------- écrans ---------- */
  var SCREENS = {};
  var SKY = { plan: 1, home: 1, done: 1, paywall: 1 };
  var TABS = { home: 1, body: 1, coach: 1, path: 1, lib: 1, anat: 1 };

  SCREENS.welcome = function () {
    return '<div class="intro"><div class="kicker">' + t("app.name") + "</div><h1>" + t("welcome.title") + "</h1><p>" + t("welcome.sub") + "</p></div>" +
      '<div><b class="small">' + t("welcome.lang") + '</b><div class="chips" style="margin-top:8px">' +
      I.LANGS.map(function (l) { return chip(t("lang.name." + l), "lang", l, I.state.lang === l); }).join("") + "</div></div>" +
      '<div class="bottom"><button class="btn" data-act="go" data-v="amb">' + t("welcome.start") + "</button></div>";
  };

  SCREENS.amb = function () {
    return hero("ecoute", t("guide.name")) + '<span class="step">' + t("amb.step") + "</span><h2>" + t("amb.title") + "</h2><p class=\"muted\">" + t("amb.sub") + "</p>" +
      ambCards() + '<button class="btn bottom" data-act="go" data-v="q1">' + t("common.continue") + "</button>";
  };

  SCREENS.q1 = function () {
    return '<div class="bar"><i class="on"></i><i></i><i></i></div><span class="step">' + t("q.n", { n: 1 }) + "</span>" + guideRow(t("guide.illu")) +
      "<h2>" + t("q1.title") + '</h2><div class="chips">' +
      chip(t("q1.a"), "age", "a", S.age === "a") + chip(t("q1.b"), "age", "b", S.age === "b") + chip(t("q1.c"), "age", "c", S.age === "c") +
      '</div><p class="muted">' + t("q1.note") + '</p><button class="btn bottom" data-act="go" data-v="q2">' + t("common.continue") + "</button>";
  };

  SCREENS.q2 = function () {
    var g = ["energy", "back", "weight", "muscle"];
    return '<div class="bar"><i class="on"></i><i class="on"></i><i></i></div><span class="step">' + t("q.n", { n: 2 }) + "</span><h2>" + t("q2.title") + '</h2><div class="chips">' +
      g.map(function (k) { return chip(t("q2." + k), "goal", k, S.goal === k); }).join("") +
      '</div><p class="muted">' + t("q2.note") + '</p><button class="btn bottom" data-act="go" data-v="q3">' + t("common.continue") + "</button>";
  };

  SCREENS.q3 = function () {
    return '<div class="bar"><i class="on"></i><i class="on"></i><i class="on"></i></div><span class="step">' + t("q.n", { n: 3 }) + "</span><h2>" + t("q3.title") + "</h2><p class=\"muted\">" + t("q3.sub") + "</p>" +
      bodyMap() + '<button class="btn bottom" data-act="finishOnboarding">' + t("q3.go") + "</button>";
  };

  function sessionItems() { return L.buildSession(S.zones, L.dayOfYear(today())); }

  SCREENS.plan = function () {
    var items = sessionItems();
    return hero("bras-leves", t("guide.name")) + '<span class="step ink">' + t("plan.ready") + "</span><h2>" + t("plan.title") + "</h2>" +
      '<div class="card solid"><div class="tags"><span class="tag">' + t("plan.min", { n: minutes() }) + '</span><span class="tag">' + t("plan.nogear") + '</span><span class="tag ok">' + swapLabel(items) + "</span></div><ol class=\"plist\">" +
      items.map(function (x) {
        return "<li><b>" + esc(exName(x.ex)) + "</b>" + (x.swapped ? '<br><span class="swap">' + t("plan.replaces", { x: esc(exName(x.was)) }) + "</span>" : "") + "</li>";
      }).join("") + "</ol></div>" + '<div class="card solid">' + levelBlock(false) + "</div>" +
      '<div class="bottom stack"><button class="btn" data-act="startSession">' + t("plan.start") + '</button><button class="btn ghost solid" data-act="go" data-v="home">' + t("plan.later") + "</button></div>";
  };

  function arcSvg(n) {
    var p = Math.min(1, n / 4), th = Math.PI * (1 - p);
    var x = (180 + 150 * Math.cos(th)).toFixed(1), y = (165 - 150 * Math.sin(th)).toFixed(1);
    return '<div class="arc" aria-hidden="true"><svg viewBox="0 0 360 195" preserveAspectRatio="xMidYMid meet">' +
      '<path d="M30 165 A150 150 0 0 1 330 165" fill="none" stroke="var(--card)" stroke-opacity=".6" stroke-width="3" stroke-dasharray="2 8" stroke-linecap="round"/>' +
      (p > 0 ? '<path d="M30 165 A150 150 0 0 1 ' + x + " " + y + '" fill="none" stroke="var(--sun)" stroke-width="5" stroke-linecap="round"/>' : "") +
      '<circle cx="' + x + '" cy="' + y + '" r="26" fill="var(--sun)" opacity=".25"/><circle cx="' + x + '" cy="' + y + '" r="16" fill="var(--sun)"/></svg></div>';
  }

  SCREENS.home = function () {
    var items = sessionItems(), key = L.dateKey(today());
    var n = L.lightCount(L.weekDays(S.log, today()));
    var rested = S.log[key] === "r";
    return '<div class="row between"><div class="hello">' + t("home.hello") + '</div><button class="chip" data-act="go" data-v="settings">' + t("home.settings") + "</button></div>" +
      arcSvg(n) +
      '<div class="today"><span class="step">' + t("home.today") + "</span><h3>" + t("plan.title") + '</h3><div class="tags"><span class="tag">' + t("plan.min", { n: minutes() }) + '</span><span class="tag ok">' + swapLabel(items) + "</span></div>" +
      '<button class="btn" data-act="startSession">' + t("home.start") + "</button></div>" +
      '<div class="today tight"><div class="row between"><span>' + t("home.tired") + '</span><button class="chip" data-act="rest"' + (rested ? " disabled" : "") + ">" + (rested ? t("home.restDone") : t("home.rest")) + "</button></div><p class=\"muted small\">" + t("home.restNote") + "</p></div>";
  };

  SCREENS.player = function () {
    var p = ui.sess, cur = p.seq[p.idx], e = cur.ex, rest = p.phase === "rest";
    var dots = p.seq.map(function (_, i) {
      var c = i < p.idx || (rest && i === p.idx) ? "done" : i === p.idx ? "on" : "";
      return '<button class="dot ' + c + '" data-act="jump" data-v="' + i + '" aria-label="' + esc(t("player.jump", { n: i + 1 })) + '"></button>';
    }).join("");
    var round = t("player.round", { a: Math.floor(p.idx / 5) + 1, b: S.rounds });
    var orb = '<div class="orbwrap"><div class="orb' + (p.paused ? " paused" : "") + '" id="orb"><div><b id="count">' + p.left + "</b><span>" + t("player.seconds") + "</span></div></div></div>";
    if (rest) {
      var nx = p.seq[p.idx + 1].ex;
      return '<div class="dots">' + dots + '</div><div class="center"><span class="step">' + round + "</span><h2>" + t("player.restTitle") + '</h2><p class="muted">' + t("player.upnext", { x: esc(exName(nx)) }) + "</p></div>" + orb +
        '<div class="row3"><button class="btn ghost" data-act="prev">‹ ' + t("player.prev") + '</button><button class="btn ghost" data-act="plus">' + t("player.plus") + '</button><button class="btn" data-act="skipRest">' + t("player.skipRest") + "</button></div>" +
        '<div class="row"><button class="btn dusk" data-act="pause">' + (p.paused ? t("player.resume") : t("player.pause")) + '</button></div><button class="btn plain" data-act="stopSession">' + t("player.stop") + "</button>";
    }
    return '<div class="dots">' + dots + '</div><div class="center"><span class="step">' + round + "</span><h2>" + esc(exName(e)) + '</h2><p class="muted">' + esc(pick(e.c)) + "</p>" +
      (cur.swapped ? '<span class="swap">' + t("player.swapped") + "</span>" : "") + "</div>" +
      '<div class="vid"><div><b>' + t("player.vid", { x: esc(exName(e)) }) + "</b><br><span>" +
      t("player.vidinfo", { who: t(S.demo === "f" ? "who.f" : "who.m"), angle: t(ui.angle === "face" ? "angle.face" : "angle.side") }) + "</span></div></div>" +
      '<div class="chips">' + chip(t("angle.face"), "angle", "face", ui.angle === "face") + chip(t("angle.side"), "angle", "side", ui.angle === "side") + "</div>" + orb +
      '<div class="row3"><button class="btn ghost" data-act="prev">‹ ' + t("player.prev") + '</button><button class="btn dusk" data-act="pause">' + (p.paused ? t("player.resume") : t("player.pause")) + '</button><button class="btn ghost" data-act="next">' + t("player.next") + " ›</button></div>" +
      '<div class="row"><button class="chip" data-act="redo">↻ ' + t("player.redo") + '</button><button class="chip" data-act="plus">' + t("player.plus") + '</button></div>' +
      '<button class="btn plain" data-act="stopSession">' + t("player.stop") + "</button>";
  };

  SCREENS.done = function () {
    return hero("double-pouce", t("guide.name")) + '<div class="stack"><h2>' + t("done.title") + "</h2><p>" + t("done.sub") + "</p></div>" +
      '<div class="stack"><button class="btn ghost solid" data-act="fb" data-v="hard">' + t("fb.hard") + '</button><button class="btn" data-act="fb" data-v="ok">' + t("fb.ok") + '</button><button class="btn ghost solid" data-act="fb" data-v="easy">' + t("fb.easy") + "</button></div>" +
      '<div class="card solid" id="fbMsg"' + (ui.fbMsg ? "" : " hidden") + ">" + esc(ui.fbMsg) + "</div>" +
      '<button class="btn dusk bottom" data-act="go" data-v="path">' + t("done.week") + "</button>";
  };

  SCREENS.body = function () {
    var ps = pickedList(), items = sessionItems();
    var n = items.filter(function (x) { return x.swapped; }).length;
    return "<h2>" + t("body.title") + '</h2><p class="muted">' + t("body.sub") + "</p>" + bodyMap() +
      '<div class="card">' + (ps.length ? t("body.some", { z: zlist(ps) }) + " " + swapLabel(items) + "." : t("body.none")) + "</div>" +
      '<div class="stack"><button class="btn dusk" data-act="go" data-v="lib">' + t("body.lib") + '</button><button class="btn ghost" data-act="go" data-v="anat">' + t("body.anat") + "</button></div>";
  };

  SCREENS.lib = function () {
    var cats = ["all"].concat(D.CATS);
    var rows = D.EX.filter(function (e) { return ui.libF === "all" || e.cat === ui.libF; }).map(function (e) {
      var hit = L.hits(e, S.zones);
      var sub = hit.length ? t("lib.hit", { z: zlist(hit) }) : e.z.length ? t("lib.uses", { z: zlist(e.z) }) : t("lib.none");
      return '<div class="libitem' + (hit.length ? " off" : "") + '"><div><b>' + esc(exName(e)) + '</b><div class="muted small">' + sub + "</div></div>" + (e.v1 ? '<span class="v1">V1</span>' : "") + "</div>";
    }).join("");
    return backChip("body") + "<h2>" + t("lib.title") + '</h2><p class="muted">' + t("lib.sub") + "</p>" +
      '<div class="chips">' + cats.map(function (c) { return chip(c === "all" ? t("lib.all") : t("cat." + c), "libf", c, ui.libF === c); }).join("") + "</div>" +
      '<div class="stack tight">' + rows + '</div><p class="muted small">' + t("lib.note") + "</p>";
  };

  function anatSvg() {
    var bones = ui.layer === "bones", s = '<svg class="body" viewBox="0 0 200 300" role="img" aria-label="' + esc(t("anat.title")) + '"><g class="sil"><circle cx="100" cy="38" r="20"/><rect x="72" y="62" width="56" height="130" rx="26"/><rect x="40" y="76" width="22" height="100" rx="11"/><rect x="138" y="76" width="22" height="100" rx="11"/><rect x="74" y="190" width="24" height="96" rx="12"/><rect x="102" y="190" width="24" height="96" rx="12"/></g>';
    if (bones) {
      s += '<g class="bone"><circle cx="100" cy="38" r="14"/><path d="M100 54V190" stroke-dasharray="3 5"/><ellipse cx="100" cy="108" rx="24" ry="32"/><path d="M72 82H128"/><ellipse cx="100" cy="190" rx="24" ry="11"/>' +
        '<path d="M70 86L50 152L38 176M130 86L150 152L162 176"/><path d="M88 198L84 262L86 288M112 198L116 262L114 288"/></g>';
    } else {
      s += '<g class="mus"><ellipse cx="86" cy="96" rx="14" ry="11"/><ellipse cx="114" cy="96" rx="14" ry="11"/><circle cx="62" cy="98" r="11"/><circle cx="138" cy="98" r="11"/>' +
        '<rect x="88" y="120" width="24" height="52" rx="10"/><ellipse cx="50" cy="128" rx="8" ry="20"/><ellipse cx="150" cy="128" rx="8" ry="20"/>' +
        '<ellipse cx="85" cy="226" rx="11" ry="30"/><ellipse cx="115" cy="226" rx="11" ry="30"/><ellipse cx="85" cy="272" rx="8" ry="16"/><ellipse cx="115" cy="272" rx="8" ry="16"/></g>';
    }
    D.ZONES.forEach(function (z) {
      POS[z].forEach(function (p) {
        s += '<circle class="z' + (ui.azone === z ? " on" : "") + '" data-act="azone" data-v="' + z + '" cx="' + p[0] + '" cy="' + p[1] + '" r="13"/>';
      });
    });
    return s + "</svg>";
  }

  SCREENS.anat = function () {
    var z = ui.azone, info = '<div class="card">' + t("anat.pick") + "</div>";
    if (z) {
      var A = D.ANAT[z], linked = D.EX.filter(function (e) { return e.z.indexOf(z) >= 0; }).map(function (e) { return "<li>" + esc(exName(e)) + "</li>"; }).join("");
      info = '<div class="card"><h3>' + t("zone." + z) + "</h3><p><b>" + t("anat.bonesLabel") + " :</b> " + esc(pick(A.b)) + "</p><p><b>" + t("anat.musclesLabel") + " :</b> " + esc(pick(A.m)) + "</p>" +
        "<p><b>" + t("anat.linked") + " :</b></p><ul class=\"plain-list\">" + linked + "</ul></div>";
    }
    return backChip("body") + "<h2>" + t("anat.title") + '</h2><p class="muted">' + t("anat.sub") + "</p>" +
      '<div class="chips">' + chip(t("anat.muscles"), "layer", "muscles", ui.layer === "muscles") + chip(t("anat.bones"), "layer", "bones", ui.layer === "bones") + "</div>" +
      anatSvg() + info + '<p class="muted small">' + t("anat.note") + "</p>";
  };

  function msgHtml(m) {
    return '<div class="msg ' + m.cls + '"><span class="who">' + esc(m.who || "") + "</span><span>" + esc(m.text) + "</span>" + (m.fiche ? ficheHtml(m.fiche) : "") + "</div>";
  }
  function ficheHtml(topic) {
    var list = D.FICHES[topic].map(function (r) { return "<span>• " + esc(exName(D.BY_ID[r[0]])) + " · " + r[1] + "</span>"; }).join("");
    return '<div class="fiche"><b>' + t("fiche.title", { z: t("zname." + topic) }) + "</b>" + list + '<button class="btn dusk" data-act="addFiche" data-v="' + topic + '">' + t("fiche.add") + "</button></div>";
  }

  SCREENS.coach = function () {
    var seg = '<div class="seg" role="group"><button data-act="coachtab" data-v="ai" aria-pressed="' + (ui.coachTab === "ai") + '">' + t("coach.ai") + '</button><button data-act="coachtab" data-v="pro" aria-pressed="' + (ui.coachTab === "pro") + '">' + t("coach.pro") + "</button></div>";
    var body;
    if (ui.coachTab === "ai") {
      var msgs = [{ cls: "ai", who: "", text: t("ai.hello") }].concat(ui.ai);
      body = guideRow(t("guide.illu")) + '<div class="chat" id="chat" aria-live="polite">' + msgs.map(msgHtml).join("") + "</div>" +
        '<div class="chips">' + [1, 2, 3, 4].map(function (i) { return '<button class="chip" data-act="ask" data-v="ai.s' + i + '">' + t("ai.s" + i) + "</button>"; }).join("") + "</div>" +
        '<form class="ask" data-form="ai"><input id="aiInput" placeholder="' + esc(t("ai.ph")) + '" aria-label="' + esc(t("ai.ph")) + '" autocomplete="off"><button class="btn" type="submit">' + t("ai.send") + "</button></form>" +
        '<p class="muted small">' + t("ai.disc") + "</p>";
    } else {
      var P = S.pro, rel = [1, 2, 3, 4].map(function (i) { return '<li class="' + P.relay[i - 1] + '"><i></i>' + t("pro.r" + i) + "</li>"; }).join("");
      var msgsP = [{ cls: "pro", who: t("pro.who.coach"), text: t("pro.welcome") }].concat(P.msgs);
      body = '<div class="pro"><div class="avatar">C</div><div><b>' + t("pro.name") + '</b><div class="muted small">' + t("pro.sample") + "</div></div></div>" +
        '<ol class="relay">' + rel + '</ol><div class="chat" id="chat" aria-live="polite">' + msgsP.map(msgHtml).join("") + "</div>" +
        '<form class="ask" data-form="pro"><input id="proInput" placeholder="' + esc(t("pro.ph")) + '" aria-label="' + esc(t("pro.ph")) + '" autocomplete="off"><button class="btn" type="submit">' + t("ai.send") + "</button></form>" +
        '<div class="demo-bar">' + t("pro.demo") + ' <button type="button" data-act="demoReply">' + t("pro.demoReply") + '</button><button type="button" data-act="demoLate">' + t("pro.demoLate") + "</button></div>" +
        '<p class="muted small">' + t("pro.disc") + "</p>";
    }
    return "<h2>" + t("coach.title") + "</h2>" + seg + '<div class="pane">' + body + "</div>";
  };

  SCREENS.path = function () {
    var days = L.weekDays(S.log, today()), n = L.lightCount(days), m = L.monthCounts(S.log, today());
    var cells = days.map(function (d) {
      var label = d.status === "s" ? t("day.s") : d.status === "r" ? t("day.r") : d.status === "now" ? t("day.now") : t("day.next");
      var icon = d.status === "s" ? "✓" : d.status === "r" ? "R" : "";
      var cls = d.status === "s" ? "full" : d.status === "r" ? "rest" : d.status === "now" ? "now" : "";
      return "<div><span>" + t("day." + d.dow) + '</span><span class="sun ' + cls + '" aria-label="' + label + '">' + icon + "</span></div>";
    }).join("");
    return "<h2>" + t("path.title") + '</h2><div class="week">' + cells + "</div>" +
      '<div class="card"><b class="big">' + t("path.light", { n: n }) + '</b><p class="muted">' + t("path.lightNote") + "</p></div>" +
      '<div class="card"><p><b>' + t("path.month") + '</b></p><p class="muted">' + t("path.monthText", { s: m.s, r: m.r }) + "</p></div>" +
      '<button class="btn bottom" data-act="go" data-v="paywall">' + t("path.unlock") + "</button>";
  };

  SCREENS.paywall = function () {
    return hero("pouce", t("guide.name")) + "<h2>" + t("pay.title") + '</h2><ul class="list card solid">' + [1, 2, 3, 4].map(function (i) { return "<li>" + t("pay.f" + i) + "</li>"; }).join("") + "</ul>" +
      '<div class="stack tight"><button class="plan" data-act="plan" data-v="year" aria-pressed="' + (S.plan === "year") + '"><div><b>' + t("pay.year") + '</b><div class="muted small">' + t("pay.yearSub") + '</div></div><span class="tag ok">' + t("pay.popular") + "</span></button>" +
      '<button class="plan" data-act="plan" data-v="month" aria-pressed="' + (S.plan === "month") + '"><div><b>' + t("pay.month") + '</b><div class="muted small">' + t("pay.monthSub") + "</div></div></button>" +
      '<button class="plan" data-act="addon" aria-pressed="' + S.addon + '"><div><b>' + t("pay.addon") + '</b><div class="muted small">' + t("pay.addonSub") + '</div></div><span class="tag">' + t("pay.option") + "</span></button></div>" +
      '<div class="bottom stack"><button class="btn" data-act="trial">' + t("pay.trial") + '</button><p class="muted small center">' + t(S.plan === "year" ? "pay.noteYear" : "pay.noteMonth") + '</p><p class="muted small center">' + t("pay.demo") + '</p><button class="btn ghost solid" data-act="go" data-v="home">' + t("pay.free") + "</button></div>";
  };

  SCREENS.settings = function () {
    return backChip("home") + "<h2>" + t("set.title") + "</h2><b>" + t("set.lang") + '</b><div class="chips">' +
      I.LANGS.map(function (l) { return chip(t("lang.name." + l), "lang", l, I.state.lang === l); }).join("") + "</div><b>" + t("set.amb") + "</b>" + ambCards() +
      levelBlock(true) + "<b>" + t("set.sound") + '</b><div class="chips">' + chip(t("set.on"), "sound", "1", S.sound) + chip(t("set.off"), "sound", "0", !S.sound) + "</div>" +
      "<b>" + t("set.text") + '</b><div class="chips">' + [[1, "set.t1"], [1.15, "set.t2"], [1.3, "set.t3"]].map(function (r) { return chip(t(r[1]), "tz", r[0], S.tz === r[0]); }).join("") + "</div>" +
      "<b>" + t("set.demo") + '</b><div class="chips">' + chip(t("who.f"), "demo", "f", S.demo === "f") + chip(t("who.m"), "demo", "m", S.demo === "m") + "</div>" +
      '<p class="muted small">' + t("set.dark") + " " + t("set.data") + '</p><button class="btn ghost" data-act="' + (ui.resetAsk ? "reset" : "resetAsk") + '">' + t(ui.resetAsk ? "set.resetSure" : "set.reset") + "</button>";
  };

  /* ---------- affichage ---------- */
  function tabsHtml() {
    var icons = {
      home: '<circle cx="12" cy="13" r="4"/><path d="M12 3v3M4.5 7.5 6.6 9.6M19.5 7.5 17.4 9.6M2 17h3M19 17h3"/>',
      body: '<circle cx="12" cy="5" r="2.5"/><path d="M12 8v7M7 10l5-2 5 2M9 21l3-6 3 6"/>',
      coach: '<path d="M4 5h16v11H9l-5 4z"/>',
      path: '<path d="M4 19V9M10 19V5M16 19v-7M21 19H3"/>'
    };
    var cur = ui.screen === "lib" || ui.screen === "anat" ? "body" : ui.screen;
    return ["home", "body", "coach", "path"].map(function (k) {
      return '<button class="tab" data-act="go" data-v="' + k + '" aria-current="' + (cur === k) + '"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + icons[k] + "</svg>" + t("tab." + (k === "home" ? "today" : k)) + "</button>";
    }).join("");
  }

  function render() {
    applyPrefs();
    var el = $("#screen"), tabs = $("#tabs");
    el.className = "screen" + (SKY[ui.screen] ? " sky" : "");
    el.innerHTML = SCREENS[ui.screen]();
    el.scrollTop = 0;
    var showTabs = !!TABS[ui.screen];
    tabs.hidden = !showTabs;
    if (showTabs) tabs.innerHTML = tabsHtml();
    var chat = $("#chat"); if (chat) chat.scrollTop = chat.scrollHeight;
  }

  function go(name) { stopTimer(); ui.screen = name; ui.resetAsk = false; render(); }

  /* ---------- séance ---------- */
  var wakeLock = null, audioCtx = null;
  function wake() {
    try { if (navigator.wakeLock && navigator.wakeLock.request) navigator.wakeLock.request("screen").then(function (l) { wakeLock = l; }).catch(function () { /* refusé */ }); } catch (e) { /* ignoré */ }
  }
  function unwake() { try { if (wakeLock) { wakeLock.release(); wakeLock = null; } } catch (e) { /* ignoré */ } }
  function beep(freq, len) {
    if (!S.sound) return;
    try {
      audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
      var o = audioCtx.createOscillator(), g = audioCtx.createGain();
      o.frequency.value = freq; g.gain.value = 0.08; o.connect(g); g.connect(audioCtx.destination);
      o.start(); o.stop(audioCtx.currentTime + len);
    } catch (e) { /* son indisponible */ }
  }
  function stopTimer() { if (ui.timer) { clearInterval(ui.timer); ui.timer = null; } unwake(); }
  function startSession() {
    ui.sess = L.newPlayer(L.sequence(sessionItems(), S.rounds), S.dur, S.rest);
    ui.screen = "player"; render(); runTimer(); wake();
  }
  function finish() {
    stopTimer(); S.log[L.dateKey(today())] = "s"; save(); ui.fbMsg = ""; ui.screen = "done"; render();
  }
  function afterMove() { if (ui.sess.done) finish(); else render(); }
  function runTimer() {
    if (ui.timer) clearInterval(ui.timer);
    ui.timer = setInterval(function () {
      var p = ui.sess; if (!p || p.paused) return;
      var ph = p.phase, ix = p.idx;
      L.tick(p);
      if (p.done) { beep(520, 0.4); finish(); return; }
      if (p.phase !== ph || p.idx !== ix) { beep(660, 0.25); render(); return; }
      var c = $("#count"); if (c) c.textContent = p.left;
      if (p.left <= 3) beep(880, 0.1);
    }, 1000);
  }

  /* ---------- coach ---------- */
  function addMsg(list, m) {
    list.push(m);
    var chat = $("#chat");
    if (chat) { chat.insertAdjacentHTML("beforeend", msgHtml(m)); chat.lastElementChild.scrollIntoView({ block: "nearest" }); }
  }
  function ask(text) {
    if (!text.trim()) return;
    addMsg(ui.ai, { cls: "me", who: "", text: text });
    var r = L.replyFor(text);
    setTimeout(function () {
      if (ui.screen !== "coach" || ui.coachTab !== "ai") return;
      addMsg(ui.ai, { cls: "ai", who: "", text: t(r.key) });
      if (r.zone && !S.zones[r.zone]) {
        S.zones[r.zone] = true; save();
        addMsg(ui.ai, { cls: "ai", who: "", text: t("ai.noted", { z: t("zone." + r.zone).toLowerCase() }) });
      }
    }, 500);
  }
  function refreshRelay() {
    var lis = document.querySelectorAll(".relay li");
    S.pro.relay.forEach(function (c, i) { if (lis[i]) lis[i].className = c; });
  }
  function setRelay(a) { S.pro.relay = a; save(); refreshRelay(); }
  function sendPro(text) {
    if (!text.trim()) return;
    var P = S.pro;
    addMsg(P.msgs, { cls: "me", who: t("pro.who.me"), text: text });
    P.topic = L.topicOf(text);
    if (L.isUrgent(text)) {
      setRelay(["done", "done", "", ""]);
      setTimeout(function () { addMsg(P.msgs, { cls: "ai", who: t("pro.who.ai"), text: t("pro.urgent") }); save(); }, 500);
    } else {
      P.replied = false; P.waiting = true; setRelay(["done", "done", "on", ""]);
      setTimeout(function () { addMsg(P.msgs, { cls: "ai", who: t("pro.who.ai"), text: t("pro.ack") }); save(); }, 500);
    }
    save();
  }
  function demoReply() {
    var P = S.pro;
    if (!P.waiting) { toast(t("pro.writeFirst")); return; }
    P.replied = true; P.waiting = false; setRelay(["done", "done", "done", ""]);
    addMsg(P.msgs, { cls: "pro", who: t("pro.who.coach"), text: t("pro.thanks") + t("why." + P.topic), fiche: P.topic });
    save();
  }
  function demoLate() {
    var P = S.pro;
    if (P.replied) { toast(t("pro.alreadyReplied")); return; }
    if (!P.waiting) { toast(t("pro.writeFirst")); return; }
    P.waiting = false; setRelay(["done", "done", "done", "on"]);
    addMsg(P.msgs, { cls: "ai", who: t("pro.who.ai2"), text: t("pro.late"), fiche: P.topic });
    addMsg(P.msgs, { cls: "team", who: t("pro.who.team"), text: t("pro.team") });
    save();
  }

  /* ---------- actions ---------- */
  function act(a, v, ev) {
    switch (a) {
      case "go": go(v); break;
      case "lang": S.lang = v; I.setLang(v); save(); render(); break;
      case "amb": S.amb = v; save(); render(); break;
      case "tz": S.tz = parseFloat(v); save(); render(); break;
      case "demo": S.demo = v; save(); render(); break;
      case "age": S.age = v; save(); render(); break;
      case "goal": S.goal = v; save(); render(); break;
      case "zone": S.zones[v] = !S.zones[v]; save(); render(); break;
      case "finishOnboarding": S.onboarded = true; save(); go("plan"); break;
      case "startSession": startSession(); break;
      case "pause": L.togglePause(ui.sess); render(); break;
      case "prev": L.prev(ui.sess); afterMove(); break;
      case "next": case "skipRest": L.next(ui.sess); afterMove(); break;
      case "redo": L.redo(ui.sess); afterMove(); break;
      case "plus": L.plus(ui.sess, 10); var cnt = $("#count"); if (cnt) cnt.textContent = ui.sess.left; break;
      case "jump": L.jump(ui.sess, parseInt(v, 10)); afterMove(); break;
      case "stopSession": go("home"); break;
      case "level": var lv = L.LEVELS[v]; S.dur = lv.dur; S.rest = lv.rest; S.rounds = lv.rounds; ui.custom = false; save(); render(); break;
      case "custom": ui.custom = !ui.custom; render(); break;
      case "dur": S.dur = parseInt(v, 10); save(); render(); break;
      case "restlen": S.rest = parseInt(v, 10); save(); render(); break;
      case "rounds": S.rounds = parseInt(v, 10); save(); render(); break;
      case "sound": S.sound = v === "1"; save(); render(); break;
      case "angle": ui.angle = v; render(); break;
      case "rest": if (S.log[L.dateKey(today())] !== "s") S.log[L.dateKey(today())] = "r"; save(); toast(t("home.restToast")); render(); break;
      case "fb": var dir = v === "hard" ? -1 : v === "easy" ? 1 : 0; if (dir) { S.dur = L.shiftDur(S.dur, dir); save(); }
        ui.fbMsg = t("fb." + v + ".msg") + (dir ? " " + t("fb.dur", { n: S.dur }) : "") + " " + t("fb.thanks"); var b = $("#fbMsg"); if (b) { b.hidden = false; b.textContent = ui.fbMsg; } break;
      case "libf": ui.libF = v; render(); break;
      case "layer": ui.layer = v; render(); break;
      case "azone": ui.azone = v; render(); break;
      case "coachtab": ui.coachTab = v; render(); break;
      case "ask": ask(t(v)); break;
      case "demoReply": demoReply(); break;
      case "demoLate": demoLate(); break;
      case "addFiche": S.zones[v] = true; save(); toast(t("fiche.added")); break;
      case "plan": S.plan = v; save(); render(); break;
      case "addon": S.addon = !S.addon; save(); toast(t(S.addon ? "pay.addonOn" : "pay.addonOff")); render(); break;
      case "trial": toast(t("pay.trialToast")); setTimeout(function () { go("home"); }, 900); break;
      case "resetAsk": ui.resetAsk = true; render(); break;
      case "reset":
        try { localStorage.removeItem(KEY); } catch (e) { /* ignoré */ }
        S = fresh(); I.setLang(I.guess(navigator.language)); ui.ai = []; ui.screen = "welcome"; ui.resetAsk = false; render(); break;
    }
  }

  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-act]");
    if (!el || el.disabled) return;
    act(el.getAttribute("data-act"), el.getAttribute("data-v"), e);
  });
  document.addEventListener("submit", function (e) {
    var f = e.target.closest("[data-form]");
    if (!f) return;
    e.preventDefault();
    var inp = f.querySelector("input"), v = inp.value; inp.value = "";
    if (f.getAttribute("data-form") === "ai") ask(v); else sendPro(v);
  });

  if ("serviceWorker" in navigator && /^https?:$/.test(location.protocol)) {
    window.addEventListener("load", function () {
      try { navigator.serviceWorker.register("sw.js").catch(function () { /* hors ligne désactivé */ }); } catch (e) { /* ignoré */ }
    });
  }

  render();
  window.SS.app = { act: act, state: function () { return S; }, ui: ui };
})();
