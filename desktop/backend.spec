# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: 跨平台打包 Python 后端为单文件二进制
# 用法: pyinstaller --noconfirm --distpath ../backend/dist --workpath ../backend/build --specpath . backend.spec
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

# spec 文件所在目录（desktop/）
spec_dir = Path(SPECPATH).resolve()
backend_dir = spec_dir.parent / 'backend'

# 要打包进二进制的样本数据
datas = [
    # 缓存的样本评价（首次启动复制到用户数据目录）
    (str(backend_dir / 'data' / 'cache'), os.path.join('data', 'cache')),
    (str(backend_dir / 'data' / 'sample_reviews.csv'), 'data'),
    (str(backend_dir / 'data' / 'sample_reviews.json'), 'data'),
    # 配置模板（Electron 启动时复制为 config.env）
    (str(backend_dir / '.env.example'), '.'),
]

# 显式声明 app 包及其所有子模块，避免动态导入遗漏
hiddenimports = ['app', 'dotenv', 'uvicorn.logging', 'uvicorn.lifespan.on', 'uvicorn.protocols.websockets.auto']
hiddenimports += collect_submodules('app')

a = Analysis(
    [str(backend_dir / 'run.py')],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除无关的大型库，减小体积
        'tkinter', 'matplotlib', 'PyQt5', 'PySide2', 'PySide6',
        'IPython', 'notebook', 'jupyter', 'pytest',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# onefile 模式：所有 binaries/datas 打进单个 EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='app-review-insight-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll', 'python3.dll', 'msvcp140.dll',
    ],
    runtime_tmpdir=None,
    # GUI 模式：不显示控制台窗口（后端日志通过 run.py 重定向到文件）
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
