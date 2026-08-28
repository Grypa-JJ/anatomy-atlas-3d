/* _packaging/shared/updater.js
 * Sprawdza dostepnosc aktualizacji i pokazuje baner "Dostepna aktualizacja".
 * Dziala w 3 srodowiskach, bez twardych zaleznosci (feature-detection):
 *   - Tauri (Windows)     -> natywny updater jesli wpiety, inaczej otwiera link do instalatora
 *   - Capacitor (Android) -> OTA paczki web przez @capgo/capacitor-updater jesli wpiety, inaczej link do APK
 *   - przegladarka / PWA  -> link do pobrania
 *
 * Konfiguracja: /app-version.json  (pole update_manifest_url -> zdalny manifest na R2).
 * Format zdalnego manifestu: patrz shared/latest.json.example
 */
(function () {
  'use strict';

  var LOCAL_URL = '/app-version.json';
  var CHECK_DELAY_MS = 2500;
  var DISMISS_KEY = 'atlas.update.dismissed';

  var RT =
    (typeof window !== 'undefined' && window.__TAURI__) ? 'tauri' :
    (typeof window !== 'undefined' && window.Capacitor) ? 'capacitor' :
    'web';

  function semverGt(a, b) {
    var pa = String(a).split('.').map(function (n) { return parseInt(n, 10) || 0; });
    var pb = String(b).split('.').map(function (n) { return parseInt(n, 10) || 0; });
    for (var i = 0; i < 3; i++) {
      if ((pa[i] || 0) > (pb[i] || 0)) return true;
      if ((pa[i] || 0) < (pb[i] || 0)) return false;
    }
    return false;
  }

  function jget(url) {
    return fetch(url, { cache: 'no-store' }).then(function (r) {
      if (!r.ok) throw new Error(url + ' -> ' + r.status);
      return r.json();
    });
  }

  function capPlugin() {
    return (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.CapacitorUpdater) || null;
  }

  function platformDownloadUrl(remote) {
    if (RT === 'tauri' && remote.platforms && remote.platforms['windows-x86_64']) {
      return remote.platforms['windows-x86_64'].url;
    }
    if (RT === 'capacitor') {
      return (remote.android && remote.android.url) || (remote.web && remote.web.url) || null;
    }
    return (remote.web && remote.web.url) ||
           (remote.platforms && remote.platforms['windows-x86_64'] && remote.platforms['windows-x86_64'].url) ||
           null;
  }

  function openExternal(url) {
    if (!url) return;
    if (RT === 'tauri' && window.__TAURI__ && window.__TAURI__.opener && window.__TAURI__.opener.openUrl) {
      window.__TAURI__.opener.openUrl(url).catch(function () { window.open(url, '_blank'); });
    } else if (RT === 'capacitor' && window.Capacitor.Plugins && window.Capacitor.Plugins.Browser) {
      window.Capacitor.Plugins.Browser.open({ url: url });
    } else {
      window.open(url, '_blank', 'noopener');
    }
  }

  function applyUpdate(remote, btn) {
    btn.disabled = true;
    btn.textContent = 'Pobieranie...';

    var fail = function (e) {
      if (e) console.error('[updater]', e);
      var url = platformDownloadUrl(remote);
      btn.disabled = false;
      btn.textContent = url ? 'Otworz strone pobrania' : 'Blad aktualizacji';
      btn.onclick = function () { openExternal(url); };
    };

    try {
      if (RT === 'tauri') {
        // Sciezka natywna dziala tylko gdy glue-faza wpiela globalny updater Tauri.
        var nativeUpd = window.__TAURI__ && window.__TAURI__.updater;
        if (nativeUpd && nativeUpd.check) {
          nativeUpd.check().then(function (u) {
            if (u && u.downloadAndInstall) {
              return u.downloadAndInstall().then(function () {
                if (window.__TAURI__.process && window.__TAURI__.process.relaunch) window.__TAURI__.process.relaunch();
              });
            }
            openExternal(platformDownloadUrl(remote));
          }).catch(fail);
          return;
        }
        openExternal(platformDownloadUrl(remote));
        return;
      }

      if (RT === 'capacitor') {
        var plugin = capPlugin();
        var web = remote.web || {};
        if (plugin && web.url) {
          plugin.download({ url: web.url, version: remote.version })
            .then(function (bundle) { return plugin.set(bundle); }) // restart -> nowa paczka web
            .catch(fail);
          return;
        }
        openExternal((remote.android && remote.android.url) || web.url);
        return;
      }

      openExternal(platformDownloadUrl(remote));
    } catch (e) {
      fail(e);
    }
  }

  function showBanner(remote) {
    if (document.getElementById('atlas-update-banner')) return;

    var wrap = document.createElement('div');
    wrap.id = 'atlas-update-banner';
    wrap.style.cssText = [
      'position:fixed', 'left:50%', 'bottom:18px', 'transform:translateX(-50%)', 'z-index:2147483000',
      'background:#1b1e28', 'color:#e9edf2', 'border:1px solid #3a4553', 'border-radius:12px',
      'padding:12px 14px', 'font:13.5px/1.45 system-ui,-apple-system,Segoe UI,sans-serif',
      'box-shadow:0 12px 40px -12px rgba(0,0,0,.6)', 'display:flex', 'gap:12px',
      'align-items:center', 'max-width:min(560px,92vw)'
    ].join(';');

    var txt = document.createElement('div');
    txt.style.flex = '1';
    var head = document.createElement('div');
    head.innerHTML = 'Dostepna aktualizacja <b>' + escapeHtml(remote.version) + '</b>';
    txt.appendChild(head);
    if (remote.notes) {
      var sub = document.createElement('div');
      sub.style.cssText = 'color:#9aa4b4;margin-top:2px;font-size:12.5px';
      sub.textContent = String(remote.notes).slice(0, 160);
      txt.appendChild(sub);
    }

    var go = document.createElement('button');
    go.textContent = 'Zaktualizuj';
    go.style.cssText = 'background:#6c5ce7;color:#fff;border:0;border-radius:8px;padding:8px 14px;font:600 13px system-ui;cursor:pointer;white-space:nowrap';
    go.onclick = function () { applyUpdate(remote, go); };

    var later = document.createElement('button');
    later.textContent = 'Pozniej';
    later.style.cssText = 'background:transparent;color:#9aa4b4;border:1px solid #3a4553;border-radius:8px;padding:8px 12px;cursor:pointer;white-space:nowrap';
    later.onclick = function () {
      try { localStorage.setItem(DISMISS_KEY, remote.version); } catch (e) {}
      wrap.remove();
    };

    wrap.appendChild(txt);
    wrap.appendChild(go);
    wrap.appendChild(later);
    document.body.appendChild(wrap);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function run() {
    jget(LOCAL_URL).then(function (local) {
      if (!local.update_manifest_url || local.update_manifest_url.indexOf('REPLACE-ME') !== -1) return;
      return jget(local.update_manifest_url).then(function (remote) {
        if (!remote || !remote.version || !semverGt(remote.version, local.version)) return;
        var dismissed = null;
        try { dismissed = localStorage.getItem(DISMISS_KEY); } catch (e) {}
        if (dismissed === remote.version) return;
        if (document.body) showBanner(remote);
        else addEventListener('DOMContentLoaded', function () { showBanner(remote); });
      });
    }).catch(function () { /* offline / brak endpointu -> cisza */ });
  }

  setTimeout(run, CHECK_DELAY_MS);
})();
