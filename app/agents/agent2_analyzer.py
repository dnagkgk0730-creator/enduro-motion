from __future__ import annotations

import logging
import os

import numpy as np

from app.models.contracts import (
    AnalysisResult,
    Delta,
    FrameLandmarks,
    JointMeasurement,
    JointStats,
    KeyPointAnalysis,
    PreprocessedData,
    StandardPoseData,
)
from app.utils.mediapipe_runner import (
    angle_three_points,
    distance_3d,
    extract_world_landmarks,
    mean_visibility,
    midpoint,
)

logger = logging.getLogger(__name__)

# MediaPipe model complexity (env override 가능)
MODEL_COMPLEXITY = int(os.environ.get("MEDIAPIPE_MODEL_COMPLEXITY", "1"))


class AnalysisAgent:
    """
    Agent 2: MediaPipe world_landmarks 추출 + 5대 핵심 포인트 분석 + 표준값 비교.

    중요 제약:
    - 반드시 pose_world_landmarks 사용 (카메라 앵글 왜곡 방지)
    - world_landmarks: 골반 원점 기준 실제 미터 단위 3D 좌표
    - MediaPipe Context Manager는 mediapipe_runner.py에서 관리
    """

    def run(self, preprocessed: PreprocessedData) -> AnalysisResult:
        job_id = preprocessed.job_id
        standards = preprocessed.standards
        logger.info(f"[{job_id}] Agent 2 start — {len(preprocessed.frames)} frames")

        # 1. world_landmarks 추출
        frame_landmarks_raw = extract_world_landmarks(
            preprocessed.frames,
            model_complexity=MODEL_COMPLEXITY,
        )

        # timestamp 채우기
        for i, fl in enumerate(frame_landmarks_raw):
            if fl is not None and i < len(preprocessed.frame_timestamps_ms):
                fl.timestamp_ms = preprocessed.frame_timestamps_ms[i]

        # 유효 프레임만 추림
        valid_frames: list[FrameLandmarks] = [fl for fl in frame_landmarks_raw if fl is not None]
        total = len(frame_landmarks_raw)
        valid = len(valid_frames)
        logger.info(f"[{job_id}] Valid frames: {valid}/{total}")

        if valid == 0:
            raise ValueError(f"[{job_id}] No valid landmarks extracted — check video quality")

        # 2. 프레임별 메트릭 계산 후 중앙값 집계
        all_metrics = [_compute_frame_metrics(fl) for fl in valid_frames]
        # None 제거 (visibility 부족 프레임)
        all_metrics = [m for m in all_metrics if m is not None]

        if not all_metrics:
            raise ValueError(f"[{job_id}] All frames failed metric computation (low visibility)")

        logger.info(f"[{job_id}] Metrics computed: {len(all_metrics)} frames")

        # 3. 중앙값으로 대표값 산출 (이상치에 강건)
        kpa = _aggregate_to_representative(all_metrics, valid_frames)

        # 4. 표준값 대비 델타 계산
        deltas = _compute_deltas(kpa, standards)

        logger.info(f"[{job_id}] Agent 2 complete")

        return AnalysisResult(
            job_id=job_id,
            frame_landmarks=valid_frames,
            key_point_analysis=kpa,
            deltas=deltas,
            standards=standards,
            valid_frame_count=valid,
            total_frame_count=total,
        )


# ---------------------------------------------------------------------------
# 단일 프레임 메트릭 계산
# ---------------------------------------------------------------------------

def _compute_frame_metrics(fl: FrameLandmarks) -> dict | None:
    lm = fl.landmarks
    if len(lm) < 33:
        return None

    # 최소 visibility 체크
    key_idx = [0, 7, 8, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28, 31, 32]
    vis = mean_visibility(fl, key_idx)
    if vis < 0.4:
        return None

    def p(i):
        return lm[i]

    # 공통 중점
    shoulder_mid = midpoint(p(11), p(12))
    hip_mid      = midpoint(p(23), p(24))
    ankle_mid    = midpoint(p(27), p(28))

    # --- 1. 상체 전경각 ---
    spine_vec = np.array([
        shoulder_mid[0] - hip_mid[0],
        shoulder_mid[1] - hip_mid[1],
        shoulder_mid[2] - hip_mid[2],
    ])
    norm_s = float(np.linalg.norm(spine_vec))
    if norm_s < 1e-9:
        return None
    vertical = np.array([0.0, 1.0, 0.0])
    cos_v = float(np.dot(spine_vec / norm_s, vertical))
    cos_v = max(-1.0, min(1.0, cos_v))
    spine_tilt = float(np.degrees(np.arccos(cos_v)))
    if spine_vec[2] < 0:   # 앞숙임 = 양수
        spine_tilt = -spine_tilt

    # ΔX 체중이동: 골반 - 발목 (X축)
    delta_x = float(hip_mid[0] - ankle_mid[0])

    # --- 2. 팔꿈치 ---
    l_elbow_angle = angle_three_points(p(11), p(13), p(15))
    r_elbow_angle = angle_three_points(p(12), p(14), p(16))
    l_elbow_drop  = p(13).y - p(11).y   # 처짐 = 양수
    r_elbow_drop  = p(14).y - p(12).y

    # --- 3. 무릎 ---
    l_knee_angle = angle_three_points(p(23), p(25), p(27))
    r_knee_angle = angle_three_points(p(24), p(26), p(28))
    knee_dist    = distance_3d(p(25), p(26))

    # --- 4. 발목 ---
    l_ankle_angle = angle_three_points(p(25), p(27), p(31))
    r_ankle_angle = angle_three_points(p(26), p(28), p(32))
    l_heel_drop   = p(27).y - p(31).y   # 발뒤꿈치 내려감 = 양수
    r_heel_drop   = p(28).y - p(32).y

    # --- 5. 시선/두부 ---
    ear_mid_y    = (p(7).y + p(8).y) / 2.0
    head_tilt    = p(0).y - ear_mid_y   # 고개 숙임 = 양수
    shoulder_lv  = p(11).y - p(12).y

    return {
        "spine_tilt_angle":         (spine_tilt,    "degrees",    mean_visibility(fl, [11, 12, 23, 24])),
        "weight_transfer_delta_x":  (delta_x,       "normalized", mean_visibility(fl, [23, 24, 27, 28])),
        "left_elbow_angle":         (l_elbow_angle, "degrees",    mean_visibility(fl, [11, 13, 15])),
        "right_elbow_angle":        (r_elbow_angle, "degrees",    mean_visibility(fl, [12, 14, 16])),
        "left_elbow_drop":          (l_elbow_drop,  "normalized", mean_visibility(fl, [11, 13])),
        "right_elbow_drop":         (r_elbow_drop,  "normalized", mean_visibility(fl, [12, 14])),
        "left_knee_angle":          (l_knee_angle,  "degrees",    mean_visibility(fl, [23, 25, 27])),
        "right_knee_angle":         (r_knee_angle,  "degrees",    mean_visibility(fl, [24, 26, 28])),
        "knee_width_distance":      (knee_dist,     "normalized", mean_visibility(fl, [25, 26])),
        "left_ankle_angle":         (l_ankle_angle, "degrees",    mean_visibility(fl, [25, 27, 31])),
        "right_ankle_angle":        (r_ankle_angle, "degrees",    mean_visibility(fl, [26, 28, 32])),
        "left_heel_drop":           (l_heel_drop,   "normalized", mean_visibility(fl, [27, 31])),
        "right_heel_drop":          (r_heel_drop,   "normalized", mean_visibility(fl, [28, 32])),
        "head_tilt":                (head_tilt,     "normalized", mean_visibility(fl, [0, 7, 8])),
        "shoulder_level":           (shoulder_lv,   "normalized", mean_visibility(fl, [11, 12])),
    }


# ---------------------------------------------------------------------------
# 중앙값 집계
# ---------------------------------------------------------------------------

def _aggregate_to_representative(
    all_metrics: list[dict],
    valid_frames: list[FrameLandmarks],
) -> KeyPointAnalysis:
    def med(key: str) -> JointMeasurement:
        vals   = [m[key][0] for m in all_metrics]
        unit   = all_metrics[0][key][1]
        confs  = [m[key][2] for m in all_metrics]
        return JointMeasurement(
            value=float(np.median(vals)),
            unit=unit,
            confidence=float(np.mean(confs)),
        )

    return KeyPointAnalysis(
        spine_tilt_angle=med("spine_tilt_angle"),
        weight_transfer_delta_x=med("weight_transfer_delta_x"),
        left_elbow_angle=med("left_elbow_angle"),
        right_elbow_angle=med("right_elbow_angle"),
        left_elbow_drop=med("left_elbow_drop"),
        right_elbow_drop=med("right_elbow_drop"),
        left_knee_angle=med("left_knee_angle"),
        right_knee_angle=med("right_knee_angle"),
        knee_width_distance=med("knee_width_distance"),
        left_ankle_angle=med("left_ankle_angle"),
        right_ankle_angle=med("right_ankle_angle"),
        left_heel_drop=med("left_heel_drop"),
        right_heel_drop=med("right_heel_drop"),
        head_tilt=med("head_tilt"),
        shoulder_level=med("shoulder_level"),
    )


# ---------------------------------------------------------------------------
# 표준값 대비 델타
# ---------------------------------------------------------------------------

def _compute_deltas(
    kpa: KeyPointAnalysis,
    standards: StandardPoseData,
) -> dict[str, Delta]:
    pairs = [
        ("spine_tilt_angle",        kpa.spine_tilt_angle,        standards.spine_tilt_angle),
        ("weight_transfer_delta_x", kpa.weight_transfer_delta_x, standards.weight_transfer_delta_x),
        ("left_elbow_angle",        kpa.left_elbow_angle,        standards.left_elbow_angle),
        ("right_elbow_angle",       kpa.right_elbow_angle,       standards.right_elbow_angle),
        ("left_elbow_drop",         kpa.left_elbow_drop,         standards.left_elbow_drop),
        ("right_elbow_drop",        kpa.right_elbow_drop,        standards.right_elbow_drop),
        ("left_knee_angle",         kpa.left_knee_angle,         standards.left_knee_angle),
        ("right_knee_angle",        kpa.right_knee_angle,        standards.right_knee_angle),
        ("knee_width_distance",     kpa.knee_width_distance,     standards.knee_width_distance),
        ("left_ankle_angle",        kpa.left_ankle_angle,        standards.left_ankle_angle),
        ("right_ankle_angle",       kpa.right_ankle_angle,       standards.right_ankle_angle),
        ("left_heel_drop",          kpa.left_heel_drop,          standards.left_heel_drop),
        ("right_heel_drop",         kpa.right_heel_drop,         standards.right_heel_drop),
        ("head_tilt",               kpa.head_tilt,               standards.head_tilt),
        ("shoulder_level",          kpa.shoulder_level,          standards.shoulder_level),
    ]

    deltas: dict[str, Delta] = {}
    for name, measurement, stats in pairs:
        user_val = measurement.value
        err = user_val - stats.mean
        err_pct = (err / stats.std * 100.0) if stats.std > 1e-9 else 0.0
        deltas[name] = Delta(
            user_value=user_val,
            standard_mean=stats.mean,
            standard_std=stats.std,
            error_value=err,
            error_percent=err_pct,
            within_one_std=abs(err) <= stats.std,
        )

    return deltas
