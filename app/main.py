from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 기동 시 표준값 싱글톤 워밍업 (디스크 읽기 1회)
    from app.utils.standards_loader import load_standards
    try:
        load_standards(settings.standards_path)
        logger.info(f"Standards loaded: {settings.standards_path}")
    except FileNotFoundError:
        logger.warning(
            f"Standards file not found: {settings.standards_path} — "
            "run build_standard.py first"
        )
    yield


app = FastAPI(
    title="Enduro Motion API",
    description="엔듀로 바이크 3D 자세 분석 파이프라인",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
