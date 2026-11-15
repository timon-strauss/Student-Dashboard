from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from Routers import api_router
import Services


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    Services.start()
    yield


app = FastAPI(title="Flashcards API", lifespan=lifespan)
app.include_router(api_router)


@app.exception_handler(Services.NotFoundError)
def handle_not_found(_: Request, error: Services.NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(error)})


@app.exception_handler(Services.InvalidImageError)
def handle_invalid_image(_: Request, error: Services.InvalidImageError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, content={"detail": str(error)})


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
