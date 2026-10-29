/* Service worker : garde l'application disponible hors connexion.
   Changez VERSION quand la liste des fichiers change. */
var VERSION = "ss-v5";
var SHELL = [
  "./", "./index.html", "./manifest.webmanifest", "./css/styles.css",
  "./js/i18n.js", "./js/data.js", "./js/logic.js", "./js/app.js",
  "./icons/icon.svg", "./icons/icon-192.png", "./icons/icon-512.png",
  "./img/leo.webp", "./img/ecoute.webp", "./img/bras-leves.webp", "./img/pouce.webp", "./img/double-pouce.webp"
];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(VERSION).then(function (c) { return c.addAll(SHELL); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== VERSION; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

/* Réponse immédiate depuis le cache, mise à jour en arrière-plan : une modification est visible à la visite suivante. */
self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;
  e.respondWith(
    caches.open(VERSION).then(function (cache) {
      return cache.match(req).then(function (hit) {
        var net = fetch(req).then(function (res) {
          if (res && res.ok && res.type === "basic") cache.put(req, res.clone());
          return res;
        }).catch(function () { return hit || cache.match("./index.html"); });
        return hit || net;
      });
    })
  );
});
