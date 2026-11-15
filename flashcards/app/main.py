from fastapi import FastAPI

from Routers import api_router

app = FastAPI(title="Flashcards API")
app.include_router(api_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
