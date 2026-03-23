from __future__ import annotations

import dataclasses
import json
import os

import redis

# job TTL: 1시간 (분석 완료 후 자동 만료)
JOB_TTL_SEC = 3600

_client: redis.Redis | None = None


def _redis() -> redis.Redis:
    global _client
    if _client is None:
        url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        _client = redis.from_url(url, decode_responses=True)
    return _client


def set_status(job_id: str, status: str) -> None:
    _redis().setex(f"job:{job_id}:status", JOB_TTL_SEC, status)


def get_status(job_id: str) -> str | None:
    return _redis().get(f"job:{job_id}:status")


def set_result(job_id: str, payload) -> None:
    data = _serialize(payload)
    _redis().setex(f"job:{job_id}:result", JOB_TTL_SEC, data)


def get_result(job_id: str) -> dict | None:
    raw = _redis().get(f"job:{job_id}:result")
    if raw is None:
        return None
    return json.loads(raw)


def set_error(job_id: str, error_msg: str) -> None:
    _redis().setex(f"job:{job_id}:error", JOB_TTL_SEC, error_msg)


def get_error(job_id: str) -> str | None:
    return _redis().get(f"job:{job_id}:error")


def _serialize(obj) -> str:
    """dataclass 재귀 직렬화."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return json.dumps(dataclasses.asdict(obj), ensure_ascii=False)
    return json.dumps(obj, ensure_ascii=False)
