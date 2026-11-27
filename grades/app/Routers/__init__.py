from fastapi import APIRouter

from . import grading, modules, statistics, submodules, years

api_router = APIRouter(prefix="/api")
api_router.include_router(years.router)
api_router.include_router(modules.router)
api_router.include_router(submodules.router)
api_router.include_router(statistics.router)
api_router.include_router(grading.router)
