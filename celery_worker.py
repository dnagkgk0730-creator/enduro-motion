"""
Celery 워커 진입점.

실행:
    celery -A celery_worker worker --concurrency=2 --loglevel=info
"""
from __future__ import annotations

import logging
import os

from celery import Celery

from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Celery 앱 구성
celery_app = Celery(
    "enduro_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.pipeline.orchestrator"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,           # 태스크 완료 후 ack (재시작 안전)
    worker_prefetch_multiplier=1,  # 워커당 태스크 1개씩 처리 (무거운 작업)
    task_track_started=True,
)

# orchestrator의 celery_app에 동일 설정 주입
from app.pipeline.orchestrator import celery_app as orchestrator_celery
orchestrator_celery.conf.update(
    broker_url=settings.redis_url,
    result_backend=settings.redis_url,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
)

# 워커 기동 시 표준값 싱글톤 워밍업
try:
    from app.utils.standards_loader import load_standards
    load_standards(settings.standards_path)
    logger.info(f"Worker: standards loaded from {settings.standards_path}")
except FileNotFoundError:
    logger.warning(
        f"Worker: standards file not found ({settings.standards_path}) — "
        "run build_standard.py first"
    )

app = orchestrator_celery
