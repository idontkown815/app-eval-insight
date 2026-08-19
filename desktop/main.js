// Electron 主进程：启动 Python 后端 + 创建原生窗口 + 健康检查
const { app, BrowserWindow, Menu, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const http = require('http');

const isDev = process.argv.includes('--dev');
const BACKEND_HOST = '127.0.0.1';
const BACKEND_PORT = 8000;
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

let mainWindow = null;
let backendProcess = null;
let backendReady = false;

// ---------- 路径解析 ----------

function getBackendCommand() {
  // 开发模式：直接用 python 跑 run.py
  if (isDev) {
    const backendDir = path.join(__dirname, '..', 'backend');
    // Windows 用 python，其他平台用 python3
    const py = process.platform === 'win32' ? 'python' : 'python3';
    return { cmd: py, args: [path.join(backendDir, 'run.py')], cwd: backendDir };
  }
  // 打包模式：用 PyInstaller 产出的后端二进制
  const exeName = process.platform === 'win32'
    ? 'app-review-insight-backend.exe'
    : 'app-review-insight-backend';
  const backendExe = path.join(process.resourcesPath, 'backend', exeName);
  return { cmd: backendExe, args: [], cwd: path.dirname(backendExe) };
}

function getFrontendTarget() {
  if (isDev) {
    return { type: 'url', target: 'http://localhost:5173' };
  }
  // 打包模式：FastAPI 自服务前端静态文件
  return { type: 'url', target: BACKEND_URL };
}

// ---------- 配置文件管理 ----------

function ensureConfigFile() {
  const dataDir = app.getPath('userData');
  const envFile = path.join(dataDir, 'config.env');

  if (!fs.existsSync(envFile)) {
    let template = '# App Review Insight 配置\nLLM_API_KEY=\nLLM_BASE_URL=https://api.openai.com/v1\nLLM_MODEL=gpt-4o-mini\n';
    try {
      const templatePath = path.join(process.resourcesPath, 'config.env.example');
      if (fs.existsSync(templatePath)) {
        template = fs.readFileSync(templatePath, 'utf8');
      }
    } catch (e) {
      // 资源目录不存在（开发模式），用默认模板
    }
    fs.writeFileSync(envFile, template, 'utf8');
    console.log(`[main] created config at ${envFile}`);
  }
  return envFile;
}

// ---------- 后端进程管理 ----------

function startBackend() {
  const { cmd, args, cwd } = getBackendCommand();
  const dataDir = app.getPath('userData');
  const envFile = ensureConfigFile();

  const env = {
    ...process.env,
    BACKEND_DATA_DIR: dataDir,
    ENV_FILE: envFile,
    BACKEND_HOST: BACKEND_HOST,
    BACKEND_PORT: String(BACKEND_PORT),
    // 打包模式让 FastAPI 托管前端静态文件
    STATIC_DIR: isDev ? '' : path.join(process.resourcesPath, 'frontend'),
    PYTHONUNBUFFERED: '1',
    // 防止 Python 缓存写失败
    PYTHONDONTWRITEBYTECODE: '1',
  };

  console.log(`[main] starting backend: ${cmd} ${args.join(' ')}`);

  backendProcess = spawn(cmd, args, {
    env,
    cwd,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  backendProcess.stdout.on('data', (d) => {
    console.log(`[backend] ${d.toString().trim()}`);
  });
  backendProcess.stderr.on('data', (d) => {
    console.error(`[backend] ${d.toString().trim()}`);
  });
  backendProcess.on('exit', (code, signal) => {
    console.log(`[main] backend exited code=${code} signal=${signal}`);
    if (!app.isQuitting && code !== 0 && code !== null) {
      dialog.showErrorBox(
        'Backend Error',
        `后端进程意外退出（code=${code}）。请查看日志：\n${path.join(dataDir, 'logs', 'backend.log')}`
      );
    }
  });
}

function waitForBackend(callback) {
  const maxAttempts = 120; // 60 秒超时
  let attempts = 0;

  const check = () => {
    attempts++;
    const req = http.get(`${BACKEND_URL}/api/health`, (res) => {
      if (res.statusCode === 200) {
        backendReady = true;
        callback();
        return;
      }
      if (attempts < maxAttempts) {
        setTimeout(check, 500);
      } else {
        console.error('[main] backend health check timed out');
        callback(); // 超时也尝试加载，让用户看到错误页
      }
      res.resume();
    });
    req.on('error', () => {
      if (attempts < maxAttempts) {
        setTimeout(check, 500);
      } else {
        callback();
      }
    });
    req.end();
  };
  check();
}

// ---------- 窗口管理 ----------

function createWindow() {
  const { target } = getFrontendTarget();

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'App Review Insight',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  mainWindow.loadURL(target);

  if (isDev) {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }

  // 外部链接在默认浏览器打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http://localhost') || url.startsWith('http://127.0.0.1')) {
      return { action: 'allow' };
    }
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ---------- 应用菜单 ----------

function buildMenu() {
  const dataDir = app.getPath('userData');
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Edit Configuration...',
          click: () => {
            const cfg = path.join(dataDir, 'config.env');
            shell.openPath(cfg);
          },
        },
        {
          label: 'Open Data Folder',
          click: () => shell.openPath(dataDir),
        },
        {
          label: 'View Backend Log',
          click: () => {
            const logPath = path.join(dataDir, 'logs', 'backend.log');
            if (fs.existsSync(logPath)) {
              shell.openPath(logPath);
            } else {
              dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'Log',
                message: '暂无日志文件',
                detail: `路径: ${logPath}`,
              });
            }
          },
        },
        { type: 'separator' },
        { role: 'quit' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About',
              message: 'App Review Insight',
              detail: '美国 App Store 评价智能分析平台\nv0.1.0',
            });
          },
        },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// ---------- 生命周期 ----------

app.whenReady().then(() => {
  startBackend();
  buildMenu();

  waitForBackend(() => {
    createWindow();
  });
});

app.on('window-all-closed', () => {
  // Mac 上保留进程，其他平台退出
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    if (backendReady) {
      createWindow();
    } else {
      waitForBackend(() => createWindow());
    }
  }
});

app.on('before-quit', (e) => {
  app.isQuitting = true;
  if (backendProcess) {
    e.preventDefault();
    console.log('[main] stopping backend...');
    try {
      // Windows 用 taskkill 确保子进程树退出
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', String(backendProcess.pid), '/f', '/t']);
      } else {
        backendProcess.kill('SIGTERM');
      }
    } catch (err) {
      console.error('[main] failed to stop backend:', err);
    }
    setTimeout(() => app.exit(0), 1000);
  }
});
