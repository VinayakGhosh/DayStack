from fastapi import FastAPI
import asyncio
import logging
from routes import api_router
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from attachment_cleanup_worker import run_attachment_cleanup_worker

load_dotenv()


def _cors_origins() -> list[str]:
    """Read explicit browser origins from the deployment environment."""
    configured = os.getenv("CORS_ALLOWED_ORIGINS", "")
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = asyncio.Event()
    cleanup_worker = asyncio.create_task(run_attachment_cleanup_worker(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        await cleanup_worker

app = FastAPI(
    title="DayStack API",
    description="API for the DayStack MVP",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def default():
    return{"msg": "Hello world"}

app.include_router(api_router, prefix="/v1")
