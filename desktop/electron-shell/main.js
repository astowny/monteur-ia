const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');

const BACKEND_PORT = 8000;
let backendProcess = null;

function configPath() {
  return path.join(app.getPath('userData'), 'monteur-config.json');
}

function defaultConfig() {
  return {
    MONTEUR_ENV: 'dev',
    MONTEUR_API_KEY: 'change-me',
    MONTEUR_TRANSCRIBE_MODE: 'local',
    WHISPER_API_URL: '',
    WHISPER_API_KEY: '',
    MONTEUR_SQLITE_PATH: path.join(app.getPath('userData'), 'monteur.db'),
    MONTEUR_FFMPEG_BIN: 'ffmpeg',
    MONTEUR_WHISPER_BIN: 'whisper',
  };
}

function loadConfig() {
  const file = configPath();
  if (!fs.existsSync(file)) {
    const conf = defaultConfig();
    fs.writeFileSync(file, JSON.stringify(conf, null, 2));
    return conf;
  }
  const conf = JSON.parse(fs.readFileSync(file, 'utf-8'));
  return { ...defaultConfig(), ...conf };
}

function saveConfig(conf) {
  fs.writeFileSync(configPath(), JSON.stringify(conf, null, 2));
}

function backendEnv(config) {
  return {
    ...process.env,
    ...config,
    PYTHONPATH: path.resolve(__dirname, '../../src'),
  };
}

function resolveBackendLaunch() {
  const packagedExe = path.join(process.resourcesPath, 'backend', 'monteur-backend.exe');
  if (app.isPackaged && fs.existsSync(packagedExe)) {
    return { command: packagedExe, args: [] };
  }

  return {
    command: process.platform === 'win32' ? 'python' : 'python3',
    args: [
      '-c',
      "from ai_service.main import create_fastapi_app; app=create_fastapi_app(); import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)",
    ],
  };
}

async function waitForBackendReady(timeoutMs = 20000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(`http://127.0.0.1:${BACKEND_PORT}/health`);
      if (res.ok) {
        return true;
      }
    } catch (_err) {
      // retry
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

async function startBackend() {
  if (backendProcess) return;
  const config = loadConfig();
  const launch = resolveBackendLaunch();

  backendProcess = spawn(launch.command, launch.args, {
    env: backendEnv(config),
    stdio: 'ignore',
    detached: false,
  });

  backendProcess.on('exit', () => {
    backendProcess = null;
  });

  const ok = await waitForBackendReady();
  if (!ok) {
    throw new Error('Backend did not start in time');
  }
}

function stopBackend() {
  if (!backendProcess) return;
  try {
    backendProcess.kill();
  } catch (_err) {
    // no-op
  }
  backendProcess = null;
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 850,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  win.loadFile('renderer.html');
}

app.whenReady().then(async () => {
  ipcMain.handle('config:get', () => loadConfig());
  ipcMain.handle('config:save', async (_event, conf) => {
    saveConfig(conf);
    stopBackend();
    await startBackend();
    return { ok: true };
  });

  await startBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('before-quit', () => {
  stopBackend();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
