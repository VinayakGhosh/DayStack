from fastapi import FastAPI
from db.db import get_db
import logging
from models.user import Users
from models.plan import Plans
from models.Project import Projects, ProjectStatus
from models.Task import Tasks, TaskComment
from routes import api_router
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
from scheduler import scheduler

load_dotenv()


# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("proj-task")

@asynccontextmanager
async def lifespan(app:FastAPI):
    db: Session = next(get_db())

    logging.info("Checking if plan exist")
    # Create default plans if not already present
    default_plans = os.getenv("DEFAULT_PLANS", "Free, Pro").split(",")
    existing_plans = db.query(Plans.plan_tier).all()
    existing_plan_tier = {plan[0] for plan in existing_plans}

    plan_created = False
    for plan in default_plans:
        plan = plan.strip()
        if plan and plan not in existing_plan_tier:
            new_plan = Plans(
                plan_tier=plan,
                price=0 if plan=="Free" else 500,
                duration_days=30 if plan=="Pro" else None,
                max_projects=3 if plan=="Free" else 12,
                task_per_day=5 if plan=="Free" else 30,
                export_allowed=False if plan=="Free" else True
            )
            db.add(new_plan)
            plan_created = True
    
    if plan_created:
        db.commit()
        logger.info("Default plans created")
    else:
        logger.info("Default plans already exist")
    db.close()

    logger.info("Starting scheduler")
    scheduler.start()

    yield

    logging.info("Stopping scheduler")
    scheduler.shutdown()
    

app = FastAPI(
    title="Proj_Task",
    description="api for proj_task",
    version="0.3.6",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def default():
    return{"msg": "Hello world"}

app.include_router(api_router, prefix="/v1")