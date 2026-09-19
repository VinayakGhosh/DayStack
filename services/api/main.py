from fastapi import FastAPI
import logging
from routes import api_router
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from models import register_models

load_dotenv()
register_models()


def _cors_origins() -> list[str]:
    """Read explicit browser origins from the deployment environment."""
    configured = os.getenv("CORS_ALLOWED_ORIGINS", "")
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
app = FastAPI(
    title="DayStack API",
    description="API for the DayStack MVP",
    version="1.0.0",
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
