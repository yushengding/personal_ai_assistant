const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mainWindow = null;
let backendProcess = null;

function startBackend() {
  const projectRoot = path.resolve(__dirname, '..', '..');
  const venvPython = path.join(projectRoot, '.venv', 'Scripts', 'python.exe');
  const fallbackPy = 'py';
  const backendScript = path.join(projectRoot, 'scripts', 'run_backend.py');

  const useVenv = require('fs').existsSync(venvPython);
  const cmd = useVenv ? venvPython : fallbackPy;
  const args = useVenv ? [backendScript] : ['-3', backendScript];

  backendProcess = spawn(cmd, args, {
    cwd: projectRoot,
    stdio: 'inherit',
    shell: false,
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 900,
    minWidth: 1100,
    minHeight: 720,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadURL('http://127.0.0.1:8000/ui');
}

app.whenReady().then(() => {
  startBackend();
  setTimeout(createWindow, 1500);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  if (backendProcess) {
    try {
      backendProcess.kill();
    } catch (_) {}
  }
});
