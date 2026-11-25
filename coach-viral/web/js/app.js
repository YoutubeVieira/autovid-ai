/* Coach Viral : écrans et enchaînements. */
(function () {
  var esc = UI.esc, store = UI.store;
  var vue = document.getElementById("vue");
  var PLAT = { tiktok: "TikTok", instagram: "Instagram Reels", youtube: "YouTube Shorts" };
  var UPLOAD = { tiktok: "https://www.tiktok.com/upload", instagram: "https://www.instagram.com/", youtube: "https://www.youtube.com/upload" };
  var state = { idees: null, score: null, profil: null, publier: null };
  var files = { scoreVideo: null, profilImages: [], publierVideo: null };

  function platformSelect(id, value) {
    return '<select id="' + id + '">' + Object.keys(PLAT).map(function (k) {
      return '<option value="' + k + '"' + (k === value ? " selected" : "") + ">" + PLAT[k] + "</option>";
    }).join("") + "</select>";
  }
  function val(id) { var el = document.getElementById(id); return el ? el.value : ""; }
  function hashtags(list) { return (list || []).map(function (h) { return h.charAt(0) === "#" ? h : "#" + h; }).join(" "); }
  function errorCard(e) { return '<div class="card err" role="alert">' + esc(e.message) + "</div>"; }

  /* ---------------- Idées ---------------- */

  function viewIdees() {
    var p = store.get("idees.form", {});
    vue.innerHTML =
      "<h1>Idées et scripts</h1><p class='lead'>Des idées de vidéos avec l'accroche, le script seconde par seconde, la légende et les hashtags.</p>" +
      '<form class="card" id="f-idees">' +
      '<label for="niche">Votre niche ou sujet</label><input type="text" id="niche" required placeholder="ex. capoeira pour débutants" value="' + esc(p.niche) + '">' +
      '<label for="audience">Public visé <small>(facultatif)</small></label><input type="text" id="audience" placeholder="ex. adultes qui n\'ont jamais fait de sport" value="' + esc(p.audience) + '">' +
      '<label for="objectif">Objectif <small>(facultatif)</small></label><input type="text" id="objectif" placeholder="ex. remplir mes cours du samedi" value="' + esc(p.objectif) + '">' +
      '<div class="row"><div><label for="plat-i">Plateforme</label>' + platformSelect("plat-i", p.plateforme || "tiktok") + "</div>" +
      '<div><label for="ton">Ton</label><select id="ton">' + ["énergique", "drôle", "inspirant", "pédagogique", "intime"].map(function (t) {
        return "<option" + (t === p.ton ? " selected" : "") + ">" + t + "</option>"; }).join("") + "</select></div></div>" +
      '<div class="row"><div><label for="nombre">Nombre d\'idées</label><select id="nombre">' + [3, 5, 8].map(function (n) {
        return "<option" + (n == p.nombre ? " selected" : "") + ">" + n + "</option>"; }).join("") + "</select></div>" +
      '<div><label for="contraintes">Contraintes <small>(facultatif)</small></label><input type="text" id="contraintes" placeholder="ex. seul, téléphone" value="' + esc(p.contraintes) + '"></div></div>' +
      '<button class="primary" type="submit">Générer les idées</button></form><div id="r-idees"></div>';
    document.getElementById("f-idees").onsubmit = async function (ev) {
      ev.preventDefault();
      var form = { niche: val("niche"), audience: val("audience"), objectif: val("objectif"), plateforme: val("plat-i"), ton: val("ton"), nombre: val("nombre"), contraintes: val("contraintes") };
      store.set("idees.form", form);
      await run(ev.submitter || ev.target.querySelector("button"), "r-idees", "Le coach écrit vos idées…", function () { return UI.api("ideas", form); }, function (d) { state.idees = d; return renderIdees(d); });
    };
    if (state.idees) document.getElementById("r-idees").innerHTML = renderIdees(state.idees);
  }

  function renderIdees(d) {
    return d.ideas.map(function (it, i) {
      var full = it.legende + "\n\n" + hashtags(it.hashtags);
      return '<article class="card idea"><span class="tag">' + esc(it.format) + '</span><span class="tag">' + Math.round(it.duree_secondes) + " s</span>" +
        "<h2>" + esc(it.titre) + "</h2>" +
        '<p class="hook">« ' + esc(it.accroche) + " »</p>" +
        '<p class="note">Texte à l\'écran : <strong>' + esc(it.texte_ecran) + "</strong></p>" +
        '<table class="script"><tbody>' + it.script.map(function (s) {
          return "<tr><td>" + esc(s.temps) + "</td><td>" + esc(s.parole) + '<div class="vis">🎬 ' + esc(s.visuel) + "</div></td></tr>";
        }).join("") + "</tbody></table>" +
        "<h3>Appel à l'action</h3><p>" + esc(it.appel_action) + "</p>" +
        "<h3>Légende</h3><div class='pre'>" + esc(it.legende) + '</div><p class="hashtags">' + esc(hashtags(it.hashtags)) + "</p>" +
        '<p class="note">💡 ' + esc(it.pourquoi_ca_marche) + "</p>" +
        '<div class="actions"><button class="secondary" data-copy="' + i + '">Copier la légende</button><button class="secondary" data-publier="' + i + '">Préparer la publication</button></div>' +
        '<textarea hidden id="leg-' + i + '">' + esc(full) + "</textarea></article>";
    }).join("");
  }

  /* ---------------- Score ---------------- */

  function viewScore() {
    vue.innerHTML =
      "<h1>Score de viralité</h1><p class='lead'>Ajoutez votre vidéo : le coach regarde l'accroche, le rythme, le texte à l'écran et vous dit quoi corriger avant de publier.</p>" +
      '<form class="card" id="f-score">' +
      '<label class="drop" for="video-s"><strong>🎞️ Choisir une vidéo</strong><span id="video-s-nom">La vidéo reste sur votre téléphone : seules 6 images sont envoyées.</span><input type="file" id="video-s" accept="video/*"></label>' +
      '<div class="thumbs" id="thumbs-s"></div>' +
      '<label for="desc-s">De quoi parle la vidéo ? <small>(conseillé)</small></label><textarea id="desc-s" placeholder="ex. Je montre 3 mouvements de base de capoeira pour débutants"></textarea>' +
      '<label for="trans-s">Ce qui est dit <small>(facultatif : améliore beaucoup l\'analyse)</small></label><textarea id="trans-s" placeholder="Collez le texte prononcé dans la vidéo"></textarea>' +
      '<label for="leg-s">Légende prévue <small>(facultatif)</small></label><input type="text" id="leg-s">' +
      '<label for="plat-s">Plateforme</label>' + platformSelect("plat-s", store.get("plateforme", "tiktok")) +
      '<button class="primary" type="submit">Analyser ma vidéo</button></form><div id="r-score"></div>' + historyBlock();
    var input = document.getElementById("video-s");
    input.onchange = async function () {
      var f = input.files[0];
      if (!f) return;
      document.getElementById("video-s-nom").textContent = "Préparation de " + f.name + "…";
      try {
        files.scoreVideo = await Media.framesFromVideo(f, 6);
        document.getElementById("video-s-nom").textContent = f.name + " · " + Math.round(files.scoreVideo.duree) + " s";
        document.getElementById("thumbs-s").innerHTML = files.scoreVideo.images.map(function (src) { return '<img alt="" src="' + src + '">'; }).join("");
      } catch (e) {
        files.scoreVideo = null;
        document.getElementById("video-s-nom").textContent = e.message;
      }
    };
    document.getElementById("f-score").onsubmit = async function (ev) {
      ev.preventDefault();
      var v = files.scoreVideo;
      var body = {
        description: val("desc-s"), transcription: val("trans-s"), legende: val("leg-s"), plateforme: val("plat-s"),
        duree: v ? v.duree : 0, images: v ? v.images.map(Media.base64) : []
      };
      store.set("plateforme", body.plateforme);
      await run(ev.target.querySelector("button"), "r-score", "Le coach regarde votre vidéo…", function () { return UI.api("score", body); }, function (d) {
        state.score = d;
        var h = store.get("historique", []);
        h.unshift({ date: new Date().toISOString(), score: Math.round(d.score_global), titre: (body.description || body.legende || "Vidéo").slice(0, 60) });
        store.set("historique", h.slice(0, 20));
        return renderScore(d);
      });
    };
    if (state.score) document.getElementById("r-score").innerHTML = renderScore(state.score);
  }

  function renderScore(d) {
    var g = Math.round(d.score_global), lv = UI.level(g, 100);
    return '<section class="card"><div class="gauge"><div class="ring" style="--v:' + g + ";--c:var(--" + lv + ')"><b class="n-' + lv + '">' + g + "</b></div>" +
      "<div><h2>Potentiel viral</h2><p>" + esc(d.resume) + "</p></div></div></section>" +
      '<section class="card"><h2>Les 3 choses à corriger d\'abord</h2><ol class="clean">' + d.priorites.slice(0, 3).map(function (p) { return "<li>" + esc(p) + "</li>"; }).join("") + "</ol></section>" +
      '<section class="card"><h2>Détail</h2>' + d.criteres.map(function (c) {
        var l = UI.level(c.note, 10);
        return '<div class="crit"><strong>' + esc(c.nom) + '</strong><strong class="n-' + l + '">' + Math.round(c.note) + "/10</strong>" +
          '<div class="bar"><i class="bg-' + l + '" style="width:' + Math.max(0, Math.min(100, c.note * 10)) + '%"></i></div>' +
          "<p>" + esc(c.constat) + "</p><p><strong>→ " + esc(c.conseil) + "</strong></p></div>";
      }).join("") + "</section>" +
      '<section class="card"><h2>Autres accroches à tester</h2>' + d.accroches_alternatives.map(function (a, i) {
        return '<div class="pre">« ' + esc(a) + ' »</div>';
      }).join("") + '<p class="note">' + esc(d.limites) + "</p></section>";
  }

  function historyBlock() {
    var h = store.get("historique", []);
    if (!h.length) return "";
    return '<section class="card"><h2>Mes derniers scores</h2><ul class="clean history">' + h.slice(0, 8).map(function (x) {
      return "<li><span>" + esc(x.titre) + ' <span class="note">' + new Date(x.date).toLocaleDateString("fr-FR") + '</span></span><strong class="n-' + UI.level(x.score, 100) + '">' + x.score + "</strong></li>";
    }).join("") + "</ul></section>";
  }

  /* ---------------- Profil ---------------- */

  function viewProfil() {
    var p = store.get("profil.form", {});
    vue.innerHTML =
      "<h1>Analyse du profil</h1><p class='lead'>Envoyez des captures d'écran de votre profil et de vos statistiques (TikTok, Instagram ou YouTube). Le coach repère ce qui marche et vous donne un plan sur 7 jours.</p>" +
      '<form class="card" id="f-profil">' +
      '<label for="pseudo">Nom du compte <small>(facultatif)</small></label><input type="text" id="pseudo" placeholder="@moncompte" value="' + esc(p.pseudo) + '">' +
      '<label for="niche-p">Niche</label><input type="text" id="niche-p" value="' + esc(p.niche) + '">' +
      '<label class="drop" for="img-p"><strong>📸 Ajouter des captures d\'écran</strong><span>Profil, statistiques, vidéos les plus vues (6 au maximum)</span><input type="file" id="img-p" accept="image/*" multiple></label>' +
      '<div class="thumbs" id="thumbs-p"></div>' +
      '<label for="stats">Ou collez vos chiffres <small>(abonnés, vues des dernières vidéos, etc.)</small></label><textarea id="stats">' + esc(p.stats) + "</textarea>" +
      '<button class="primary" type="submit">Analyser mon profil</button>' +
      '<p class="note">La connexion directe à votre compte TikTok demande une autorisation officielle de TikTok : en attendant, les captures d\'écran donnent le même résultat.</p></form><div id="r-profil"></div>';
    var input = document.getElementById("img-p");
    input.onchange = async function () {
      var list = Array.prototype.slice.call(input.files, 0, 6);
      try {
        files.profilImages = await Promise.all(list.map(Media.shrinkImage));
        document.getElementById("thumbs-p").innerHTML = files.profilImages.map(function (src) { return '<img alt="" src="' + src + '">'; }).join("");
      } catch (e) { UI.toast(e.message); }
    };
    document.getElementById("f-profil").onsubmit = async function (ev) {
      ev.preventDefault();
      var form = { pseudo: val("pseudo"), niche: val("niche-p"), stats: val("stats") };
      store.set("profil.form", form);
      var body = Object.assign({ images: files.profilImages.map(Media.base64) }, form);
      await run(ev.target.querySelector("button"), "r-profil", "Le coach étudie votre compte…", function () { return UI.api("profile", body); }, function (d) { state.profil = d; return renderProfil(d); });
    };
    if (state.profil) document.getElementById("r-profil").innerHTML = renderProfil(state.profil);
  }

  function renderProfil(d) {
    var g = Math.round(d.score_profil), lv = UI.level(g, 100);
    function list(a) { return '<ul class="clean">' + a.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>"; }
    return '<section class="card"><div class="gauge"><div class="ring" style="--v:' + g + ";--c:var(--" + lv + ')"><b class="n-' + lv + '">' + g + "</b></div><div><h2>Votre compte</h2><p>" + esc(d.resume) + "</p></div></div>" +
      (d.chiffres_lus.length ? "<h3>Chiffres lus</h3>" + list(d.chiffres_lus.map(function (c) { return c.indicateur + " : " + c.valeur; })) : "") + "</section>" +
      '<section class="card"><h2>✅ Points forts</h2>' + list(d.forces) + "<h2>⚠️ À améliorer</h2>" + list(d.faiblesses) +
      "<h3>Formats conseillés</h3>" + list(d.meilleurs_formats) + "<h3>Rythme de publication</h3><p>" + esc(d.frequence_conseillee) + "</p></section>" +
      '<section class="card"><h2>Plan sur 7 jours</h2><table class="script"><tbody>' + d.plan_7_jours.map(function (j) {
        return "<tr><td>" + esc(j.jour) + "</td><td>" + esc(j.action) + '<div class="vis">🎬 ' + esc(j.idee_video) + "</div></td></tr>";
      }).join("") + "</tbody></table></section>";
  }

  /* ---------------- Publier ---------------- */

  function viewPublier(prefill) {
    var canShareFiles = !!(navigator.canShare && window.File);
    vue.innerHTML =
      "<h1>Publier partout</h1><p class='lead'>Le coach adapte le titre, la légende et les hashtags à chaque plateforme. Ensuite, un bouton ouvre l'application avec votre vidéo.</p>" +
      '<form class="card" id="f-pub">' +
      '<label class="drop" for="video-p"><strong>🎞️ Votre vidéo</strong><span id="video-p-nom">Facultatif : pour la partager directement depuis votre téléphone</span><input type="file" id="video-p" accept="video/*"></label>' +
      '<label for="contenu">Contenu de la vidéo ou script</label><textarea id="contenu" required>' + esc(prefill || "") + "</textarea>" +
      '<label for="leg-p">Légende de départ <small>(facultatif)</small></label><input type="text" id="leg-p">' +
      "<label>Plateformes</label><div class='chips'>" + Object.keys(PLAT).map(function (k) {
        return '<label class="chip"><input type="checkbox" name="plat" value="' + k + '" checked> ' + PLAT[k] + "</label>";
      }).join("") + "</div>" +
      '<button class="primary" type="submit">Adapter pour chaque plateforme</button>' +
      '<p class="note">' + (canShareFiles ? "Sur téléphone, « Partager » ouvre TikTok, Instagram ou YouTube avec la vidéo." : "Sur ordinateur, « Ouvrir » ouvre la page d'envoi : déposez-y la vidéo et collez la légende.") +
      " La publication 100 % automatique demande de relier vos comptes via les accès officiels des plateformes (prochaine étape).</p></form><div id=\"r-pub\"></div>";
    document.getElementById("video-p").onchange = function (e) {
      files.publierVideo = e.target.files[0] || null;
      document.getElementById("video-p-nom").textContent = files.publierVideo ? files.publierVideo.name : "Aucune vidéo";
    };
    document.getElementById("f-pub").onsubmit = async function (ev) {
      ev.preventDefault();
      var plats = Array.prototype.map.call(document.querySelectorAll('input[name="plat"]:checked'), function (x) { return x.value; });
      var body = { contenu: val("contenu"), legende: val("leg-p"), plateformes: plats };
      await run(ev.target.querySelector("button"), "r-pub", "Le coach adapte vos textes…", function () { return UI.api("adapt", body); }, function (d) { state.publier = d; return renderPublier(d); });
    };
    if (state.publier && !prefill) document.getElementById("r-pub").innerHTML = renderPublier(state.publier);
  }

  function publishText(v) { return (v.titre ? v.titre + "\n\n" : "") + v.legende + "\n\n" + hashtags(v.hashtags); }

  function renderPublier(d) {
    return d.versions.map(function (v, i) {
      return '<section class="card"><h2>' + esc(PLAT[v.plateforme] || v.plateforme) + "</h2>" +
        (v.titre ? "<h3>Titre</h3><div class='pre'>" + esc(v.titre) + "</div>" : "") +
        "<h3>Légende</h3><div class='pre'>" + esc(v.legende) + '</div><p class="hashtags">' + esc(hashtags(v.hashtags)) + "</p>" +
        '<p class="note">' + esc(v.conseils) + "</p>" +
        '<div class="actions"><button class="secondary" data-copy-v="' + i + '">Copier</button><button class="secondary" data-share="' + i + '">Partager</button>' +
        '<a class="secondary" href="' + UPLOAD[v.plateforme] + '" target="_blank" rel="noopener">Ouvrir ' + esc(PLAT[v.plateforme]) + "</a></div></section>";
    }).join("");
  }

  async function share(v) {
    var text = publishText(v);
    var f = files.publierVideo;
    try {
      if (f && navigator.canShare && navigator.canShare({ files: [f] })) {
        await UI.copy(text);
        await navigator.share({ files: [f], text: text });
      } else if (navigator.share) {
        await navigator.share({ text: text });
      } else {
        await UI.copy(text);
        window.open(UPLOAD[v.plateforme], "_blank", "noopener");
      }
    } catch (e) {
      if (e && e.name !== "AbortError") UI.toast("Partage impossible : copiez la légende à la main.");
    }
  }

  /* ---------------- Commun ---------------- */

  async function run(button, target, msg, call, render) {
    var box = document.getElementById(target);
    button.disabled = true;
    box.innerHTML = UI.loading(msg);
    try {
      var d = await call();
      box.innerHTML = render(d);
      box.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) {
      box.innerHTML = errorCard(e);
    } finally {
      button.disabled = false;
    }
  }

  vue.addEventListener("click", function (ev) {
    var b = ev.target.closest("button");
    if (!b) return;
    if (b.dataset.copy != null) UI.copy(document.getElementById("leg-" + b.dataset.copy).value);
    if (b.dataset.publier != null) {
      var it = state.idees.ideas[+b.dataset.publier];
      show("publier", it.titre + "\n" + it.script.map(function (s) { return s.parole; }).join(" "));
    }
    if (b.dataset.copyV != null) UI.copy(publishText(state.publier.versions[+b.dataset.copyV]));
    if (b.dataset.share != null) share(state.publier.versions[+b.dataset.share]);
  });

  var VIEWS = {
    idees: viewIdees, score: viewScore, profil: viewProfil, publier: viewPublier,
    studio: function () { return StudioViews.studio(vue); }, voix: function () { return StudioViews.voix(vue); }
  };
  function show(name, arg) {
    document.querySelectorAll(".tabs button").forEach(function (t) { t.setAttribute("aria-selected", String(t.dataset.vue === name)); });
    store.set("vue", name);
    VIEWS[name](arg);
    window.scrollTo(0, 0);
  }
  document.querySelectorAll(".tabs button").forEach(function (t) { t.onclick = function () { show(t.dataset.vue); }; });

  /* ---------- Abonnement ---------- */

  async function subscribe() {
    if (document.querySelector("dialog.abo")) return;
    var s = await StudioViews.sante().catch(function () { return null; });
    if (!s || !s.vente) return;
    var q = s.quotas || {};
    var d = document.createElement("dialog");
    d.className = "abo";
    d.innerHTML = `<h2>Coach Viral Pro</h2><p class="prix">${esc(s.prix)}</p>
      <ul class="clean"><li>${q.analyse} analyses et idées par mois</li><li>${q.video} vidéos fabriquées par mois</li><li>Voix off réalistes, clonage de votre voix</li><li>Sans engagement : résiliable en un clic</li></ul>
      <div class="actions"><button class="secondary" value="non" id="abo-non">Plus tard</button><button class="primary" id="abo-go" style="margin-top:0">S'abonner</button></div>
      <p class="note">Paiement sécurisé par Stripe. Après le paiement, cet appareil reçoit votre clé d'abonnement : gardez-la (Réglages) pour l'utiliser sur un autre appareil.</p>`;
    document.body.appendChild(d);
    d.querySelector("#abo-non").onclick = function () { d.close(); };
    d.querySelector("#abo-go").onclick = async function () {
      try { location.href = (await UI.api("abonnement/payer", {})).url; } catch (e) { UI.toast(e.message); }
    };
    d.addEventListener("close", function () { d.remove(); });
    d.showModal();
  }

  async function activateFromUrl() {
    var p = new URLSearchParams(location.search);
    var sid = p.get("abonnement");
    if (!sid) return;
    history.replaceState(null, "", location.pathname);
    if (sid === "annule") return UI.toast("Paiement annulé.");
    try {
      var r = await UI.api("abonnement/activer", { session: sid });
      store.set("cle", r.cle);
      UI.toast("Bienvenue ! Votre abonnement est actif.");
    } catch (e) { UI.toast(e.message); }
  }

  /* Réglages : langue, thème, code d'accès ou abonnement. */
  document.getElementById("btn-reglages").onclick = async function () {
    var s = await StudioViews.sante().catch(function () { return {}; });
    var d = document.createElement("dialog");
    var cle = store.get("cle", "");
    d.innerHTML = '<form method="dialog"><h2>Réglages</h2>' +
      '<label for="r-langue">Langue des réponses et des voix</label><select id="r-langue"><option value="fr">Français</option><option value="pt">Português (Brasil)</option><option value="en">English</option></select>' +
      '<label for="r-theme">Thème</label><select id="r-theme"><option value="">Automatique</option><option value="light">Clair</option><option value="dark">Sombre</option></select>' +
      (s.vente
        ? '<label for="r-cle">Clé d\'abonnement</label><input type="text" id="r-cle" autocomplete="off" spellcheck="false"><div id="r-usage" class="note"></div>' +
          '<div class="actions"><button class="secondary" type="button" id="r-copier">Copier la clé</button><button class="secondary" type="button" id="r-portail">Gérer l\'abonnement</button><button class="secondary" type="button" id="r-abo">S\'abonner</button></div>'
        : '<label for="r-code">Code d\'accès <small>(donné par la personne qui gère le serveur)</small></label><input type="password" id="r-code" autocomplete="off">') +
      '<div class="actions"><button class="secondary" value="cancel">Annuler</button><button class="secondary" id="r-ok" value="ok">Enregistrer</button></div></form>';
    document.body.appendChild(d);
    d.querySelector("#r-langue").value = store.get("langue", "fr");
    d.querySelector("#r-theme").value = store.get("theme", "");
    if (s.vente) {
      d.querySelector("#r-cle").value = cle;
      d.querySelector("#r-copier").onclick = function () { UI.copy(d.querySelector("#r-cle").value); };
      d.querySelector("#r-abo").onclick = function () { d.close(); subscribe(); };
      d.querySelector("#r-portail").onclick = async function () {
        try { location.href = (await UI.api("abonnement/portail", {})).url; } catch (e) { UI.toast(e.message); }
      };
      if (cle) UI.get("abonnement/etat").then(function (e) {
        var u = e.usage;
        d.querySelector("#r-usage").textContent = (e.actif ? "Abonnement actif" : "Abonnement inactif") +
          " · ce mois : " + u.analyse.utilise + "/" + u.analyse.max + " analyses, " + u.video.utilise + "/" + u.video.max + " vidéos";
      }).catch(function () { d.querySelector("#r-usage").textContent = "Clé inconnue."; });
    } else {
      d.querySelector("#r-code").value = store.get("code", "");
    }
    d.addEventListener("close", function () {
      if (d.returnValue === "ok") {
        store.set("langue", d.querySelector("#r-langue").value);
        store.set("theme", d.querySelector("#r-theme").value);
        if (s.vente) store.set("cle", d.querySelector("#r-cle").value.trim());
        else store.set("code", d.querySelector("#r-code").value.trim());
        applyTheme();
        UI.toast("Réglages enregistrés");
      }
      d.remove();
    });
    d.showModal();
  };
  window.CV = { show: show, subscribe: subscribe };
  function applyTheme() {
    var t = store.get("theme", "");
    if (t) document.documentElement.setAttribute("data-theme", t); else document.documentElement.removeAttribute("data-theme");
  }

  applyTheme();
  activateFromUrl();
  show(VIEWS[store.get("vue", "idees")] ? store.get("vue", "idees") : "idees");
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(function () {});
})();
