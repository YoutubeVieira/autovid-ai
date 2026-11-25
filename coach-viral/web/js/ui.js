/* Outils communs : texte échappé, stockage local, appels au serveur, messages. */
(function (g) {
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  var store = {
    get: function (k, d) { try { var v = localStorage.getItem("cv." + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem("cv." + k, JSON.stringify(v)); } catch (e) { /* stockage indisponible */ } }
  };

  function headers(extra) {
    return Object.assign({ "x-code-acces": store.get("code", ""), "x-cle": store.get("cle", "") }, extra || {});
  }

  async function request(method, service, body, type) {
    var res;
    var init = { method: method, headers: headers(type ? { "Content-Type": type } : {}) };
    if (body !== undefined) init.body = body;
    try {
      res = await fetch("api/" + service, init);
    } catch (e) {
      throw new Error("Pas de connexion au serveur. Vérifiez votre réseau.");
    }
    var data = {};
    try { data = await res.json(); } catch (e) { /* réponse vide */ }
    if (res.status === 402 && g.CV && g.CV.subscribe) g.CV.subscribe();
    if (!res.ok) throw new Error(data.erreur || "Erreur " + res.status);
    return data;
  }

  function api(service, body) {
    return request("POST", service, JSON.stringify(Object.assign({ langue: store.get("langue", "fr") }, body)), "application/json");
  }
  function get(service) { return request("GET", service); }
  function del(service) { return request("DELETE", service); }
  function upload(file) {
    return request("POST", "fichier", file, file.type || "application/octet-stream");
  }

  /* Suit une fabrication jusqu'à la fin. */
  async function waitJob(id, onStep) {
    for (;;) {
      var j = await get("travaux/" + id);
      if (onStep) onStep(j.etape);
      if (j.etat === "termine") return j.resultat;
      if (j.etat === "erreur") throw new Error(j.erreur);
      await new Promise(function (r) { setTimeout(r, 1500); });
    }
  }

  /* Adresse d'un fichier produit (les en-têtes ne passent pas dans <video src>, d'où le passage par un blob). */
  async function fileUrl(name) {
    var res = await fetch("api/fichiers/" + name, { headers: headers() });
    if (!res.ok) throw new Error("Fichier indisponible.");
    return URL.createObjectURL(await res.blob());
  }

  var toastTimer;
  function toast(msg) {
    var t = document.querySelector(".toast");
    if (!t) { t = document.createElement("div"); t.className = "toast"; t.setAttribute("role", "status"); document.body.appendChild(t); }
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.hidden = true; }, 2400);
  }

  async function copy(text) {
    try { await navigator.clipboard.writeText(text); toast("Copié !"); }
    catch (e) { toast("Copie impossible : sélectionnez le texte à la main."); }
  }

  function level(note, max) {
    var r = note / max;
    return r >= 0.7 ? "good" : r >= 0.45 ? "mid" : "bad";
  }

  function loading(msg) {
    return '<div class="card loading"><div class="spin"></div><span>' + esc(msg) + "</span></div>";
  }

  g.UI = { esc: esc, store: store, api: api, get: get, del: del, upload: upload, waitJob: waitJob, fileUrl: fileUrl, toast: toast, copy: copy, level: level, loading: loading };
})(window);
