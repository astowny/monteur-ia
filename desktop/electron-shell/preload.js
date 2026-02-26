const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('monteur', {
  // Config
  getConfig: () => ipcRenderer.invoke('config:get'),
  saveConfig: (conf) => ipcRenderer.invoke('config:save', conf),
  onBackendStatus: (cb) => ipcRenderer.on('backend:status', (_event, data) => cb(data)),

  // File dialogs
  openVideo: () => ipcRenderer.invoke('file:pick-video'),
  openSubtitle: () => ipcRenderer.invoke('file:pick-subtitle'),
  saveAs: (defaultPath) => ipcRenderer.invoke('file:save-as', defaultPath),

  // FFmpeg export
  runExport: (command) => ipcRenderer.invoke('export:run', command),
  onExportProgress: (cb) => ipcRenderer.on('export:progress', (_event, data) => cb(data)),
});
