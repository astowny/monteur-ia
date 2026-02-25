const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('monteur', {
  getConfig: () => ipcRenderer.invoke('config:get'),
  saveConfig: (conf) => ipcRenderer.invoke('config:save', conf),
});
