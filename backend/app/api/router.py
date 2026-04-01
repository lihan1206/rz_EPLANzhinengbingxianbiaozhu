from fastapi import APIRouter

from app.api import analysis, annotations, auth, dashboard, exports, imports, json_analysis, logs, projects, users

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(imports.router)
api_router.include_router(analysis.router)
api_router.include_router(json_analysis.router)
api_router.include_router(annotations.router)
api_router.include_router(dashboard.router)
api_router.include_router(users.router)
api_router.include_router(exports.router)
api_router.include_router(logs.router)
