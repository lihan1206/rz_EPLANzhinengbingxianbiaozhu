import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.logging import setup_logging
from app.services.seed import seed_initial_data

settings = get_settings()
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[item.strip() for item in settings.cors_origins.split(",") if item.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception):
    logger.exception("未处理异常: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误，请稍后重试"})


@app.on_event("startup")
def on_startup() -> None:
    max_retry = 20
    for attempt in range(1, max_retry + 1):
        try:
            Base.metadata.create_all(bind=engine)
            with SessionLocal() as db:
                seed_initial_data(db)
            logger.info("数据库初始化成功")
            return
        except OperationalError:
            logger.warning("数据库尚未就绪，重试 %s/%s", attempt, max_retry)
            time.sleep(2)

    raise RuntimeError("数据库启动失败，请检查连接配置")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


app.include_router(api_router)
