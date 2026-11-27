/* Néon Bay : version portails de jeux (Poki, CrazyGames).
   Activée seulement si window.NB_PORTAL vaut 'poki' ou 'crazygames' (mis par tools/build-portal.js).
   Sur les portails : tous les niveaux sont gratuits, l'argent vient des publicités du portail.
   Vérifie les API dans la documentation de chaque portail avant de soumettre. */
window.NB_PORTAL_API = (() => {
  'use strict';
  const kind = window.NB_PORTAL || null;
  let sdk = null, playing = false;
  const mute = m => { try { window.NB_AUDIO && window.NB_AUDIO.setMute(m); } catch (e) {} };
  let ready = Promise.resolve();
  try {
    if (kind === 'poki' && window.PokiSDK) ready = window.PokiSDK.init().then(() => { sdk = 'poki'; }).catch(() => { sdk = 'poki'; });
    else if (kind === 'crazygames' && window.CrazyGames && window.CrazyGames.SDK) ready = window.CrazyGames.SDK.init().then(() => { sdk = 'cg'; }).catch(() => {});
  } catch (e) {}
  const CG = () => window.CrazyGames.SDK;
  return {
    kind,
    get active() { return !!kind; },
    loaded() { ready.then(() => { try { if (sdk === 'poki') window.PokiSDK.gameLoadingFinished(); else if (sdk === 'cg' && CG().game.loadingStop) CG().game.loadingStop(); } catch (e) {} }); },
    start() { if (playing) return; playing = true; try { if (sdk === 'poki') window.PokiSDK.gameplayStart(); else if (sdk === 'cg') CG().game.gameplayStart(); } catch (e) {} },
    stop() { if (!playing) return; playing = false; try { if (sdk === 'poki') window.PokiSDK.gameplayStop(); else if (sdk === 'cg') CG().game.gameplayStop(); } catch (e) {} },
    // pub entre deux niveaux (le portail décide s'il en montre une)
    breakAd() {
      return new Promise(res => {
        try {
          if (sdk === 'poki') { window.PokiSDK.commercialBreak(() => mute(true)).then(() => { mute(false); res(); }).catch(() => { mute(false); res(); }); return; }
          if (sdk === 'cg') { CG().ad.requestAd('midgame', { adStarted: () => mute(true), adFinished: () => { mute(false); res(); }, adError: () => { mute(false); res(); } }); return; }
        } catch (e) {}
        res();
      });
    },
    // pub récompensée : renvoie true si le joueur l'a regardée jusqu'au bout
    rewarded() {
      return new Promise(res => {
        try {
          if (sdk === 'poki') { window.PokiSDK.rewardedBreak(() => mute(true)).then(ok => { mute(false); res(!!ok); }).catch(() => { mute(false); res(false); }); return; }
          if (sdk === 'cg') { CG().ad.requestAd('rewarded', { adStarted: () => mute(true), adFinished: () => { mute(false); res(true); }, adError: () => { mute(false); res(false); } }); return; }
        } catch (e) {}
        res(false);
      });
    },
  };
})();
