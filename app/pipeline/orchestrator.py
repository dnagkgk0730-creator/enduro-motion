from __future__ import annotations

import logging
import time
from pathlib import Path

from celery import Celery

from app import pipeline  # noqa: F401  (circular import 방지용 lazy import)

logger = logging.getLogger(__name__)

# Celery 앱 — 설정은 celery_worker.py에서 주입
celery_app = Celery(__name__)


@celery_app.task(bind=True, max_retries=0, name="run_pipeline")
def run_pipeline(self, job_id: str, video_path: str) -> None:
    """
    단일 Celery 태스크 내에서 Agent 1 → 2 → 3을 순차 함수 호출.

    중요 제약:
    - chain() 분리 절대 금지 — NumPy 배열 직렬화 불가
    - Agent 2 완료 후 frames 명시 해제 (OOM 방지)
    - 표준값은 싱글톤 참조 (디스크 읽기 없음)
    """
    # import here to avoid circular at module load
    from app.agents.agent1_data_processor import DataProcessorAgent
    from app.agents.agent2_analyzer import AnalysisAgent
    from app.agents.agent3_inspector import InspectionAgent
    from app.pipeline import job_store
    from app.utils.standards_loader import load_standards

    start_ns = time.perf_counter_ns()
    job_store.set_status(job_id, "processing")

    try:
        # 표준값 싱글톤 참조 (프로세스당 1회 로드)
        standards = load_standards()

        # Agent 1: 영상 검증 + 프레임 추출
        preprocessed = DataProcessorAgent().run(job_id, video_path, standards)

        # Agent 2: MediaPipe + 5대 포인트 분석
        analysis = AnalysisAgent().run(preprocessed)

        # Agent 2 완료 즉시 프레임 메모리 해제 (OOM 방지)
        del preprocessed.frames
        preprocessed.frames = []

        # Agent 3: 검수 + 시각화 페이로드 조립
        payload = InspectionAgent().run(analysis, start_time_ns=start_ns)

        job_store.set_result(job_id, payload)
        job_store.set_status(job_id, "complete")

        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1e6
        logger.info(f"[{job_id}] Pipeline complete in {elapsed_ms:.0f}ms")

    except Exception as exc:
        logger.exception(f"[{job_id}] Pipeline failed: {exc}")
        job_store.set_status(job_id, "failed")
        job_store.set_error(job_id, str(exc))
        raise

    finally:
        # 업로드된 임시 파일 삭제
        Path(video_path).unlink(missing_ok=True)
