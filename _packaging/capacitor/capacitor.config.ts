import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.grypajj.atlas3d',
  appName: 'Atlas anatomiczny 3D',
  // bundle skladany przez ../assemble.mjs (uruchamiany przez `npm run sync`)
  webDir: '../web',
  plugins: {
    CapacitorUpdater: {
      // baner + reczne "Zaktualizuj" obsluguje updater.js — NIE ciche auto:
      autoUpdate: false,
      // po pobraniu paczki OTA zresetuj do niej przy nastepnym starcie:
      resetWhenUpdate: true,
      // wlasny self-host: updater.js wola download({url}) z URL-a z latest.json (R2).
      // Pole 'updateUrl' zostawiamy puste — nie uzywamy wbudowanego auto-pollingu Capgo.
      updateUrl: '',
      appReadyTimeout: 10000
    }
  },
  android: {
    allowMixedContent: false
  }
};

export default config;
