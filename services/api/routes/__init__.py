from fastapi import APIRouter
from routes.users import router as users_router
from routes.plans import router as plans_router
from routes.subscriptions import router as subscription_router
from routes.projects import router as projects_router
from routes.tasks import router as tasks_router
from routes.stats import router as stats_router
from routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(plans_router, prefix='/plans', tags=["Plans"])
api_router.include_router(subscription_router, prefix='/subscription', tags=["Subscriptions"])
api_router.include_router(projects_router, prefix='/project', tags=["Projects"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(stats_router, prefix="/stats", tags=["Stats"])