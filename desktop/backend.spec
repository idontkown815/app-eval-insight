# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: 跨平台打包 Python 后端为单文件二进制
# 用法: pyinstaller --noconfirm --distpath ../backend/dist --workpath ../backend/build backend.spec
import os
import platform
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

# spec 文件所在目录（desktop/）
spec_dir = Path(SPECPATH).resolve()
backend_dir = spec_dir.parent / 'backend'

# 判断当前平台
is_windows = platform.system() == 'Windows'
is_mac = platform.system() == 'Darwin'

# 要打包进二进制的样本数据（排除 cache 目录，体积过大且不需要）
# 注意：app_review.db 是运行时生成的，CI 环境中可能不存在，需要过滤
datas = []
for src, dst in [
    (backend_dir / 'data' / 'sample_reviews.csv', 'data'),
    (backend_dir / 'data' / 'sample_reviews.json', 'data'),
    (backend_dir / 'data' / 'db' / 'app_review.db', 'data/db'),
    (backend_dir / '.env.example', '.'),
]:
    if src.exists():
        datas.append((str(src), dst))

# 显式声明 app 包及其所有子模块，避免动态导入遗漏
hiddenimports = [
    'app',
    'dotenv',
    'dateutil',
    'dateutil.parser',
    'markdown',
    'uvicorn.logging',
    'uvicorn.lifespan.on',
    'uvicorn.protocols.websockets',
    'websockets',
]
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
        'tkinter', 'matplotlib', 'PyQt5', 'PySide2', 'PySide6',
        'IPython', 'notebook', 'jupyter', 'pytest',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# onefile 模式：所有 binaries/datas 打进单个可执行文件
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
    upx=False,
    upx_exclude=[] if not is_windows else [
        'vcruntime140.dll', 'python3.dll', 'msvcp140.dll',
    ],
    runtime_tmpdir=None,
    # CLI 模式：后端作为服务进程，需要控制台模式
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
