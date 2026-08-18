import uvicorn
from app.config import BACKEND_HOST, BACKEND_PORT

try:
    from app.main import app
except ImportError:
    from fastapi import FastAPI
    app = FastAPI(title="App Review Insight API")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        reload=True
    )
