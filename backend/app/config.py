import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
APP_STORE_REGION = os.getenv("APP_STORE_REGION", "us")
REQUEST_DELAY_SECONDS = int(os.getenv("REQUEST_DELAY_SECONDS", "1"))

CACHE_VALIDITY_DAYS = int(os.getenv("CACHE_VALIDITY_DAYS", "7"))
CACHE_DIR = os.getenv("CACHE_DIR", "./data/cache")

DB_PATH = os.getenv("DB_PATH", "./data/db/app_review.db")


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
