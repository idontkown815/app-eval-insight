# App Review Insight · 桌面版打包（Electron + PyInstaller）

将 Web 应用打包为 Windows / Mac 原生桌面应用。

## 架构

```
Electron 主进程 (main.js)
  ├─ BrowserWindow (原生窗口，加载 React 前端)
  └─ spawn → PyInstaller 后端二进制 (app-review-insight-backend)
              └─ FastAPI :8000 (自服务前端静态文件 + API)
```

- **开发模式**：前端走 Vite Dev Server (5173)，后端走 `python run.py`，Electron 加载 `localhost:5173`
- **打包模式**：前端 `npm run build` 产物由 FastAPI 托管，后端 PyInstaller 单文件，Electron 加载 `localhost:8000`

## 前置条件

- Node.js 20+
- Python 3.12+（与 backend/requirements.txt 一致）
- 全局/本地安装 PyInstaller：`pip install pyinstaller python-dotenv`

## 本地开发调试

```powershell
# 终端1：启动后端（带 reload）
cd backend
python run.py

# 终端2：启动前端（Vite Dev Server）
cd frontend
npm install
npm run dev

# 终端3：启动 Electron 壳（dev 模式会连接上述两个服务）
cd desktop
npm install
npm run dev
```

## 本地完整打包

```powershell
cd desktop
npm install
npm run build:all
# 产物：desktop/dist/App-Review-Insight-Setup-x.x.x.exe (Windows)
```

分步执行：
- `npm run build:frontend` → 产出 `frontend/dist/`
- `npm run build:backend` → 产出 `backend/dist/app-review-insight-backend(.exe)`
- `npm run build:electron` → electron-builder 组装安装包

## 跨平台构建（GitHub Actions）

由于 PyInstaller **不能交叉编译**（Windows exe 必须在 Windows 上打，Mac 二进制必须在 Mac 上打），跨平台构建通过 CI 完成：

```
.github/workflows/build.yml
  ├─ windows-latest runner → 产出 .exe
  └─ macos-latest runner  → 产出 .dmg
```

推送 `v*` 标签（如 `v0.1.0`）触发构建，或手动在 GitHub Actions 页面运行。产物上传为 Artifact，Mac 构建（arm64+x64）自动产出通用 DMG。

## 自定义图标

在 `desktop/build/` 下放入：
- `icon.png`（≥256×256，electron-builder 会自动生成各平台图标）

不提供图标时使用 Electron 默认图标。

## 用户数据目录

打包后所有持久化数据存于系统标准位置：
- **Windows**：`%APPDATA%/app-review-insight/`
- **Mac**：`~/Library/Application Support/app-review-insight/`

包含：`config.env`（LLM 配置）、`cache/`（评价缓存）、`db/`（SQLite）、`logs/backend.log`

首次启动会自动从内置样本数据复制 Facebook/Instagram 评价到用户目录，零配置即可体验。
