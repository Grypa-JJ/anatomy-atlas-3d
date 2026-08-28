/* _packaging/shared/sw.js
 * Cache offline dla wariantu PWA (https). W Tauri / Capacitor NIE jest rejestrowany
 * (assety sa juz lokalne) — patrz warunek rejestracji wstrzykiwany przez assemble.mjs.
 *
 * Strategia:
 *  - shell (ten sam origin): stale-while-revalidate
 *  - warstwy atlasu (Draco-GLB) hostowane na R2 (inny origin): cache-first, bo
 *    sa niezmienne (nazwa pliku = wersja), a 28.9 MB nie chcemy sciagac co wejscie
 *  - precache: katalogi warstw + domyslnie widoczna warstwa (kosci), zeby pierwsze
 *    otwarcie atlasu bylo szybkie i zeby dzialal offline zaraz po instalacji
 */
var CACHE = 'atlas-cache-v2';

// host publicznego bucketa R2 z geometria atlasu (patrz GLB_BASE / R2_ORGAN_BASE)
var R2_HOST = 'pub-75514e92552347ccbcdab6bfacd153fd.r2.dev';

// warstwy GLB atlasu (na R2). Katalogi *_v2.json serwuje Netlije z tego samego
// origin — łapie je SWR przy pierwszym otwarciu, nie trzeba ich tu wymieniać.
var LAYERS = ['bones', 'muscles', 'vessels', 'organs', 'brain', 'nerves', 'lymph', 'connective', 'teeth'];
var R2_V3 = 'https://' + R2_HOST + '/atlas/v3/';
// precache tylko domyślnie widocznej warstwy (kości, 4.9 MB) — reszta warstw
// leci przez SWR gdy użytkownik ją włączy, albo hurtem na postMessage
// {type:'precache-layers'} ("pobierz atlas offline").
var PRECACHE = [R2_V3 + 'bones.glb'];

function cacheable(url) {
  var u = new URL(url);
  if (u.origin === self.location.origin) return true;
  if (u.host === R2_HOST && u.pathname.indexOf('/atlas/') === 0) return true;
  return false;
}

self.addEventListener('install', function (e) {
  self.skipWaiting();
  // precache best-effort — brak sieci przy instalacji nie blokuje aktywacji
  e.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return Promise.all(PRECACHE.map(function (url) {
        return fetch(url, { mode: 'cors' }).then(function (r) {
          if (r && r.ok) return cache.put(url, r);
        }).catch(function () {});
      }));
    })
  );
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
  if (req.method !== 'GET' || !cacheable(req.url)) return;

  var isImmutableAsset = /\.(glb|wasm)$/.test(new URL(req.url).pathname);

  e.respondWith(
    caches.open(CACHE).then(function (cache) {
      return cache.match(req).then(function (hit) {
        // GLB/wasm sa niezmienne — jesli sa w cache, oddaj od razu, bez rewalidacji
        if (hit && isImmutableAsset) return hit;
        var net = fetch(req).then(function (res) {
          if (res && res.ok) cache.put(req, res.clone());
          return res;
        }).catch(function () { return hit || Response.error(); });
        return hit || net;
      });
    })
  );
});

// pozwala stronie recznie dogrywać pozostałe warstwy do cache (np. przycisk
// "pobierz atlas offline") — postMessage({type:'precache-layers'})
self.addEventListener('message', function (e) {
  if (!e.data || e.data.type !== 'precache-layers') return;
  e.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return Promise.all(LAYERS.map(function (l) {
        var url = R2_V3 + l + '.glb';
        return cache.match(url).then(function (h) {
          if (h) return;
          return fetch(url, { mode: 'cors' }).then(function (r) { if (r && r.ok) return cache.put(url, r); }).catch(function () {});
        });
      }));
    })
  );
});
