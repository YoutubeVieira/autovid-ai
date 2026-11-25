/* Garde l'interface disponible hors connexion. Les demandes à l'IA (/api) ne sont jamais mises en cache.
   Changez VERSION à chaque mise à jour des fichiers. */
var VERSION = "cv-v3";
var SHELL = ["./", "./index.html", "./manifest.webmanifest", "./css/app.css", "./js/ui.js", "./js/media.js", "./js/studio.js", "./js/app.js", "./icons/icon.svg"];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(VERSION).then(function (c) { return c.addAll(SHELL); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== VERSION; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
/* Réseau d'abord (pour avoir la dernière version), cache si hors connexion. */
self.addEventListener("fetch", function (e) {
  var url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== self.location.origin || url.pathname.indexOf("/api/") !== -1) return;
  e.respondWith(fetch(e.request).then(function (res) {
    if (res.ok) { var copy = res.clone(); caches.open(VERSION).then(function (c) { c.put(e.request, copy); }); }
    return res;
  }).catch(function () { return caches.match(e.request).then(function (hit) { return hit || caches.match("./index.html"); }); }));
});
