#!/usr/bin/env python3
"""Construit la page « Voix off » (une seule page HTML) à partir de docs/voiceover.json.
Usage : python3 tools/build-voiceover.py sortie.html"""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
data = json.loads((root / "docs" / "voiceover.json").read_text(encoding="utf-8"))

TEMPLATE = r'''<title>Voix off Second Souffle</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Figtree:wght@400;500;600&display=swap">
<style>
/* Layout: one reading column, sticky language bar, one collapsible block per category. */
:root{--bg:#F3F5FA;--ink:#1A2036;--muted:#566080;--line:#D3D9E8;--card:#FFFFFF;--accent:#3B3F8F;--sun:#F2784B;--soft:#E7EAF5;--ok:#2F8F6B;
  --f-display:"Bricolage Grotesque","Trebuchet MS",sans-serif;--f-body:"Figtree","Segoe UI",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0D1124;--ink:#EEF0FA;--muted:#A0A9C8;--line:#2A3050;--card:#181D38;--accent:#A3ABFF;--sun:#FF8F63;--soft:#232A4E;--ok:#5FD3A3;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0D1124;--ink:#EEF0FA;--muted:#A0A9C8;--line:#2A3050;--card:#181D38;--accent:#A3ABFF;--sun:#FF8F63;--soft:#232A4E;--ok:#5FD3A3;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--f-body);line-height:1.55;font-size:16px;
  padding-block:36px 72px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
main{max-width:820px;margin:0 auto;display:flex;flex-direction:column;gap:28px}
h1,h2,h3{font-family:var(--f-display);margin:0;line-height:1.1;text-wrap:balance}
h1{font-size:clamp(34px,6vw,52px);font-weight:800;letter-spacing:-.02em}
h2{font-size:24px;font-weight:800}
p{margin:0}
button,summary{font:inherit;color:inherit;cursor:pointer}
button:focus-visible,summary:focus-visible,input:focus-visible{outline:3px solid var(--sun);outline-offset:2px}
.kicker{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:600}
.lead{font-size:18px;color:var(--muted);max-width:62ch;margin-top:12px}
.small{font-size:14px;color:var(--muted)}
.note{background:var(--soft);border-radius:14px;padding:14px 16px;font-size:15px}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.box{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;display:flex;flex-direction:column;gap:8px;min-width:0}
.box ul,.box ol{margin:0;padding-left:20px;display:grid;gap:4px}
.stat b{font-family:var(--f-display);font-size:30px;display:block}
.bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:3;background:var(--bg);padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;align-items:center;border-bottom:1px solid var(--line)}
.chip{border:2px solid var(--line);background:transparent;border-radius:999px;padding:8px 14px;min-height:44px;font-weight:500}
.chip[aria-pressed="true"]{background:var(--accent);color:var(--bg);border-color:var(--accent)}
.prog{margin-left:auto;font-size:14px;color:var(--muted)}
details{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:0 16px}
summary{min-height:56px;display:flex;align-items:center;justify-content:space-between;gap:10px;font-family:var(--f-display);font-weight:800;font-size:19px;list-style:none}
summary::-webkit-details-marker{display:none}
summary .n{font-family:var(--f-body);font-weight:500;font-size:14px;color:var(--muted)}
.inner{display:grid;gap:12px;padding-bottom:16px}
.item{border-top:1px solid var(--line);padding-top:12px;display:grid;gap:8px;min-width:0}
.item .id{font-size:13px;color:var(--muted);word-break:break-all}
.item .nm{font-weight:600}
.txt{background:var(--soft);border-radius:12px;padding:10px 12px}
.seg{display:grid;gap:4px}
.pause{font-size:13px;color:var(--sun);font-weight:600}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.btn{border:2px solid var(--line);background:transparent;border-radius:12px;padding:8px 14px;min-height:44px;font-weight:600}
.chk{display:flex;gap:8px;align-items:center;min-height:44px}
.chk input{width:22px;height:22px;accent-color:var(--ok)}
.v1{font-size:12px;font-weight:700;color:var(--ok)}
</style>

<main>
<header>
  <div class="kicker">Second Souffle · français, anglais, portugais du Brésil</div>
  <h1>Voix off</h1>
  <p class="lead">Tous les textes parlés de l'application : séances, exercices, bien-être, motivation et sécurité. Chaque phrase est un fichier audio à produire.</p>
</header>

<section class="cols" id="stats"></section>

<p class="note"><b>À relire avant de produire :</b> le portugais par une personne de langue maternelle brésilienne, et les consignes d'exercice par un kinésithérapeute ou un enseignant en activité physique adaptée. La voix est synthétique : dites-le dans l'application, et n'imitez la voix de personne.</p>

<section class="cols">
  <div class="box"><h2>Production, pas à pas</h2><ol>
    <li>Testez une phrase par langue avec le modèle de voix choisi (Gemini 3.8 Flash-Lite TTS ou un autre) et choisissez une voix par langue.</li>
    <li>Demandez le ton : chaleureux, calme, encourageant, rythme moyen.</li>
    <li>Produisez un fichier par phrase, nommé comme dans la colonne « fichier » du manifeste.</li>
    <li>Pour le bien-être, ajoutez le silence indiqué entre les phrases dans un logiciel de son.</li>
    <li>Écoutez tout, puis cochez ici.</li></ol></div>
  <div class="box"><h2>Fichiers du dépôt</h2><ul>
    <li><code>docs/voiceover.json</code> : tous les textes</li>
    <li><code>docs/voiceover-manifest.csv</code> : une ligne par fichier audio (id, langue, texte, pause, nom de fichier)</li></ul>
    <p class="small">Je n'ai pas testé de service de voix : aucune clé n'est disponible dans cette session.</p></div>
</section>

<div class="bar" role="group" aria-label="Langue">
  <button class="chip" data-lang="fr" aria-pressed="true">Français</button>
  <button class="chip" data-lang="en" aria-pressed="false">English</button>
  <button class="chip" data-lang="pt" aria-pressed="false">Português (Brasil)</button>
  <span class="prog" id="prog"></span>
</div>
<div id="cats" style="display:grid;gap:12px"></div>
</main>

<script>
(function () {
  var DATA = __DATA__;
  var lang = "fr", KEY = "ss.voice.v1", done = {};
  try { done = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { done = {}; }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(done)); } catch (e) {} }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function words(s) { return s.split(/\s+/).length; }
  var NAMES = { fr: "Français", en: "English", pt: "Português (Brasil)" };

  function units(c) {
    var out = [];
    c.items.forEach(function (it) {
      if (it.segments) it.segments.forEach(function (s, n) { out.push({ id: it.id + "." + (n < 9 ? "0" : "") + (n + 1), t: s.t, pause: s.pause }); });
      else out.push({ id: it.id, t: it.t, pause: 0 });
    });
    return out;
  }
  var all = [];
  DATA.categories.forEach(function (c) { all = all.concat(units(c)); });

  function stats() {
    var html = "";
    ["fr", "en", "pt"].forEach(function (l) {
      var w = 0, secs = 0;
      all.forEach(function (u) { var n = words(u.t[l]); w += n; secs += n / 2.5; });
      html += '<div class="box stat"><span class="small">' + NAMES[l] + "</span><b>" + all.length + '</b><span class="small">fichiers audio · ' + w + " mots · environ " + Math.round(secs / 60) + " min de parole</span></div>";
    });
    document.getElementById("stats").innerHTML = html;
  }

  function render() {
    var openIds = {};
    document.querySelectorAll("details[open]").forEach(function (d) { openIds[d.id] = 1; });
    var html = "";
    DATA.categories.forEach(function (c) {
      var us = units(c), nDone = us.filter(function (u) { return done[lang + ":" + u.id]; }).length;
      html += '<details id="c-' + c.id + '"' + (openIds["c-" + c.id] ? " open" : "") + "><summary><span>" + esc(c.title) + '</span><span class="n">' + nDone + "/" + us.length + " audio</span></summary><div class=\"inner\">" +
        (c.desc ? '<p class="small">' + esc(c.desc) + "</p>" : "") +
        '<div class="row"><button class="btn" data-copyall="' + c.id + '">Copier toute la catégorie</button></div>';
      c.items.forEach(function (it) {
        html += '<div class="item"><div class="nm">' + esc(it.name || it.id) + (it.v1 ? ' <span class="v1">V1</span>' : "") + '</div><div class="id">' + esc(it.id) + "</div>";
        if (it.segments) {
          it.segments.forEach(function (s, n) {
            var id = it.id + "." + (n < 9 ? "0" : "") + (n + 1);
            html += '<div class="seg"><div class="txt">' + esc(s.t[lang]) + "</div><div class=\"row\">" + (s.pause ? '<span class="pause">silence ensuite : ' + s.pause + ' s</span>' : '<span class="pause">fin</span>') +
              '<label class="chk"><input type="checkbox" data-k="' + lang + ":" + id + '"' + (done[lang + ":" + id] ? " checked" : "") + "> audio fait</label></div></div>";
          });
        } else {
          html += '<div class="txt">' + esc(it.t[lang]) + '</div><div class="row"><button class="btn" data-copy="' + esc(it.id) + '">Copier</button><span class="small">' + words(it.t[lang]) + ' mots</span>' +
            '<label class="chk"><input type="checkbox" data-k="' + lang + ":" + it.id + '"' + (done[lang + ":" + it.id] ? " checked" : "") + "> audio fait</label></div>";
        }
        html += "</div>";
      });
      html += "</div></details>";
    });
    document.getElementById("cats").innerHTML = html;
    var d = 0; all.forEach(function (u) { if (done[lang + ":" + u.id]) d++; });
    document.getElementById("prog").textContent = NAMES[lang] + " : " + d + "/" + all.length + " audio faits";
  }

  function findUnit(id) { return all.filter(function (u) { return u.id === id; })[0]; }
  function copy(btn, text, label) {
    var ok = function () { btn.textContent = "Copié"; setTimeout(function () { btn.textContent = label; }, 1500); };
    var fail = function () { btn.textContent = "Copie impossible ici"; setTimeout(function () { btn.textContent = label; }, 2000); };
    try { navigator.clipboard.writeText(text).then(ok, fail); } catch (e) { fail(); }
  }
  document.addEventListener("click", function (e) {
    var l = e.target.closest("[data-lang]");
    if (l) { lang = l.getAttribute("data-lang"); document.querySelectorAll("[data-lang]").forEach(function (b) { b.setAttribute("aria-pressed", String(b === l)); }); render(); return; }
    var c = e.target.closest("[data-copy]");
    if (c) { var u = findUnit(c.getAttribute("data-copy")); copy(c, u.t[lang], "Copier"); return; }
    var a = e.target.closest("[data-copyall]");
    if (a) {
      var cat = DATA.categories.filter(function (x) { return x.id === a.getAttribute("data-copyall"); })[0];
      copy(a, units(cat).map(function (u) { return u.id + " | " + u.t[lang] + (u.pause ? " | silence " + u.pause + " s" : ""); }).join("\n"), "Copier toute la catégorie");
    }
  });
  document.addEventListener("change", function (e) {
    var k = e.target.getAttribute && e.target.getAttribute("data-k");
    if (!k) return;
    done[k] = e.target.checked; save(); render();
  });
  stats(); render();
})();
</script>
'''

out = Path(sys.argv[1] if len(sys.argv) > 1 else "voix-off.html")
out.write_text(TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
print("écrit", out, out.stat().st_size, "octets")
