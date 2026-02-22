from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import RegisterTortoise

from app.config import TORTOISE_ORM
from app.routes.auth import router as auth_router
from app.routes.bookmarks import router as bookmarks_router
from app.routes.sentences import router as sentences_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with RegisterTortoise(app, config=TORTOISE_ORM, generate_schemas=True):
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
app.include_router(sentences_router)
app.include_router(bookmarks_router)
