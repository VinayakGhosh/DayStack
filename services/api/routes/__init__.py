from fastapi import APIRouter
from routes.users import router as users_router
from routes.projects import router as projects_router
from routes.tasks import router as tasks_router
from routes.health import router as health_router
from routes.today import router as today_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(users_router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(projects_router, prefix='/project', tags=["Projects"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(today_router, prefix="/today", tags=["Today"])
