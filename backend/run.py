import os
import sys
from pathlib import Path

import uvicorn
from app.config import BACKEND_HOST, BACKEND_PORT, BACKEND_DATA_DIR


def _redirect_stdio_when_frozen():
    """GUI 模式（console=False）下 sys.stdout/stderr 为 None，重定向到日志文件。"""
    if not getattr(sys, "frozen", False):
        return
    if sys.stdout is not None and sys.stderr is not None:
        return

    log_dir = Path(BACKEND_DATA_DIR) / "logs" if BACKEND_DATA_DIR else Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "backend.log"
    log_file = open(log_path, "a", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = log_file
    if sys.stderr is None:
        sys.stderr = log_file
    print(f"[{__import__('datetime').datetime.now()}] backend started, log -> {log_path}")


try:
    from app.main import app
except ImportError:
    from fastapi import FastAPI
    app = FastAPI(title="App Review Insight API")


if __name__ == "__main__":
    _redirect_stdio_when_frozen()

    # 打包模式关闭 reload（reload 会fork子进程，与 PyInstaller onefile 不兼容）
    use_reload = not getattr(sys, "frozen", False)

    uvicorn.run(
        "app.main:app",
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        reload=use_reload,
        log_level="info",
    )
