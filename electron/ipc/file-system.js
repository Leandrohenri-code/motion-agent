const path = require('path');
const os = require('os');

module.exports = function registerFileSystemHandlers(ipcMain, dialog, shell, fs, osModule) {
  const configDir = path.join(osModule.homedir(), '.motion-agent');
  const configPath = path.join(configDir, 'config.json');

  function ensureConfigDir() {
    if (!fs.existsSync(configDir)) fs.mkdirSync(configDir, { recursive: true });
  }

  ipcMain.handle('fs:browseFolder', async (event) => {
    const result = await dialog.showOpenDialog({ properties: ['openDirectory'] });
    return result.canceled ? null : result.filePaths[0];
  });

  ipcMain.handle('fs:browseFile', async (event, filters) => {
    const result = await dialog.showOpenDialog({
      properties: ['openFile'],
      filters: filters || [{ name: 'All Files', extensions: ['*'] }],
    });
    return result.canceled ? null : result.filePaths[0];
  });

  // Multi-select nativo para imagens/vídeos
  ipcMain.handle('fs:browseFiles', async (event, opts) => {
    const { type = 'images' } = opts || {};
    const imageFilters = [
      { name: 'Imagens', extensions: ['jpg','jpeg','png','webp','gif','tiff','tif','bmp','avif','heic','heif','svg'] },
    ];
    const videoFilters = [
      { name: 'Vídeos', extensions: ['mp4','mov','avi','webm','mkv','m4v','wmv','flv'] },
    ];
    const result = await dialog.showOpenDialog({
      properties: ['openFile', 'multiSelections'],
      filters: type === 'videos' ? videoFilters : imageFilters,
    });
    return result.canceled ? [] : result.filePaths;
  });

  // Lê arquivo e retorna base64 data URL (com resize opcional via canvas no renderer)
  ipcMain.handle('fs:readFileBase64', async (event, filePath) => {
    try {
      const data = fs.readFileSync(filePath);
      const ext = path.extname(filePath).toLowerCase().replace('.', '');
      const mimeMap = {
        jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png',
        webp: 'image/webp', gif: 'image/gif', bmp: 'image/bmp',
        tiff: 'image/tiff', tif: 'image/tiff', svg: 'image/svg+xml',
        avif: 'image/avif', heic: 'image/heic', heif: 'image/heif',
        mp4: 'video/mp4', mov: 'video/quicktime', webm: 'video/webm',
      };
      const mime = mimeMap[ext] || 'application/octet-stream';
      return `data:${mime};base64,${data.toString('base64')}`;
    } catch (e) {
      return null;
    }
  });

  ipcMain.handle('fs:readFile', async (event, filePath) => {
    try {
      return fs.readFileSync(filePath, 'utf-8');
    } catch (e) {
      return null;
    }
  });

  ipcMain.handle('fs:writeFile', async (event, filePath, content) => {
    try {
      fs.mkdirSync(path.dirname(filePath), { recursive: true });
      fs.writeFileSync(filePath, content, 'utf-8');
      return true;
    } catch (e) {
      return false;
    }
  });

  ipcMain.handle('fs:fileExists', async (event, filePath) => {
    return fs.existsSync(filePath);
  });

  ipcMain.handle('fs:openFolder', async (event, folderPath) => {
    shell.openPath(folderPath);
  });

  ipcMain.handle('fs:openExternal', async (event, url) => {
    shell.openExternal(url);
  });

  ipcMain.handle('fs:getImageBase64', async (event, filePath) => {
    try {
      const data = fs.readFileSync(filePath);
      const ext = path.extname(filePath).toLowerCase().replace('.', '');
      const mimeMap = { jpg: 'jpeg', jpeg: 'jpeg', png: 'png', webp: 'webp', gif: 'gif' };
      const mime = mimeMap[ext] || 'jpeg';
      return `data:image/${mime};base64,${data.toString('base64')}`;
    } catch (e) {
      return null;
    }
  });

  ipcMain.handle('config:load', async () => {
    ensureConfigDir();
    try {
      if (fs.existsSync(configPath)) {
        return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      }
    } catch (e) {}
    return null;
  });

  ipcMain.handle('config:save', async (event, config) => {
    ensureConfigDir();
    try {
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8');
      return true;
    } catch (e) {
      return false;
    }
  });

  // Store API keys in a local file (hidden from config export)
  ipcMain.handle('config:saveApiKey', async (event, provider, key) => {
    ensureConfigDir();
    const keysPath = path.join(configDir, '.keys.json');
    let keys = {};
    try { keys = JSON.parse(fs.readFileSync(keysPath, 'utf-8')); } catch {}
    keys[provider] = key;
    fs.writeFileSync(keysPath, JSON.stringify(keys), 'utf-8');
    return true;
  });

  ipcMain.handle('config:loadApiKey', async (event, provider) => {
    const keysPath = path.join(configDir, '.keys.json');
    try {
      const keys = JSON.parse(fs.readFileSync(keysPath, 'utf-8'));
      return keys[provider] || null;
    } catch {
      return null;
    }
  });

  ipcMain.handle('remotion:detect', async (event, folderPath) => {
    if (!folderPath) return false;
    const indicators = [
      path.join(folderPath, 'remotion.config.ts'),
      path.join(folderPath, 'remotion.config.js'),
      path.join(folderPath, 'package.json'),
    ];
    for (const p of indicators) {
      if (fs.existsSync(p)) {
        if (p.endsWith('package.json')) {
          try {
            const pkg = JSON.parse(fs.readFileSync(p, 'utf-8'));
            if (pkg.dependencies?.remotion || pkg.devDependencies?.remotion) return true;
          } catch {}
        } else {
          return true;
        }
      }
    }
    return false;
  });

  ipcMain.handle('remotion:openStudio', async (event, folderPath) => {
    const { spawn } = require('child_process');
    spawn('npx', ['remotion', 'studio', '--no-open', '--port', '3333'], {
      cwd: folderPath,
      shell: true,
      detached: true,
      stdio: 'ignore',
    }).unref();
    setTimeout(() => shell.openExternal('http://localhost:3333'), 3000);
  });

  // Inicia Remotion studio em background (sem abrir browser)
  let remotionStudioProcess = null;
  ipcMain.handle('remotion:startStudio', async (event, folderPath) => {
    if (remotionStudioProcess) {
      try { remotionStudioProcess.kill(); } catch {}
      remotionStudioProcess = null;
    }
    if (!folderPath) return { started: false, error: 'No path' };
    const { spawn } = require('child_process');
    remotionStudioProcess = spawn('npx', ['remotion', 'studio', '--no-open', '--port', '3333'], {
      cwd: folderPath,
      shell: true,
      detached: false,
      stdio: 'pipe',
    });
    return { started: true };
  });

  // Checa se o servidor Remotion está rodando
  ipcMain.handle('remotion:checkServer', async () => {
    const http = require('http');
    return new Promise((resolve) => {
      const req = http.get('http://localhost:3333', (res) => {
        resolve({ online: true, status: res.statusCode });
      });
      req.on('error', () => resolve({ online: false }));
      req.setTimeout(1500, () => { req.destroy(); resolve({ online: false }); });
    });
  });
};

