/* Écrans Studio (analyser une vidéo, créer une version améliorée, fabriquer) et Voix (essai, clonage). */
(function (g) {
  const { esc, store } = UI;
  const st = { sante: null, analyse: null, version: null, style: {}, sceneImages: {}, faceStyle: null, resultat: null, enreg: null };

  async function sante() {
    if (!st.sante) st.sante = await UI.get("sante");
    return st.sante;
  }
  const $ = (id) => document.getElementById(id);
  const ENGINE_NAMES = { kokoro: "Kokoro (gratuit)", chatterbox: "Ma voix clonée (Chatterbox)", fal: "Ma voix clonée (fal.ai)", edge: "Edge (gratuit, usage perso)", test: "Son de test" };

  function engineOptions(s, selected) {
    const list = s.moteurs_voix.map((m) => `<option value="${m}"${m === selected ? " selected" : ""}>${ENGINE_NAMES[m] || m}</option>`);
    return list.join("") + `<option value="aucune"${selected === "aucune" ? " selected" : ""}>Sans voix off</option>`;
  }
  function voiceOptions(s, engine) {
    const lang = store.get("langue", "fr");
    const list = (s.voix[engine] && s.voix[engine][lang]) || [];
    if (!list.length) return `<option value="">${s.clonage.includes(engine) ? "Votre voix enregistrée" : "Voix par défaut"}</option>`;
    return list.map((v) => `<option value="${v.id}">${esc(v.nom)}</option>`).join("");
  }
  function bindVoicePickers(s, engineId, voiceId) {
    const e = $(engineId), v = $(voiceId);
    const refresh = () => { v.innerHTML = voiceOptions(s, e.value); v.disabled = e.value === "aucune"; store.set("moteur", e.value); };
    e.onchange = refresh;
    refresh();
  }

  /* ---------------- Studio ---------------- */

  async function viewStudio(vue) {
    vue.innerHTML = UI.loading("Chargement du studio…");
    let s;
    try { s = await sante(); } catch (e) { vue.innerHTML = `<div class="card err">${esc(e.message)}</div>`; return; }
    const mode = store.get("studio.mode", "lien");
    vue.innerHTML = `
      <h1>Studio vidéo</h1>
      <p class="lead">Collez le lien d'une vidéo qui marche : le coach analyse son style et écrit une nouvelle version, originale et améliorée. Ensuite, le studio fabrique la vidéo avec images et voix off.</p>
      <div class="chips" role="radiogroup" aria-label="Point de départ">
        ${[["lien", "🔗 Lien"], ["fichier", "🎞️ Fichier"], ["sujet", "✍️ Sujet"], ["face", "🎤 Face caméra"]].map(([k, t]) =>
          `<label class="chip"><input type="radio" name="mode" value="${k}"${k === mode ? " checked" : ""}> ${t}</label>`).join("")}
      </div>
      <form class="card" id="f-studio"></form>
      <details class="card" id="ref-style"><summary><strong>🎨 Copier un style à partir d'images de référence</strong></summary>
        <p class="note">Ajoutez 1 à 4 captures d'écran d'une vidéo dont vous aimez la mise en page. L'IA mesure les couleurs, tailles et positions, et règle le modèle pour vous.</p>
        <label class="drop" for="ref-img"><strong>📸 Images de référence</strong><input type="file" id="ref-img" accept="image/*" multiple></label>
        <div class="thumbs" id="ref-thumbs"></div><div id="ref-res"></div>
      </details>
      <div id="r-studio"></div>`;
    document.querySelectorAll('input[name="mode"]').forEach((r) => (r.onchange = () => { store.set("studio.mode", r.value); renderForm(s, r.value); }));
    $("ref-img").onchange = (ev) => refStyle(ev.target.files);
    renderForm(s, mode);
    if (st.version) renderVersion(s);
  }

  function renderForm(s, mode) {
    const f = $("f-studio");
    const consigne = `<label for="consigne">Ce que vous voulez changer <small>(facultatif)</small></label>
      <input type="text" id="consigne" placeholder="ex. sujet capoeira, ton plus drôle, en 3 scènes">`;
    if (mode === "lien") {
      f.innerHTML = `<label for="lien">Lien de la vidéo (TikTok, Instagram, YouTube…)</label>
        <input type="text" id="lien" inputmode="url" placeholder="https://www.tiktok.com/@…/video/…">
        ${consigne}
        <p class="note">Utilisez vos propres vidéos ou des vidéos dont vous avez le droit de vous inspirer. Le studio ne recopie ni les images, ni les textes, ni la marque : il écrit une version originale dans le même style.</p>
        <button class="primary" type="submit">Analyser et améliorer</button>`;
    } else if (mode === "fichier") {
      f.innerHTML = `<label class="drop" for="src-file"><strong>🎞️ Choisir la vidéo</strong><span id="src-name">MP4, MOV ou WebM, 150 Mo au maximum</span><input type="file" id="src-file" accept="video/*"></label>
        ${consigne}<button class="primary" type="submit">Analyser et améliorer</button>`;
      $("src-file").onchange = (e) => ($("src-name").textContent = e.target.files[0] ? e.target.files[0].name : "");
    } else if (mode === "sujet") {
      f.innerHTML = `<label for="sujet">Sujet de la vidéo</label>
        <input type="text" id="sujet" placeholder="ex. ce que la capoeira m'a appris sur la patience">
        ${consigne}<button class="primary" type="submit">Écrire la vidéo</button>`;
    } else {
      f.innerHTML = `<p class="note">Votre vidéo face caméra reçoit des sous-titres mot à mot et des titres en boîte aux moments clés, comme les créateurs tech et éducatifs.</p>
        <label class="drop" for="face-file"><strong>🎤 Votre vidéo face caméra</strong><span id="face-name">Choisir un fichier</span><input type="file" id="face-file" accept="video/*"></label>
        <label class="chip" style="margin-top:12px"><input type="checkbox" id="face-titres" checked> Ajouter des titres en boîte</label>
        <div id="face-style-info" class="note">${st.faceStyle ? "Style de référence appliqué ✓" : "Style par défaut : texte blanc contour noir, mot en cours en jaune."}</div>
        <button class="primary" type="submit">Fabriquer avec sous-titres</button>`;
      $("face-file").onchange = (e) => ($("face-name").textContent = e.target.files[0] ? e.target.files[0].name : "");
    }
    f.onsubmit = (ev) => { ev.preventDefault(); submit(s, mode, f.querySelector("button[type=submit]")); };
  }

  async function submit(s, mode, btn) {
    const box = $("r-studio");
    btn.disabled = true;
    try {
      const consigne = $("consigne") ? $("consigne").value : "";
      if (mode === "face") {
        const file = $("face-file").files[0];
        if (!file) throw new Error("Choisissez votre vidéo.");
        box.innerHTML = UI.loading("Envoi de la vidéo…");
        const up = await UI.upload(file);
        const job = await UI.api("studio/fabriquer", { gabarit: "face_camera", video: up.id, style: st.faceStyle || {}, titres: $("face-titres").checked });
        return showResult(await follow(job.travail, box), s);
      }
      if (mode === "sujet") {
        const sujet = $("sujet").value.trim();
        if (!sujet) throw new Error("Indiquez un sujet.");
        box.innerHTML = UI.loading("Le coach écrit votre vidéo…");
        st.analyse = null;
        st.version = await UI.api("studio/creer", { sujet, consigne });
      } else {
        let body = { consigne };
        if (mode === "lien") {
          const lien = $("lien").value.trim();
          if (!/^https:\/\//.test(lien)) throw new Error("Collez un lien qui commence par https://");
          body.lien = lien;
          box.innerHTML = UI.loading("Récupération et analyse de la vidéo (30 à 60 s)…");
        } else {
          const file = $("src-file").files[0];
          if (!file) throw new Error("Choisissez une vidéo.");
          box.innerHTML = UI.loading("Envoi de la vidéo…");
          body.fichier = (await UI.upload(file)).id;
          box.innerHTML = UI.loading("Analyse du style (30 à 60 s)…");
        }
        st.analyse = await UI.api("studio/analyser", body);
        st.version = st.analyse.nouvelle_version;
      }
      st.sceneImages = {};
      renderVersion(s);
    } catch (e) {
      box.innerHTML = `<div class="card err" role="alert">${esc(e.message)}</div>`;
    } finally {
      btn.disabled = false;
    }
  }

  function renderVersion(s) {
    const v = st.version, a = st.analyse;
    const list = (arr) => `<ul class="clean">${arr.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;
    $("r-studio").innerHTML = (a ? `<section class="card"><h2>Le style analysé</h2>
        <p><strong>${esc(a.style.format)}</strong> · ${Math.round(a.style.duree_secondes)} s · ${esc(a.style.rythme)}</p>
        <p class="note">🎨 ${esc(a.style.visuel)}<br>🔤 ${esc(a.style.texte)}<br>🎙️ ${esc(a.style.voix)}</p>
        <h3>Pourquoi ça marche</h3>${list(a.pourquoi_ca_marche)}<h3>À améliorer</h3>${list(a.a_ameliorer)}</section>` : "") +
      `<section class="card"><h2>Nouvelle version : ${esc(v.titre)}</h2><p class="note">💡 ${esc(v.pourquoi_mieux)}</p>
        <p class="note">Modifiez les textes si besoin. Ajoutez votre propre image à une scène, sinon le studio en génère une.</p>
        ${v.scenes.map((sc, i) => `<div class="scene">
          <h3>Scène ${i + 1}</h3>
          <label for="sc-h-${i}">Texte du haut</label><input type="text" id="sc-h-${i}" value="${esc(sc.haut)}">
          <label for="sc-b-${i}">Texte du bas</label><input type="text" id="sc-b-${i}" value="${esc(sc.bas)}">
          <label for="sc-v-${i}">Voix off</label><textarea id="sc-v-${i}" rows="2">${esc(sc.voix)}</textarea>
          <label class="drop small" for="sc-i-${i}"><span id="sc-in-${i}">🖼️ ${st.sceneImages[i] ? "Image ajoutée ✓" : "Ma propre image (facultatif)"}</span><input type="file" id="sc-i-${i}" accept="image/*" data-scene="${i}"></label>
        </div>`).join("")}
        <h3>Voix off</h3>
        <div class="row"><div><label for="st-moteur">Moteur</label><select id="st-moteur">${engineOptions(s, store.get("moteur", s.moteurs_voix[0]))}</select></div>
        <div><label for="st-voix">Voix</label><select id="st-voix"></select></div></div>
        <label class="drop small" for="st-musique"><span id="st-mus-nom">🎵 Musique de fond libre de droits (facultatif) — ambiance conseillée : ${esc(v.ambiance_musique)}</span><input type="file" id="st-musique" accept="audio/*"></label>
        <button class="primary" id="btn-fab">🎬 Fabriquer la vidéo</button>
      </section><div id="r-fab"></div>`;
    bindVoicePickers(s, "st-moteur", "st-voix");
    document.querySelectorAll("input[data-scene]").forEach((inp) => (inp.onchange = async () => {
      const i = inp.dataset.scene, f = inp.files[0];
      if (!f) return;
      $("sc-in-" + i).textContent = "Envoi…";
      try { st.sceneImages[i] = (await UI.upload(f)).id; $("sc-in-" + i).textContent = "🖼️ " + f.name + " ✓"; }
      catch (e) { $("sc-in-" + i).textContent = e.message; }
    }));
    $("st-musique").onchange = async (e) => {
      const f = e.target.files[0];
      if (!f) return;
      $("st-mus-nom").textContent = "Envoi…";
      try { st.musique = (await UI.upload(f)).id; $("st-mus-nom").textContent = "🎵 " + f.name + " ✓"; } catch (err) { $("st-mus-nom").textContent = err.message; }
    };
    $("btn-fab").onclick = () => fabricate(s);
  }

  async function fabricate(s) {
    const btn = $("btn-fab"), box = $("r-fab");
    const v = JSON.parse(JSON.stringify(st.version));
    v.scenes.forEach((sc, i) => { sc.haut = $("sc-h-" + i).value; sc.bas = $("sc-b-" + i).value; sc.voix = $("sc-v-" + i).value; });
    st.version = v;
    btn.disabled = true;
    try {
      box.innerHTML = UI.loading("Mise en file d'attente…");
      const job = await UI.api("studio/fabriquer", {
        gabarit: "citation", version: v, moteur: $("st-moteur").value, voix: $("st-voix").value,
        images: st.sceneImages, musique: st.musique || null, style: st.style
      });
      showResult(await follow(job.travail, box), s, box);
    } catch (e) {
      box.innerHTML = `<div class="card err" role="alert">${esc(e.message)}</div>`;
    } finally {
      btn.disabled = false;
    }
  }

  async function follow(id, box) {
    return UI.waitJob(id, (etape) => (box.innerHTML = UI.loading("Fabrication : " + (etape || "…"))));
  }

  async function showResult(r, s, box) {
    box = box || $("r-studio");
    const url = await UI.fileUrl(r.video);
    const voixUrl = r.voix ? await UI.fileUrl(r.voix) : null;
    const v = st.version;
    box.innerHTML = `<section class="card"><h2>✅ Votre vidéo est prête</h2>
      <video class="result" src="${url}" controls playsinline></video>
      <div class="actions">
        <a class="secondary" href="${url}" download="coach-viral.mp4">⬇️ Télécharger la vidéo</a>
        ${voixUrl ? `<a class="secondary" href="${voixUrl}" download="voix-off.mp3">🎙️ Exporter la voix off</a>` : ""}
        ${v ? `<button class="secondary" id="btn-pub">🚀 Préparer la publication</button>` : ""}
      </div>
      ${v ? `<h3>Légende</h3><div class="pre">${esc(v.legende)}\n\n${esc((v.hashtags || []).map((h) => (h[0] === "#" ? h : "#" + h)).join(" "))}</div>` : ""}
    </section>`;
    if (v) $("btn-pub").onclick = () => g.CV.show("publier", v.titre + "\n" + v.scenes.map((x) => x.voix).join(" "));
  }

  async function refStyle(files) {
    const list = Array.prototype.slice.call(files, 0, 4);
    if (!list.length) return;
    const res = $("ref-res");
    try {
      const imgs = await Promise.all(list.map(Media.shrinkImage));
      $("ref-thumbs").innerHTML = imgs.map((src) => `<img alt="" src="${src}">`).join("");
      res.innerHTML = UI.loading("L'IA mesure le style…");
      const d = await UI.api("studio/style", { images: imgs.map(Media.base64) });
      st.style = d.citation;
      st.faceStyle = d.face_camera;
      const c = d.face_camera;
      res.innerHTML = `<p><strong>Modèle détecté : ${d.gabarit === "face_camera" ? "face caméra" : "citation"}</strong></p><p class="note">${esc(d.description)}</p>
        <div class="chips">${[c.couleur_texte, c.couleur_mot_actif, c.couleur_contour, c.titre_couleur_boite, c.titre_couleur_bordure, d.citation.couleur]
          .map((col) => `<span class="chip"><i class="swatch" style="background:${/^#[0-9a-f]{6}$/i.test(col) ? col : "#000"}"></i>${esc(col)}</span>`).join("")}</div>
        <p class="note">Ce style sera utilisé pour vos prochaines vidéos.</p>`;
      if (d.gabarit === "face_camera") { store.set("studio.mode", "face"); const r = document.querySelector('input[value="face"]'); if (r) { r.checked = true; renderForm(await sante(), "face"); } }
    } catch (e) {
      res.innerHTML = `<p class="err">${esc(e.message)}</p>`;
    }
  }

  /* ---------------- Voix ---------------- */

  async function viewVoix(vue) {
    vue.innerHTML = UI.loading("Chargement…");
    let s, ech;
    try { s = await sante(); ech = await UI.get("voix/echantillon"); } catch (e) { vue.innerHTML = `<div class="card err">${esc(e.message)}</div>`; return; }
    const canClone = s.clonage.length > 0;
    vue.innerHTML = `
      <h1>Voix off</h1>
      <p class="lead">Testez les voix, ou clonez la vôtre pour que vos vidéos parlent avec votre voix.</p>
      <section class="card"><h2>Essayer une voix</h2>
        <label for="vx-texte">Texte</label><textarea id="vx-texte" rows="3">Le pire bruit dans un couple, ce n'est pas les cris. C'est le silence.</textarea>
        <div class="row"><div><label for="vx-moteur">Moteur</label><select id="vx-moteur">${engineOptions(s, store.get("moteur", s.moteurs_voix[0])).replace(/<option value="aucune".*$/, "")}</select></div>
        <div><label for="vx-voix">Voix</label><select id="vx-voix"></select></div></div>
        <button class="primary" id="vx-go">▶️ Générer</button><div id="vx-res"></div>
      </section>
      <section class="card"><h2>🧬 Cloner ma voix</h2>
        ${canClone ? `<p>État : <strong id="vx-etat">${ech.enregistre ? "voix enregistrée ✓" : "aucune voix enregistrée"}</strong></p>
        <p class="note">Lisez la phrase ci-dessous à voix haute, dans un endroit calme, pendant 10 à 30 secondes (ajoutez quelques phrases de votre choix). Seule votre propre voix est autorisée.</p>
        <div class="pre" id="vx-phrase">…</div>
        <div class="actions"><button class="secondary" id="vx-rec">⏺️ Enregistrer</button>
          <label class="secondary" for="vx-file" style="cursor:pointer">📁 Ou choisir un fichier audio</label><input type="file" id="vx-file" accept="audio/*" hidden></div>
        <audio id="vx-ecoute" controls hidden></audio>
        <label class="chip" style="margin-top:12px"><input type="checkbox" id="vx-ok"> Je confirme que c'est ma propre voix et j'accepte qu'elle soit reproduite pour mes vidéos.</label>
        <div class="actions"><button class="primary" id="vx-send" disabled>Enregistrer ma voix</button></div>
        ${ech.enregistre ? `<button class="secondary" id="vx-del">🗑️ Supprimer ma voix</button>` : ""}
        <p class="note">Les voix clonées contiennent un filigrane inaudible qui indique qu'elles sont générées par IA.</p>`
        : `<p class="note">Le clonage n'est pas activé sur ce serveur : il faut Chatterbox (gratuit, avec une carte graphique) ou une clé fal.ai. Voir le guide d'installation.</p>`}
      </section>`;
    bindVoicePickers(s, "vx-moteur", "vx-voix");
    $("vx-go").onclick = async () => {
      const btn = $("vx-go"), res = $("vx-res");
      btn.disabled = true;
      res.innerHTML = UI.loading("Génération de la voix…");
      try {
        const job = await UI.api("voix/essai", { texte: $("vx-texte").value, moteur: $("vx-moteur").value, voix: $("vx-voix").value });
        const r = await UI.waitJob(job.travail);
        const url = await UI.fileUrl(r.voix);
        const wav = await UI.fileUrl(r.wav);
        res.innerHTML = `<audio src="${url}" controls autoplay></audio><div class="actions"><a class="secondary" href="${url}" download="voix.mp3">⬇️ MP3</a><a class="secondary" href="${wav}" download="voix.wav">⬇️ WAV</a></div>`;
      } catch (e) {
        res.innerHTML = `<p class="err">${esc(e.message)}</p>`;
      } finally { btn.disabled = false; }
    };
    if (!canClone) return;
    UI.get("voix/phrase?langue=" + store.get("langue", "fr")).then((p) => ($("vx-phrase").textContent = p.phrase)).catch(() => {});
    const ready = () => ($("vx-send").disabled = !(st.enreg && $("vx-ok").checked));
    $("vx-ok").onchange = ready;
    $("vx-file").onchange = (e) => { if (e.target.files[0]) { st.enreg = e.target.files[0]; preview(); ready(); } };
    function preview() { const a = $("vx-ecoute"); a.src = URL.createObjectURL(st.enreg); a.hidden = false; }
    let rec = null;
    $("vx-rec").onclick = async () => {
      const b = $("vx-rec");
      if (rec) { rec.stop(); return; }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
        const chunks = [];
        rec = new MediaRecorder(stream);
        rec.ondataavailable = (e) => chunks.push(e.data);
        rec.onstop = () => {
          stream.getTracks().forEach((t) => t.stop());
          const type = (rec.mimeType || "audio/webm").split(";")[0];
          st.enreg = new File(chunks, "voix." + (type.includes("mp4") ? "m4a" : type.includes("ogg") ? "ogg" : "webm"), { type });
          rec = null; b.textContent = "⏺️ Recommencer"; preview(); ready();
        };
        rec.start();
        b.textContent = "⏹️ Arrêter";
      } catch (e) { UI.toast("Micro inaccessible : autorisez-le, ou choisissez un fichier."); }
    };
    $("vx-send").onclick = async () => {
      const btn = $("vx-send");
      btn.disabled = true;
      try {
        const up = await UI.upload(st.enreg);
        const r = await UI.api("voix/echantillon", { fichier: up.id, consentement: true });
        $("vx-etat").textContent = `voix enregistrée ✓ (${Math.round(r.duree)} s)`;
        UI.toast("Votre voix est enregistrée");
      } catch (e) { UI.toast(e.message); }
      finally { ready(); }
    };
    if ($("vx-del")) $("vx-del").onclick = async () => { await UI.del("voix/echantillon"); $("vx-etat").textContent = "aucune voix enregistrée"; UI.toast("Voix supprimée"); };
  }

  g.StudioViews = { studio: viewStudio, voix: viewVoix, sante };
})(window);
