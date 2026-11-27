/* Néon Bay : achats selon la plateforme.
   - web    : lien de paiement (Systeme.io) + code de déblocage (comme avant)
   - play   : application Android (TWA) -> Google Play Billing via Digital Goods API + Payment Request
   Dans l'app Android, on ne montre ni le site de paiement ni son prix (règles Google Play),
   mais on accepte les codes déjà achetés ailleurs. */
window.NB_STORE = (() => {
  'use strict';
  const PLAY = 'https://play.google.com/billing';
  const cfg = () => (window.NB_DATA && window.NB_DATA.SHOP_CONFIG) || {};
  const state = { platform: 'web', ready: false, price: null, error: null, service: null, owned: false };

  function detect() {
    let p = 'web';
    try {
      const q = new URLSearchParams(location.search);
      if (q.get('src') === 'twa' || document.referrer.startsWith('android-app://')) sessionStorage.setItem('nb.platform', 'play');
      p = sessionStorage.getItem('nb.platform') || 'web';
    } catch (e) {}
    return p;
  }
  state.platform = detect();

  async function init() {
    if (state.platform !== 'play') { state.price = cfg().price || null; state.ready = true; return state; }
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

  return { state, init, buy, restore, get isPlay() { return state.platform === 'play'; } };
})();
