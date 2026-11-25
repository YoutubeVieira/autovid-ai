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

  async function api(service, body) {
    var res;
    try {
      res = await fetch("api/" + service, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-code-acces": store.get("code", "") },
        body: JSON.stringify(Object.assign({ langue: store.get("langue", "fr") }, body))
      });
    } catch (e) {
      throw new Error("Pas de connexion au serveur. Vérifiez votre réseau.");
    }
    var data = {};
    try { data = await res.json(); } catch (e) { /* réponse vide */ }
    if (!res.ok) throw new Error(data.erreur || "Erreur " + res.status);
    return data;
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

  g.UI = { esc: esc, store: store, api: api, toast: toast, copy: copy, level: level, loading: loading };
})(window);
