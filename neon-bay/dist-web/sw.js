/* Néon Bay : cache hors ligne. La version est remplacée à chaque build (tools/build-web.js). */
const VERSION = 'nb-mwqrbe6e';
const SHELL = ['./', 'index.html', 'js/data.js', 'js/i18n-dict.js', 'js/i18n.js', 'js/audio.js', 'js/store.js', 'js/portal.js', 'js/engine.js', 'vendor/three.min.js', 'vendor/GLTFLoader.js', 'vendor/SkeletonUtils.js', 'vendor/postfx.js', 'models/robot.glb', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const req = e.request; if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    // fichiers du jeu : cache d'abord, réseau ensuite
    e.respondWith(caches.match(req, { ignoreSearch: url.pathname.endsWith('/') || url.pathname.endsWith('index.html') }).then(r => r || fetch(req).then(res => { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); return res; })).catch(() => caches.match('index.html')));
  } else if (/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) {
    // polices : on garde une copie pour le hors-ligne
    e.respondWith(caches.open(VERSION + '-fonts').then(c => c.match(req).then(r => r || fetch(req).then(res => { c.put(req, res.clone()); return res; }))));
  }
});
