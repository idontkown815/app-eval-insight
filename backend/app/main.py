import os
import shutil
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import __version__, config
from app.models.database import init_db
from app.api.routes import router as api_router


def _bootstrap_sample_data():
    """打包模式下首次启动：把内置样本数据复制到用户数据目录。"""
    if not config.BACKEND_DATA_DIR:
        return  # 开发模式跳过

    data_dir = Path(config.BACKEND_DATA_DIR)
    cache_dir = Path(config.CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # 定位 PyInstaller 内置样本数据（onefile 模式在 _MEIPASS）
    bundled_data = None
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", str(Path(sys.executable).parent))
        bundled_data = Path(base) / "data"

    if not bundled_data or not bundled_data.exists():
        return

    # 缓存目录为空时复制样本评价
    bundled_cache = bundled_data / "cache"
    if bundled_cache.exists() and not any(cache_dir.iterdir()):
        shutil.copytree(bundled_cache, cache_dir, dirs_exist_ok=True)

    # 复制导入测试样本
    for name in ("sample_reviews.csv", "sample_reviews.json"):
        src = bundled_data / name
        dst = data_dir / name
        if src.exists() and not dst.exists():
            shutil.copy(src, dst)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _bootstrap_sample_data()
    yield


app = FastAPI(
    title="App Review Insight",
    version=__version__,
    lifespan=lifespan,
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# 打包模式：FastAPI 托管前端静态文件（挂载在 "/"，捕获所有非 /api 请求）
# 必须在 API 路由之后挂载，确保 /api/* 优先匹配
if config.STATIC_DIR and Path(config.STATIC_DIR).is_dir():
    app.mount("/", StaticFiles(directory=config.STATIC_DIR, html=True), name="frontend")
