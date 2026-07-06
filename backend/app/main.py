from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from .api.ranking import router as ranking_router
from .api.sector import router as sector_router
from .api.stock import router as stock_router
from .api.watchlist import router as watchlist_router
from .config import get_settings
from .database import check_database_connection, initialize_database


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(ranking_router)
app.include_router(sector_router)
app.include_router(stock_router)
app.include_router(watchlist_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    try:
        database_status = "ok" if check_database_connection() else "error"
    except SQLAlchemyError:
        database_status = "error"

    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "database": database_status,
    }
