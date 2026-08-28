/* _packaging/shared/sw.js
 * Cache offline dla wariantu PWA (https). W Tauri / Capacitor NIE jest rejestrowany
 * (assety sa juz lokalne) — patrz warunek rejestracji wstrzykiwany przez assemble.mjs.
 * Strategia: stale-while-revalidate dla wszystkich GET z tego samego origin.
 */
var CACHE = 'atlas-cache-v1';

self.addEventListener('install', function () {
  self.skipWaiting();
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.filter(function (k) { return k !== CACHE; })
          .map(function (k) { return caches.delete(k); }));
      })
      .then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  if (new URL(req.url).origin !== self.location.origin) return;

  e.respondWith(
    caches.open(CACHE).then(function (cache) {
      return cache.match(req).then(function (hit) {
        var net = fetch(req).then(function (res) {
          if (res && res.ok) cache.put(req, res.clone());
          return res;
        }).catch(function () { return hit || Response.error(); });
        return hit || net;
      });
    })
  );
});
