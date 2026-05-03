module.exports = function registerAudioHandlers(ipcMain) {
  // Audio recording is handled on the renderer side via Web Audio API
  // This module handles any native audio operations if needed

  ipcMain.handle('audio:startRecording', async () => {
    return { status: 'use-web-api' };
  });

  ipcMain.handle('audio:stopRecording', async () => {
    return { status: 'use-web-api' };
  });
};
