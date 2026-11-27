/* Néon Bay : achats selon la plateforme.
   - web    : lien de paiement (Systeme.io) + code de déblocage (comme avant)
   - play   : application Android
       * app native (Capacitor, dossier app-android/) -> Google Play Billing via cordova-plugin-purchase (CdvPurchase)
       * ancienne app TWA (Bubblewrap/PWABuilder) -> Digital Goods API + Payment Request
   Dans l'app Android, on ne montre ni le site de paiement ni son prix (règles Google Play),
   mais on accepte les codes déjà achetés ailleurs. */
window.NB_STORE = (() => {
  'use strict';
  const PLAY = 'https://play.google.com/billing';
  const cfg = () => (window.NB_DATA && window.NB_DATA.SHOP_CONFIG) || {};
  const state = { platform: 'web', native: false, ready: false, price: null, error: null, service: null, owned: false };
  const isNative = () => { try { return !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform()); } catch (e) { return false; } };

  function detect() {
    let p = 'web';
    if (isNative()) { state.native = true; return 'play'; } // l'app Capacitor compte comme Google Play
    try {
      const q = new URLSearchParams(location.search);
      if (q.get('src') === 'twa' || document.referrer.startsWith('android-app://')) sessionStorage.setItem('nb.platform', 'play');
      p = sessionStorage.getItem('nb.platform') || 'web';
    } catch (e) {}
    return p;
  }
  state.platform = detect();

  // ---------- app native (Capacitor + cordova-plugin-purchase v13) ----------
  const N = { store: null, waiters: [] };
  const sku = () => cfg().playSku || 'full_game';
  // le plugin Cordova n'existe qu'après « deviceready »
  function waitPlugin(ms) {
    return new Promise(res => {
      if (window.CdvPurchase) return res(window.CdvPurchase);
      let done = false; const end = () => { if (done) return; done = true; clearInterval(t); res(window.CdvPurchase || null); };
      document.addEventListener('deviceready', end, { once: true });
      const t = setInterval(() => { if (window.CdvPurchase) end(); }, 100);
      setTimeout(end, ms);
    });
  }
  const settle = (r) => { const w = N.waiters.splice(0); w.forEach(f => f(r)); };
  async function verifyRemote(t) { // serveur facultatif (verifyUrl) : vérifie le jeton et accuse réception côté serveur
    try { const r = await fetch(cfg().verifyUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sku: sku(), token: t.purchaseId }) }); return r.ok; } catch (e) { return false; }
  }
  async function initNative() {
    const C = await waitPlugin(8000);
    if (!C) throw new Error('Paiement Google Play indisponible');
    const { store, ProductType, Platform, LogLevel } = C; N.store = store;
    store.verbosity = LogLevel.WARNING;
    store.register([{ id: sku(), type: ProductType.NON_CONSUMABLE, platform: Platform.GOOGLE_PLAY }]);
    const mine = t => t.products && t.products.some(p => p.id === sku());
    store.when()
      .approved(async t => {
        if (!mine(t)) return;
        if (cfg().verifyUrl) { if (await verifyRemote(t)) t.finish(); else settle({ ok: false, error: 'Achat non vérifié, réessaie plus tard' }); }
        else t.verify(); // sans serveur : vérification locale, puis finish() = accusé de réception (obligatoire sous 3 jours)
      })
      .verified(r => r.finish())
      .finished(t => { if (!mine(t)) return; state.owned = true; settle({ ok: true, token: t.purchaseId }); })
      .pending(t => { if (mine(t)) settle({ ok: false, error: 'Paiement en attente : le jeu sera débloqué dès sa validation par Google' }); })
      .productUpdated(p => { if (p.id !== sku()) return; if (p.pricing && p.pricing.price) state.price = p.pricing.price; if (p.owned) state.owned = true; });
    store.error(e => { if (e && e.code === C.ErrorCode.PAYMENT_CANCELLED) settle({ ok: false, cancelled: true }); });
    const errs = await store.initialize([Platform.GOOGLE_PLAY]);
    const p = store.get(sku(), Platform.GOOGLE_PLAY);
    if (p && p.pricing && p.pricing.price) state.price = p.pricing.price;
    if (p && p.owned) state.owned = true;
    if (errs && errs.length && !p) throw new Error(errs[0].message || 'Google Play indisponible');
  }
  async function buyNative() {
    const C = window.CdvPurchase, store = N.store; if (!C || !store) return { ok: false, error: state.error || 'Paiement indisponible' };
    const p = store.get(sku(), C.Platform.GOOGLE_PLAY), offer = p && p.getOffer();
    if (!offer) return { ok: false, error: 'Produit introuvable sur Google Play' };
    if (p.owned) { state.owned = true; return { ok: true }; }
    const wait = new Promise(res => N.waiters.push(res));
    const err = await store.order(offer);
    if (err) { settle(null); return err.code === C.ErrorCode.PAYMENT_CANCELLED ? { ok: false, cancelled: true } : { ok: false, error: err.message || String(err.code) }; }
    // on attend la fin du parcours (finished / pending / annulation), 2 minutes au plus
    const r = await Promise.race([wait, new Promise(res => setTimeout(() => res({ ok: false, error: 'Délai dépassé. Touche « Restaurer mes achats » dans un instant.' }), 120000))]);
    return r || { ok: false, cancelled: true };
  }
  async function restoreNative(silent) {
    const C = window.CdvPurchase, store = N.store; if (!C || !store) return false;
    try {
      await store.restorePurchases();
      const p = store.get(sku(), C.Platform.GOOGLE_PLAY);
      if (p && p.owned) state.owned = true;
      return state.owned;
    } catch (e) { if (!silent) state.error = e.message || String(e); return false; }
  }

  async function init() {
    if (state.platform !== 'play') { state.price = cfg().price || null; state.ready = true; return state; }
    if (state.native) {
      try { await initNative(); } catch (e) { state.error = e.message || String(e); }
      state.ready = true; return state;
    }
    try {
      if (!('getDigitalGoodsService' in window)) throw new Error('Paiement Google Play indisponible sur cet appareil');
      const svc = await window.getDigitalGoodsService(PLAY);
      if (!svc) throw new Error('Service Google Play introuvable');
      state.service = svc;
      const sku = cfg().playSku || 'full_game';
      const details = await svc.getDetails([sku]);
      const d = details && details[0];
      if (d && d.price) state.price = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: d.price.currency }).format(+d.price.value);
      await restore(true);
    } catch (e) { state.error = e.message || String(e); }
    state.ready = true;
    return state;
  }

  // Renvoie true si le jeu complet est déjà acheté sur Google Play
  async function restore(silent) {
    if (state.native) return restoreNative(silent);
    if (state.platform !== 'play' || !state.service) return false;
    try {
      const sku = cfg().playSku || 'full_game';
      const list = await state.service.listPurchases();
      state.owned = list.some(p => (p.itemId || p.sku) === sku);
      return state.owned;
    } catch (e) { if (!silent) state.error = e.message || String(e); return false; }
  }

  // Lance l'achat Google Play. Renvoie { ok, token, cancelled, error }
  async function buy() {
    if (state.platform !== 'play') return { ok: false, error: 'web' };
    if (state.native) return buyNative();
    if (!state.service) return { ok: false, error: state.error || 'Paiement indisponible' };
    const sku = cfg().playSku || 'full_game';
    try {
      const req = new PaymentRequest([{ supportedMethods: PLAY, data: { sku } }], { total: { label: 'Total', amount: { currency: 'EUR', value: '0' } } });
      const res = await req.show();
      const token = res.details && res.details.purchaseToken;
      // Accusé de réception : obligatoire sous 3 jours, sinon Google rembourse l'achat.
      // Si un serveur de vérification est configuré, c'est lui qui vérifie et accuse réception (recommandé).
      let verified = true;
      if (cfg().verifyUrl) {
        try { const r = await fetch(cfg().verifyUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sku, token }) }); verified = r.ok; } catch (e) { verified = false; }
      } else if (state.service.acknowledge) {
        try { await state.service.acknowledge(token, 'onetime'); } catch (e) {}
      }
      await res.complete(verified ? 'success' : 'fail');
      if (!verified) return { ok: false, error: 'Achat non vérifié, réessaie plus tard' };
      state.owned = true;
      return { ok: true, token };
    } catch (e) {
      if (e && (e.name === 'AbortError' || /cancel/i.test(e.message || ''))) return { ok: false, cancelled: true };
      return { ok: false, error: e.message || String(e) };
    }
  }

  return { state, init, buy, restore, get isPlay() { return state.platform === 'play'; }, get isNative() { return state.native; } };
})();
