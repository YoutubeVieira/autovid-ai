#!/usr/bin/env python3
"""Construit la page « Dossier de tournage » (une seule page HTML) à partir de docs/production-data.json.
Usage : python3 tools/build-production.py sortie.html"""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
data = json.loads((root / "docs" / "production-data.json").read_text(encoding="utf-8"))

TEMPLATE = r'''<title>Dossier de tournage</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Figtree:wght@400;500;600&display=swap">
<style>
/* Layout: one reading column; a sticky language switch; one card per exercise. */
:root{--bg:#F3F5FA;--ink:#1A2036;--muted:#566080;--line:#D3D9E8;--card:#FFFFFF;--accent:#3B3F8F;--sun:#F2784B;--soft:#E7EAF5;--ok:#2F8F6B;
  --f-display:"Bricolage Grotesque","Trebuchet MS",sans-serif;--f-body:"Figtree","Segoe UI",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0D1124;--ink:#EEF0FA;--muted:#A0A9C8;--line:#2A3050;--card:#181D38;--accent:#A3ABFF;--sun:#FF8F63;--soft:#232A4E;--ok:#5FD3A3;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0D1124;--ink:#EEF0FA;--muted:#A0A9C8;--line:#2A3050;--card:#181D38;--accent:#A3ABFF;--sun:#FF8F63;--soft:#232A4E;--ok:#5FD3A3;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--f-body);line-height:1.55;font-size:16px;
  padding-block:36px 72px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
main{max-width:820px;margin:0 auto;display:flex;flex-direction:column;gap:36px}
h1,h2,h3{font-family:var(--f-display);margin:0;line-height:1.1;text-wrap:balance}
h1{font-size:clamp(34px,6vw,52px);font-weight:800;letter-spacing:-.02em}
h2{font-size:26px;font-weight:800}
h3{font-size:20px;font-weight:600}
p{margin:0}
button{font:inherit;color:inherit;cursor:pointer}
button:focus-visible,input:focus-visible{outline:3px solid var(--sun);outline-offset:2px}
.kicker{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:600}
.lead{font-size:18px;color:var(--muted);max-width:60ch;margin-top:12px}
.small{font-size:14px;color:var(--muted)}
section{display:flex;flex-direction:column;gap:14px;min-width:0}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}
.box{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;display:flex;flex-direction:column;gap:8px;min-width:0}
.box ul{margin:0;padding-left:18px;display:grid;gap:4px}
.note{background:var(--soft);border-radius:14px;padding:14px 16px;font-size:15px}
.bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:3;background:var(--bg);padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;align-items:center;border-bottom:1px solid var(--line)}
.chip{border:2px solid var(--line);background:transparent;border-radius:999px;padding:8px 14px;min-height:44px;font-weight:500}
.chip[aria-pressed="true"]{background:var(--accent);color:var(--bg);border-color:var(--accent)}
.prog{margin-left:auto;font-size:14px;color:var(--muted)}
.ex{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px;display:grid;gap:12px;min-width:0}
.ex header{display:flex;gap:10px;align-items:baseline;justify-content:space-between;flex-wrap:wrap}
.ex .num{font-family:var(--f-display);font-weight:800;color:var(--sun);font-size:15px;letter-spacing:.06em}
.tags{display:flex;gap:6px;flex-wrap:wrap}
.tag{font-size:13px;background:var(--soft);padding:3px 10px;border-radius:999px}
.dl{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:0;font-size:15px}
.dl dt{color:var(--muted);font-weight:600}
.dl dd{margin:0;min-width:0}
.script{background:var(--soft);border-radius:12px;padding:12px 14px;display:grid;gap:8px}
.script p{font-size:16px}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.btn{border:2px solid var(--line);background:transparent;border-radius:12px;padding:8px 14px;min-height:44px;font-weight:600}
.chk{display:flex;gap:8px;align-items:center;min-height:44px}
.chk input{width:22px;height:22px;accent-color:var(--ok)}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:var(--card)}
table{border-collapse:collapse;width:100%;min-width:520px;font-size:15px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
tr:last-child td{border-bottom:0}
</style>

<main>
<header>
  <div class="kicker">Second Souffle · version 1</div>
  <h1>Dossier de tournage</h1>
  <p class="lead">Les 19 exercices de la première version : plans à filmer, variantes, points de sécurité et voix off en français, anglais et portugais du Brésil.</p>
</header>

<section>
  <h2>Avant de filmer</h2>
  <p class="note"><b>À faire valider d'abord</b> par un kinésithérapeute ou un enseignant en activité physique adaptée : chaque geste, chaque variante et chaque point de vigilance. Le portugais est à relire par une personne de langue maternelle brésilienne.</p>
  <div class="cols">
    <div class="box"><h3>Personnes</h3><ul><li>Une femme et un homme, adultes, environ 45 à 60 ans, corps ordinaires.</li><li>Un coach diplômé sur place, avec le droit de refaire un plan.</li><li>Contrats de cession de droit à l'image signés avant le tournage, avec durée, territoires et usages. Faites-les relire par un juriste.</li></ul></div>
    <div class="box"><h3>Lieu et matériel</h3><ul><li>Un salon lumineux, même décor et même éclairage pour tout.</li><li>Chaise stable sans accoudoirs, tapis épais, mur lisse, sol non glissant.</li><li>Élastiques de deux résistances, coussin, petite bouteille d'eau.</li></ul></div>
    <div class="box"><h3>Tenues</h3><ul><li>Une couleur proche de l'ambiance : prune et corail (Aube), bleu pétrole et cuivre (Ardoise).</li><li>Éviter le vert citron et le camouflage de l'illustration de Léo.</li><li>Pieds nus ou chaussures plates, vêtements ajustés pour voir les alignements.</li></ul></div>
    <div class="box"><h3>Prises</h3><ul><li>Filmer en horizontal 16:9, en haute définition, pour pouvoir recadrer en vertical.</li><li>Pour chaque angle : 3 répétitions propres, puis 1 en ralenti.</li><li>Boucle finale de 5 secondes, sans son. La voix est ajoutée ensuite.</li></ul></div>
  </div>
  <div class="box"><h3>Volume</h3><p id="vol"></p></div>
</section>

<section>
  <h2>Voix off</h2>
  <div class="cols">
    <div class="box"><h3>Réglages à tester</h3><ul><li>Modèle : Gemini 3.8 Flash-Lite TTS, via l'API Google Cloud ou AI Studio.</li><li>Tester d'abord une phrase par langue pour vérifier que la voix est naturelle en français, en anglais et en portugais du Brésil.</li><li>Générer chaque fichier audio une seule fois, l'enregistrer et le réutiliser dans l'application.</li></ul></div>
    <div class="box"><h3>Ton demandé</h3><ul><li>Chaleureux, calme, encourageant, rythme moyen. Énergique sans crier.</li><li>Phrases courtes, un verbe d'action au début, la respiration en dernier.</li><li>Jamais de promesse de santé.</li></ul></div>
    <div class="box"><h3>Règles</h3><ul><li>Dire dans l'application que la voix est synthétique.</li><li>Ne pas imiter la voix d'une personne réelle.</li><li>Relire le portugais : vocabulaire brésilien, pas européen.</li><li>Vérifier les règles des plateformes pour les vidéos avec voix générée.</li></ul></div>
  </div>
</section>

<section>
  <h2>Les 19 exercices</h2>
  <div class="bar" role="group" aria-label="Langue du script">
    <button class="chip" data-lang="fr" aria-pressed="true">Français</button>
    <button class="chip" data-lang="en" aria-pressed="false">English</button>
    <button class="chip" data-lang="pt" aria-pressed="false">Português (Brasil)</button>
    <span class="prog" id="prog"></span>
  </div>
  <div id="list" style="display:grid;gap:14px"></div>
  <p class="small">Durée estimée de la voix : environ 2,5 mots par seconde. Les cases sont enregistrées dans ce navigateur seulement.</p>
</section>
</main>

<script>
(function () {
  var DATA = __DATA__;
  var lang = "fr", KEY = "ss.prod.v1", done = {};
  try { done = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { done = {}; }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(done)); } catch (e) {} }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  var clips = 0;
  DATA.items.forEach(function (i) { clips += i.angles.length * 2; });
  document.getElementById("vol").textContent = DATA.items.length + " exercices × 2 personnes × leurs angles = " + clips + " plans à filmer, sans compter les reprises et les variantes (douce et soutenue).";

  function render() {
    var html = "";
    DATA.items.forEach(function (i, n) {
      var s = i.s[lang], words = s.split(/\s+/).length, secs = Math.round(words / 2.5);
      var zones = i.zones.length ? i.zones.join(", ") : "aucune zone sensible";
      html += '<article class="ex"><header><div><span class="num">EXERCICE ' + (n + 1) + '</span><h3>' + esc(i[lang]) + '</h3></div><div class="tags">' +
        i.angles.map(function (a) { return '<span class="tag">' + esc(a) + "</span>"; }).join("") + "</div></header>" +
        '<dl class="dl"><dt>Installation</dt><dd>' + esc(i.setup) + "</dd><dt>À surveiller</dt><dd>" + esc(i.watch) + "</dd><dt>Zones</dt><dd>" + esc(zones) + "</dd><dt>Variante douce</dt><dd>" + esc(i.easy) + "</dd><dt>Variante soutenue</dt><dd>" + esc(i.hard) + "</dd></dl>" +
        '<div class="script"><p>' + esc(s) + '</p><div class="row"><button class="btn" data-copy="' + i.id + '">Copier le texte</button><span class="small">' + words + " mots, environ " + secs + " s</span></div></div>" +
        '<div class="row"><label class="chk"><input type="checkbox" data-k="' + i.id + ':film"' + (done[i.id + ":film"] ? " checked" : "") + '> Filmé</label><label class="chk"><input type="checkbox" data-k="' + i.id + ':voice"' + (done[i.id + ":voice"] ? " checked" : "") + '> Voix off faite (' + lang + ')</label></div></article>';
    });
    document.getElementById("list").innerHTML = html;
    progress();
  }
  function progress() {
    var f = 0, v = 0;
    DATA.items.forEach(function (i) { if (done[i.id + ":film"]) f++; if (done[i.id + ":voice"]) v++; });
    document.getElementById("prog").textContent = "Filmés : " + f + "/" + DATA.items.length + " · Voix : " + v + "/" + DATA.items.length;
  }
  document.addEventListener("click", function (e) {
    var l = e.target.closest("[data-lang]");
    if (l) {
      lang = l.getAttribute("data-lang");
      document.querySelectorAll("[data-lang]").forEach(function (b) { b.setAttribute("aria-pressed", String(b === l)); });
      render(); return;
    }
    var c = e.target.closest("[data-copy]");
    if (c) {
      var it = DATA.items.filter(function (x) { return x.id === c.getAttribute("data-copy"); })[0], txt = it.s[lang];
      var ok = function () { c.textContent = "Copié"; setTimeout(function () { c.textContent = "Copier le texte"; }, 1500); };
      var fail = function () {
        var r = document.createRange(); r.selectNodeContents(c.closest(".script").querySelector("p"));
        var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r); c.textContent = "Texte sélectionné";
      };
      try { navigator.clipboard.writeText(txt).then(ok, fail); } catch (err) { fail(); }
    }
  });
  document.addEventListener("change", function (e) {
    var k = e.target.getAttribute && e.target.getAttribute("data-k");
    if (!k) return;
    done[k] = e.target.checked; save(); progress();
  });
  render();
})();
</script>
'''

out = Path(sys.argv[1] if len(sys.argv) > 1 else "dossier-de-tournage.html")
out.write_text(TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
print("écrit", out, out.stat().st_size, "octets")
