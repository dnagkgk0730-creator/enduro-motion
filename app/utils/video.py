from __future__ import annotations

import cv2
import numpy as np

# MediaPipe 처리에 최적화된 해상도 (가로 기준)
MEDIAPIPE_TARGET_WIDTH = 640


def get_video_metadata(video_path: str) -> dict:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec = total_frames / fps if fps > 0 else 0.0

    cap.release()
    return {
        "fps": fps,
        "total_frames": total_frames,
        "width": width,
        "height": height,
        "duration_sec": duration_sec,
    }


def extract_frames(
    video_path: str,
    sample_fps: float = 5.0,
) -> tuple[list[np.ndarray], list[float]]:
    """
    영상에서 sample_fps 속도로 프레임을 추출한다.
    반환: (frames_bgr, timestamps_ms)
    전 프레임 디코딩 방지: CAP_PROP_POS_FRAMES으로 직접 점프.
    """
    meta = get_video_metadata(video_path)
    source_fps = meta["fps"]
    total_frames = meta["total_frames"]

    skip_interval = max(1, int(source_fps / sample_fps))

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    frames: list[np.ndarray] = []
    timestamps: list[float] = []

    frame_idx = 0
    while frame_idx < total_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break

        resized = _resize_for_mediapipe(frame)
        frames.append(resized)
        timestamps.append((frame_idx / source_fps) * 1000.0)  # ms

        frame_idx += skip_interval

    cap.release()
    return frames, timestamps


def _resize_for_mediapipe(frame_bgr: np.ndarray) -> np.ndarray:
    h, w = frame_bgr.shape[:2]
    if w <= MEDIAPIPE_TARGET_WIDTH:
        return frame_bgr
    scale = MEDIAPIPE_TARGET_WIDTH / w
    new_w = MEDIAPIPE_TARGET_WIDTH
    new_h = int(h * scale)
    return cv2.resize(frame_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)


def validate_video(
    video_path: str,
    max_duration_sec: float = 15.0,
    min_duration_sec: float = 1.0,
) -> dict:
    """
    영상 유효성 검증.
    반환: {"valid": bool, "reason": str | None, "meta": dict}
    """
    try:
        meta = get_video_metadata(video_path)
    except FileNotFoundError as e:
        return {"valid": False, "reason": str(e), "meta": {}}

    if meta["total_frames"] == 0:
        return {"valid": False, "reason": "No frames found (corrupt or empty file)", "meta": meta}

    if meta["duration_sec"] < min_duration_sec:
        return {
            "valid": False,
            "reason": f"Video too short: {meta['duration_sec']:.1f}s (min {min_duration_sec}s)",
            "meta": meta,
        }

    if meta["duration_sec"] > max_duration_sec:
        return {
            "valid": False,
            "reason": f"Video too long: {meta['duration_sec']:.1f}s (max {max_duration_sec}s)",
            "meta": meta,
        }

    if meta["width"] < 320 or meta["height"] < 240:
        return {
            "valid": False,
            "reason": f"Resolution too low: {meta['width']}x{meta['height']}",
            "meta": meta,
        }

    return {"valid": True, "reason": None, "meta": meta}
