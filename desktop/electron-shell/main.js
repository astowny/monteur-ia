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
    // Dossier de log injecté dans le backend (utilisé par backend_entry.py
    // pour rediriger stdout/stderr quand frozen avec console=False).
    MONTEUR_LOG_DIR: app.getPath('userData'),
  };
}

function resolveBackendLaunch() {
  // Avec --onedir PyInstaller : resources/backend/monteur-backend/monteur-backend.exe
  const packagedExe = path.join(process.resourcesPath, 'backend', 'monteur-backend', 'monteur-backend.exe');
  if (app.isPackaged && fs.existsSync(packagedExe)) {
    return { command: packagedExe, args: [] };
  }

  // En dev : préférer 'py' (launcher Windows qui cible Python 3) puis python3 puis python.
  const pythonCmd = process.platform === 'win32' ? 'py' : 'python3';
  return {
    command: pythonCmd,
    args: [
      '-c',
      "from ai_service.main import create_fastapi_app; app=create_fastapi_app(); import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)",
    ],
  };
}

async function waitForBackendReady(timeoutMs = 40000) {
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
  if (backendProcess) return 'already_running';
  const config = loadConfig();
  const launch = resolveBackendLaunch();

  // Pipe stdout/stderr du backend vers un fichier log dans userData.
  // Cela permet de débugger les crashs silencieux (notamment en mode frozen
  // PyInstaller console=False où sys.stdout est None sans cette redirection).
  const logPath = path.join(app.getPath('userData'), 'backend.log');
  const logFd = fs.openSync(logPath, 'a');

  backendProcess = spawn(launch.command, launch.args, {
    env: backendEnv(config),
    stdio: ['ignore', logFd, logFd],
    detached: false,
  });

  // Le fd parent peut être fermé : l'enfant a sa propre copie.
  fs.closeSync(logFd);

  backendProcess.on('exit', (code) => {
    backendProcess = null;
    // Notifier toutes les fenêtres ouvertes si le backend s'arrête de façon inattendue.
    BrowserWindow.getAllWindows().forEach((w) =>
      w.webContents.send('backend:status', { ok: false, error: `Backend exited (code ${code})` })
    );
  });

  const ok = await waitForBackendReady();
  return ok ? 'ok' : 'timeout';
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
    show: false, // évite l'écran blanc au démarrage
    backgroundColor: '#0f172a',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  win.loadFile('renderer.html');
  win.once('ready-to-show', () => win.show());
}

app.whenReady().then(async () => {
  ipcMain.handle('config:get', () => loadConfig());
  ipcMain.handle('config:save', async (_event, conf) => {
    saveConfig(conf);
    stopBackend();
    const result = await startBackend();
    return { ok: result === 'ok', status: result };
  });

  // Ouvrir la fenêtre immédiatement — le bandeau de statut s'affiche pendant le boot.
  createWindow();

  // Démarrer le backend en arrière-plan et notifier le renderer du résultat.
  startBackend().then((result) => {
    BrowserWindow.getAllWindows().forEach((w) =>
      w.webContents.send('backend:status', {
        ok: result === 'ok',
        status: result,
        error: result !== 'ok' ? `Backend non disponible (${result})` : null,
      })
    );
  }).catch((err) => {
    BrowserWindow.getAllWindows().forEach((w) =>
      w.webContents.send('backend:status', { ok: false, error: String(err) })
    );
  });

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
