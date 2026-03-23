from __future__ import annotations

from pydantic import BaseModel


class AnalyzeResponse(BaseModel):
    job_id: str
    status: str = "queued"


class StatusResponse(BaseModel):
    job_id: str
    status: str   # "queued" | "processing" | "complete" | "failed"


class ErrorResponse(BaseModel):
    job_id: str
    error: str
