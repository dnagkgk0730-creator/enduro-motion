from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.responses import AnalyzeResponse, StatusResponse
from app.pipeline import job_store
from app.pipeline.orchestrator import run_pipeline

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".mov"}
MAX_SIZE_BYTES = settings.max_video_size_mb * 1024 * 1024


@router.post("/analyze", response_model=AnalyzeResponse, status_code=202)
async def analyze(video: UploadFile = File(...)):
    # 확장자 검증
    ext = Path(video.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Use .mp4 or .mov",
        )

    # 파일 크기 검증 (Content-Length 기반 사전 체크)
    content = await video.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: max {settings.max_video_size_mb}MB",
        )

    # 업로드 디렉토리 확보
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 고유 job ID + 임시 파일 저장
    job_id = str(uuid.uuid4())
    video_path = str(upload_dir / f"{job_id}{ext}")
    with open(video_path, "wb") as f:
        f.write(content)

    # job 상태 등록 + Celery 태스크 enqueue
    job_store.set_status(job_id, "queued")
    run_pipeline.delay(job_id, video_path)

    return AnalyzeResponse(job_id=job_id, status="queued")


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    status = job_store.get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return StatusResponse(job_id=job_id, status=status)


@router.get("/result/{job_id}")
async def get_result(job_id: str):
    status = job_store.get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if status == "failed":
        error = job_store.get_error(job_id) or "Unknown error"
        raise HTTPException(status_code=500, detail=error)

    if status in ("queued", "processing"):
        return JSONResponse(
            status_code=202,
            content={"job_id": job_id, "status": status, "message": "Analysis in progress"},
        )

    result = job_store.get_result(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")

    return JSONResponse(content=result)
