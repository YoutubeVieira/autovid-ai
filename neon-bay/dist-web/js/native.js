/* Néon Bay : réglages propres à l'app Android native (Capacitor).
   Ajouté seulement dans la version app (tools/build-app-web.js). Sans Capacitor, ce fichier ne fait rien.
   - bouton Retour : met le jeu en pause / revient à l'écran précédent ; sur l'accueil, l'app passe en arrière-plan (pas de fermeture brutale)
   - app en arrière-plan : pause du jeu et coupure du son */
(() => {
  'use strict';
  const C = window.Capacitor;
  if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  document.documentElement.classList.add('native-app');
  const App = C.Plugins && C.Plugins.App;
  if (!App) return;
  App.addListener('backButton', () => {
    let handled = false;
    try { handled = !!(window.NB_BACK && window.NB_BACK()); } catch (e) {}
    if (!handled) App.minimizeApp();
  });
  App.addListener('pause', () => {
    try { window.dispatchEvent(new Event('blur')); } catch (e) {} // le moteur met la partie en pause sur « blur »
    if (window.NB_AUDIO && window.NB_AUDIO.bg) window.NB_AUDIO.bg(true);
  });
  App.addListener('resume', () => { if (window.NB_AUDIO && window.NB_AUDIO.bg) window.NB_AUDIO.bg(false); });
})();
