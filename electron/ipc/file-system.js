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
    spawn('npx', ['remotion', 'studio'], {
      cwd: folderPath,
      shell: true,
      detached: true,
      stdio: 'ignore',
    }).unref();
    setTimeout(() => shell.openExternal('http://localhost:3000'), 3000);
  });
};
