// Minimalny preload — atlas nie potrzebuje mostka do Node.
// Zostawiony jako punkt zaczepienia (np. gdyby updater.js miał kiedyś wołać natywne API).
const { contextBridge } = require('electron');
contextBridge.exposeInMainWorld('__ELECTRON_ATLAS__', { version: '0.1.0' });
