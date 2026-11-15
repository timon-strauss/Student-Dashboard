from fastapi import APIRouter

from . import cards, decks, exams, statistics

api_router = APIRouter(prefix="/api")
api_router.include_router(exams.router)
api_router.include_router(decks.router)
api_router.include_router(cards.router)
api_router.include_router(statistics.router)
