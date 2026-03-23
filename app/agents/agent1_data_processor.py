from __future__ import annotations

import logging
import os

from app.models.contracts import PreprocessedData, StandardPoseData, VideoMetadata
from app.utils.video import extract_frames, validate_video

logger = logging.getLogger(__name__)

# 영상 유효성 제한
MAX_DURATION_SEC = 15.0
MIN_DURATION_SEC = 1.0
SAMPLE_FPS = 5.0   # 초당 추출 프레임 수


class DataProcessorAgent:
    """
    Agent 1: 영상 유효성 검증, 프레임 추출, 표준값 전달.

    책임:
    - 포맷/길이/해상도 검증
    - 프레임 추출 및 MediaPipe 최적 해상도로 리사이즈
    - 표준값 객체를 PreprocessedData에 포함하여 Agent 2로 전달
    """

    def run(
        self,
        job_id: str,
        video_path: str,
        standards: StandardPoseData,
        sample_fps: float = SAMPLE_FPS,
    ) -> PreprocessedData:
        logger.info(f"[{job_id}] Agent 1 start: {video_path}")

        # 1. 유효성 검증
        validation = validate_video(
            video_path,
            max_duration_sec=MAX_DURATION_SEC,
            min_duration_sec=MIN_DURATION_SEC,
        )
        if not validation["valid"]:
            raise ValueError(f"[{job_id}] Video validation failed: {validation['reason']}")

        meta = validation["meta"]
        logger.info(
            f"[{job_id}] Video OK — {meta['duration_sec']:.1f}s, "
            f"{meta['width']}x{meta['height']}, {meta['fps']:.1f}fps"
        )

        # 2. 포맷 확인 (.mp4 / .mov)
        ext = os.path.splitext(video_path)[1].lower().lstrip(".")
        if ext not in ("mp4", "mov"):
            raise ValueError(f"[{job_id}] Unsupported format: .{ext}")

        # 3. 프레임 추출
        frames, timestamps = extract_frames(video_path, sample_fps=sample_fps)
        logger.info(f"[{job_id}] Extracted {len(frames)} frames at {sample_fps}fps")

        if len(frames) == 0:
            raise ValueError(f"[{job_id}] No frames extracted from video")

        # 처리된 해상도 확인
        h, w = frames[0].shape[:2]

        video_meta = VideoMetadata(
            filename=os.path.basename(video_path),
            format=ext,
            duration_seconds=meta["duration_sec"],
            fps=meta["fps"],
            frame_count=meta["total_frames"],
            original_resolution=(meta["width"], meta["height"]),
            processed_resolution=(w, h),
        )

        logger.info(f"[{job_id}] Agent 1 complete — {len(frames)} frames ready")

        return PreprocessedData(
            job_id=job_id,
            video_meta=video_meta,
            frames=frames,
            frame_timestamps_ms=timestamps,
            standards=standards,
        )
