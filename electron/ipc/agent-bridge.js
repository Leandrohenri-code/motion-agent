const { spawn } = require('child_process');
const path = require('path');

module.exports = function registerAgentHandlers(ipcMain, initialWindow, getWindow) {
  let agentProcess = null;
  let buffer = '';

  function sendToRenderer(msg) {
    const win = getWindow();
    if (win && !win.isDestroyed()) {
      win.webContents.send('agent:message', msg);
    }
  }

  ipcMain.handle('agent:start', async (event, config) => {
    if (agentProcess) {
      agentProcess.kill();
      agentProcess = null;
    }

    const agentPath = path.join(__dirname, '../../agent/main_agent.py');
    const pythonBin = process.platform === 'win32' ? 'python' : 'python3';

    agentProcess = spawn(pythonBin, [agentPath], {
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    agentProcess.stdin.write(JSON.stringify(config) + '\n');

    agentProcess.stdout.on('data', (data) => {
      buffer += data.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop();
      lines.forEach((line) => {
        line = line.trim();
        if (!line) return;
        try {
          const msg = JSON.parse(line);
          sendToRenderer(msg);
        } catch {
          sendToRenderer({ type: 'log', level: 'info', message: line });
        }
      });
    });

    agentProcess.stderr.on('data', (data) => {
      sendToRenderer({ type: 'log', level: 'error', message: data.toString().trim() });
    });

    agentProcess.on('close', (code) => {
      agentProcess = null;
      sendToRenderer({ type: 'agent_closed', code });
    });

    return { started: true };
  });

  ipcMain.handle('agent:stop', async () => {
    if (agentProcess) {
      agentProcess.stdin.write(JSON.stringify({ type: 'abort' }) + '\n');
      setTimeout(() => {
        if (agentProcess) {
          agentProcess.kill();
          agentProcess = null;
        }
      }, 2000);
    }
    return { stopped: true };
  });

  ipcMain.handle('agent:send', async (event, msg) => {
    if (agentProcess && agentProcess.stdin.writable) {
      agentProcess.stdin.write(JSON.stringify(msg) + '\n');
      return true;
    }
    return false;
  });
};
