#!/usr/bin/env python3
"""
오프라인 표준값 생성 CLI.

선수 영상 디렉토리에서 MediaPipe world_landmarks를 추출하고,
5대 핵심 포인트의 mean/std를 계산하여 JSON으로 저장한다.

사용법:
    python build_standard.py \
        --input-dir ./pro_videos/ \
        --output standards/enduro_standard.json \
        --min-samples 5
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from app.utils.mediapipe_runner import (
    angle_three_points,
    distance_3d,
    extract_world_landmarks,
    get_landmark,
    mean_visibility,
    midpoint,
)
from app.utils.video import extract_frames, validate_video

# 최소 유효 프레임 수 (미달 시 WARNING)
MIN_VALID_FRAMES = 100

# sanity check 범위 (Agent 3와 동일)
SANITY_BOUNDS: dict[str, tuple[float, float]] = {
    "spine_tilt_angle":         (-90.0,  90.0),
    "weight_transfer_delta_x":  (-1.0,   1.0),
    "left_elbow_angle":         (0.0,  180.0),
    "right_elbow_angle":        (0.0,  180.0),
    "left_elbow_drop":          (-0.5,   0.5),
    "right_elbow_drop":         (-0.5,   0.5),
    "left_knee_angle":          (0.0,  180.0),
    "right_knee_angle":         (0.0,  180.0),
    "knee_width_distance":      (0.0,   1.0),
    "left_ankle_angle":         (0.0,  180.0),
    "right_ankle_angle":        (0.0,  180.0),
    "left_heel_drop":           (-0.3,   0.3),
    "right_heel_drop":          (-0.3,   0.3),
    "head_tilt":                (-0.3,   0.3),
    "shoulder_level":           (-0.2,   0.2),
}


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("build_standard")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    return logger


def compute_metrics(frame_lms) -> dict[str, float] | None:
    """
    단일 프레임에서 5대 핵심 포인트 값을 계산한다.
    최소 visibility 미달 시 None 반환.
    """
    lm = frame_lms.landmarks

    # 최소 visibility 체크 (핵심 랜드마크만)
    key_indices = [0, 7, 8, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28, 31, 32]
    vis = mean_visibility(frame_lms, key_indices)
    if vis < 0.5:
        return None

    def lmp(i):
        return lm[i]

    # 1. 상체 전경각
    shoulder_mid = midpoint(lmp(11), lmp(12))
    hip_mid = midpoint(lmp(23), lmp(24))
    ankle_mid = midpoint(lmp(27), lmp(28))

    # 척추 벡터 vs 수직(Y축)
    spine_vec = np.array([shoulder_mid[0] - hip_mid[0],
                          shoulder_mid[1] - hip_mid[1],
                          shoulder_mid[2] - hip_mid[2]])
    vertical = np.array([0.0, 1.0, 0.0])
    norm_s = np.linalg.norm(spine_vec)
    if norm_s < 1e-9:
        return None
    cos_v = float(np.dot(spine_vec / norm_s, vertical))
    cos_v = max(-1.0, min(1.0, cos_v))
    spine_tilt = float(np.degrees(np.arccos(cos_v)))
    # 앞숙임이면 양수 부호 부여 (x축 방향으로 앞)
    if spine_vec[2] < 0:
        spine_tilt = -spine_tilt

    # ΔX 체중이동
    delta_x = float(hip_mid[0] - ankle_mid[0])

    # 2. 팔꿈치
    l_elbow_angle = angle_three_points(lmp(11), lmp(13), lmp(15))
    r_elbow_angle = angle_three_points(lmp(12), lmp(14), lmp(16))
    l_elbow_drop = lmp(13).y - lmp(11).y   # 처짐 = 양수
    r_elbow_drop = lmp(14).y - lmp(12).y

    # 3. 무릎
    l_knee_angle = angle_three_points(lmp(23), lmp(25), lmp(27))
    r_knee_angle = angle_three_points(lmp(24), lmp(26), lmp(28))
    knee_dist = distance_3d(lmp(25), lmp(26))

    # 4. 발목
    l_ankle_angle = angle_three_points(lmp(25), lmp(27), lmp(31))
    r_ankle_angle = angle_three_points(lmp(26), lmp(28), lmp(32))
    l_heel_drop = lmp(27).y - lmp(31).y
    r_heel_drop = lmp(28).y - lmp(32).y

    # 5. 시선/두부
    ear_mid_y = (lmp(7).y + lmp(8).y) / 2
    head_tilt = lmp(0).y - ear_mid_y
    shoulder_level = lmp(11).y - lmp(12).y

    return {
        "spine_tilt_angle":         spine_tilt,
        "weight_transfer_delta_x":  delta_x,
        "left_elbow_angle":         l_elbow_angle,
        "right_elbow_angle":        r_elbow_angle,
        "left_elbow_drop":          l_elbow_drop,
        "right_elbow_drop":         r_elbow_drop,
        "left_knee_angle":          l_knee_angle,
        "right_knee_angle":         r_knee_angle,
        "knee_width_distance":      knee_dist,
        "left_ankle_angle":         l_ankle_angle,
        "right_ankle_angle":        r_ankle_angle,
        "left_heel_drop":           l_heel_drop,
        "right_heel_drop":          r_heel_drop,
        "head_tilt":                head_tilt,
        "shoulder_level":           shoulder_level,
    }


def process_video(
    video_path: str,
    sample_fps: float,
    model_complexity: int,
    logger: logging.Logger,
) -> tuple[list[dict], list]:
    """단일 영상을 처리하여 유효 프레임 메트릭과 랜드마크를 반환."""
    logger.info(f"Processing: {Path(video_path).name}")

    validation = validate_video(video_path)
    if not validation["valid"]:
        logger.warning(f"  SKIP: {validation['reason']}")
        return [], []

    frames, timestamps = extract_frames(video_path, sample_fps=sample_fps)
    logger.info(f"  Extracted {len(frames)} frames")

    frame_landmarks = extract_world_landmarks(frames, model_complexity=model_complexity)

    valid_metrics = []
    valid_landmarks = []
    rejected = 0

    for i, fl in enumerate(frame_landmarks):
        if fl is None:
            rejected += 1
            continue
        fl.timestamp_ms = timestamps[i]
        metrics = compute_metrics(fl)
        if metrics is None:
            rejected += 1
            continue
        valid_metrics.append(metrics)
        valid_landmarks.append(fl)

    logger.info(f"  Accepted: {len(valid_metrics)} / Rejected: {rejected}")
    return valid_metrics, valid_landmarks


def build_ideal_skeleton(all_valid_landmarks: list) -> list[dict]:
    """유효 랜드마크들의 평균을 이상적 스켈레톤으로 사용."""
    if not all_valid_landmarks:
        return []

    from app.utils.mediapipe_runner import LANDMARK_NAMES
    n_landmarks = len(all_valid_landmarks[0].landmarks)
    coords = {i: {"x": [], "y": [], "z": []} for i in range(n_landmarks)}

    for fl in all_valid_landmarks:
        for i, lm in enumerate(fl.landmarks):
            coords[i]["x"].append(lm.x)
            coords[i]["y"].append(lm.y)
            coords[i]["z"].append(lm.z)

    skeleton = []
    for i in range(n_landmarks):
        if coords[i]["x"]:
            skeleton.append({
                "index": i,
                "name": LANDMARK_NAMES.get(i, f"LANDMARK_{i}"),
                "x": float(np.mean(coords[i]["x"])),
                "y": float(np.mean(coords[i]["y"])),
                "z": float(np.mean(coords[i]["z"])),
            })
    return skeleton


def aggregate(all_metrics: list[dict]) -> dict[str, dict]:
    """전체 프레임의 지표를 집계하여 mean/std/min_valid/max_valid 반환."""
    result = {}
    metric_names = list(SANITY_BOUNDS.keys())

    for name in metric_names:
        vals = [m[name] for m in all_metrics if name in m]
        if not vals:
            continue
        arr = np.array(vals, dtype=float)
        bounds = SANITY_BOUNDS[name]
        result[name] = {
            "mean":      float(np.mean(arr)),
            "std":       float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
            "min":       float(np.min(arr)),
            "max":       float(np.max(arr)),
            "median":    float(np.median(arr)),
            "min_valid": bounds[0],
            "max_valid": bounds[1],
            "n":         len(vals),
        }

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build enduro standard pose data")
    parser.add_argument("--input-dir", required=True, help="Directory containing .mp4/.mov files")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--sample-fps", type=float, default=3.0)
    parser.add_argument("--complexity", type=int, default=1, choices=[0, 1, 2])
    parser.add_argument("--min-samples", type=int, default=5)
    args = parser.parse_args()

    logger = setup_logging()

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        logger.error(f"Input directory not found: {input_dir}")
        return 1

    video_files = sorted(
        list(input_dir.glob("*.mp4")) + list(input_dir.glob("*.mov"))
    )
    if not video_files:
        logger.error(f"No .mp4/.mov files found in {input_dir}")
        return 1

    logger.info(f"Found {len(video_files)} videos in {input_dir}")

    all_metrics: list[dict] = []
    all_landmarks = []
    video_count = 0

    for vf in video_files:
        metrics, landmarks = process_video(
            str(vf), args.sample_fps, args.complexity, logger
        )
        if metrics:
            all_metrics.extend(metrics)
            all_landmarks.extend(landmarks)
            video_count += 1
        logger.info(f"  Running total: {len(all_metrics)} valid frames from {video_count} videos")

    if video_count < args.min_samples:
        logger.warning(f"Only {video_count} valid videos (min: {args.min_samples})")

    if len(all_metrics) < MIN_VALID_FRAMES:
        logger.warning(f"Only {len(all_metrics)} valid frames (min: {MIN_VALID_FRAMES})")
        if len(all_metrics) == 0:
            logger.error("No valid frames — cannot build standard")
            return 1

    angle_stats = aggregate(all_metrics)
    ideal_skeleton = build_ideal_skeleton(all_landmarks)

    output = {
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_count": video_count,
        "n_frames": len(all_metrics),
        "angles": angle_stats,
        "ideal_skeleton_3d": ideal_skeleton,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info("=" * 50)
    logger.info("SUMMARY")
    logger.info(f"Videos processed : {video_count}")
    logger.info(f"Total valid frames: {len(all_metrics)}")
    for name, stats in angle_stats.items():
        logger.info(f"  {name}: mean={stats['mean']:.2f} std={stats['std']:.2f} (n={stats['n']})")
    logger.info(f"Output: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
