const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // File system
  browseFolder: () => ipcRenderer.invoke('fs:browseFolder'),
  browseFile: (filters) => ipcRenderer.invoke('fs:browseFile', filters),
  readFile: (filePath) => ipcRenderer.invoke('fs:readFile', filePath),
  writeFile: (filePath, content) => ipcRenderer.invoke('fs:writeFile', filePath, content),
  fileExists: (filePath) => ipcRenderer.invoke('fs:fileExists', filePath),
  openFolder: (folderPath) => ipcRenderer.invoke('fs:openFolder', folderPath),
  openExternal: (url) => ipcRenderer.invoke('fs:openExternal', url),
  getImageBase64: (filePath) => ipcRenderer.invoke('fs:getImageBase64', filePath),

  // Config persistence
  loadConfig: () => ipcRenderer.invoke('config:load'),
  saveConfig: (config) => ipcRenderer.invoke('config:save', config),
  loadApiKey: (provider) => ipcRenderer.invoke('config:loadApiKey', provider),
  saveApiKey: (provider, key) => ipcRenderer.invoke('config:saveApiKey', provider, key),

  // Agent
  startAgent: (config) => ipcRenderer.invoke('agent:start', config),
  stopAgent: () => ipcRenderer.invoke('agent:stop'),
  sendAgentMessage: (msg) => ipcRenderer.invoke('agent:send', msg),
  onAgentMessage: (cb) => {
    const handler = (_, msg) => cb(msg);
    ipcRenderer.on('agent:message', handler);
    return () => ipcRenderer.removeListener('agent:message', handler);
  },

  // Audio
  startRecording: () => ipcRenderer.invoke('audio:startRecording'),
  stopRecording: () => ipcRenderer.invoke('audio:stopRecording'),
  onRecordingData: (cb) => {
    const handler = (_, data) => cb(data);
    ipcRenderer.on('audio:data', handler);
    return () => ipcRenderer.removeListener('audio:data', handler);
  },

  // Remotion
  detectRemotion: (folderPath) => ipcRenderer.invoke('remotion:detect', folderPath),
  openRemotionStudio: (folderPath) => ipcRenderer.invoke('remotion:openStudio', folderPath),

  // Platform
  platform: process.platform,
});
