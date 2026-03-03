from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import RegisterTortoise

from app.config import TORTOISE_ORM
from app.routes.auth import router as auth_router
from app.routes.books import router as books_router
from app.routes.events import router as events_router
from app.routes.favorites import router as favorites_router
from app.routes.garden import router as garden_router
from app.services.book import load_books


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_books()
    async with RegisterTortoise(app, config=TORTOISE_ORM, generate_schemas=False):
        yield


app = FastAPI(title="OneLiner API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(books_router)
app.include_router(events_router)
app.include_router(favorites_router)
app.include_router(garden_router)


@app.get("/")
@app.get("/health")
async def health():
    """健康检查端点。"""
    return {"status": "ok"}
