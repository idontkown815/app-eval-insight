import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def _resolve_env_file():
    """查找 .env 配置文件，支持打包模式（PyInstaller）。"""
    candidates = []

    env_file = os.getenv("ENV_FILE")
    if env_file:
        candidates.append(Path(env_file))

    if _is_frozen():
        exe_dir = Path(sys.executable).parent
        candidates.append(exe_dir / "config.env")
        candidates.append(exe_dir / ".env")

    candidates.append(Path.cwd() / ".env")

    for c in candidates:
        if c.exists():
            return c
    return None


_env_path = _resolve_env_file()
if load_dotenv and _env_path:
    load_dotenv(_env_path)

# 由 Electron 主进程注入：指向用户数据目录（持久化数据存放处）
BACKEND_DATA_DIR = os.getenv("BACKEND_DATA_DIR", "")


LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
APP_STORE_REGION = os.getenv("APP_STORE_REGION", "us")
REQUEST_DELAY_SECONDS = int(os.getenv("REQUEST_DELAY_SECONDS", "1"))

CACHE_VALIDITY_DAYS = int(os.getenv("CACHE_VALIDITY_DAYS", "7"))


def _resolve_data_path(env_key: str, default_rel: str) -> str:
    """清晰的三段式：环境变量 > 数据目录 > 开发默认相对路径。"""
    val = os.getenv(env_key)
    if val:
        return val
    if BACKEND_DATA_DIR:
        return str(Path(BACKEND_DATA_DIR) / default_rel)
    return "./data/" + default_rel


CACHE_DIR = _resolve_data_path("CACHE_DIR", "cache")
DB_PATH = _resolve_data_path("DB_PATH", "db/app_review.db")

# 打包后由 Electron 注入：前端静态文件目录（开发模式为空，走 Vite 代理）
STATIC_DIR = os.getenv("STATIC_DIR", "")


class AppConfig:
    LLM_API_KEY = LLM_API_KEY
    LLM_BASE_URL = LLM_BASE_URL
    LLM_MODEL = LLM_MODEL
    BACKEND_HOST = BACKEND_HOST
    BACKEND_PORT = BACKEND_PORT
    APP_STORE_REGION = APP_STORE_REGION
    REQUEST_DELAY_SECONDS = REQUEST_DELAY_SECONDS
    CACHE_VALIDITY_DAYS = CACHE_VALIDITY_DAYS
    CACHE_DIR = CACHE_DIR
    DB_PATH = DB_PATH
    STATIC_DIR = STATIC_DIR
    BACKEND_DATA_DIR = BACKEND_DATA_DIR
