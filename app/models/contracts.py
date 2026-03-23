from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Standards (loaded once at startup, shared across all agents)
# ---------------------------------------------------------------------------

@dataclass
class JointStats:
    mean: float
    std: float
    min_valid: float   # sanity check lower bound
    max_valid: float   # sanity check upper bound


@dataclass
class StandardPoseData:
    version: str
    sample_count: int
    # 1. 상체 전경각 및 무게중심
    spine_tilt_angle: JointStats
    weight_transfer_delta_x: JointStats
    # 2. 팔꿈치 포지셔닝
    left_elbow_angle: JointStats
    right_elbow_angle: JointStats
    left_elbow_drop: JointStats
    right_elbow_drop: JointStats
    # 3. 무릎 굽힘 및 차체 밀착
    left_knee_angle: JointStats
    right_knee_angle: JointStats
    knee_width_distance: JointStats
    # 4. 풋페그 하중 및 발목
    left_ankle_angle: JointStats
    right_ankle_angle: JointStats
    left_heel_drop: JointStats
    right_heel_drop: JointStats
    # 5. 시선 및 두부
    head_tilt: JointStats
    shoulder_level: JointStats
    # 이상적 스켈레톤 (33포인트, world_landmarks 기준)
    ideal_skeleton_3d: list[dict]  # [{index, name, x, y, z}, ...]


# ---------------------------------------------------------------------------
# Agent 1 Output → Agent 2 Input
# ---------------------------------------------------------------------------

@dataclass
class VideoMetadata:
    filename: str
    format: str                            # "mp4" | "mov"
    duration_seconds: float
    fps: float
    frame_count: int
    original_resolution: tuple[int, int]   # (width, height)
    processed_resolution: tuple[int, int]  # resized for MediaPipe


@dataclass
class PreprocessedData:
    job_id: str
    video_meta: VideoMetadata
    frames: list                           # list[np.ndarray], BGR
    frame_timestamps_ms: list[float]
    standards: StandardPoseData


# ---------------------------------------------------------------------------
# Agent 2 Output → Agent 3 Input
# ---------------------------------------------------------------------------

@dataclass
class LandmarkPoint:
    x: float
    y: float
    z: float
    visibility: float


@dataclass
class FrameLandmarks:
    frame_index: int
    timestamp_ms: float
    landmarks: list[LandmarkPoint]   # 33 points, MediaPipe world_landmarks


@dataclass
class JointMeasurement:
    value: float          # computed angle or offset
    unit: str             # "degrees" | "normalized"
    confidence: float     # mean visibility of contributing landmarks (0–1)


@dataclass
class KeyPointAnalysis:
    # 1. 상체 전경각 및 무게중심
    spine_tilt_angle: JointMeasurement
    weight_transfer_delta_x: JointMeasurement   # ΔX = X_hip_mid - X_ankle_mid

    # 2. 팔꿈치 포지셔닝
    left_elbow_angle: JointMeasurement
    right_elbow_angle: JointMeasurement
    left_elbow_drop: JointMeasurement    # elbow_y - shoulder_y  (양수=처짐)
    right_elbow_drop: JointMeasurement

    # 3. 무릎 굽힘 및 차체 밀착
    left_knee_angle: JointMeasurement
    right_knee_angle: JointMeasurement
    knee_width_distance: JointMeasurement   # 좌우 무릎 간 3D 거리

    # 4. 풋페그 하중 및 발목
    left_ankle_angle: JointMeasurement
    right_ankle_angle: JointMeasurement
    left_heel_drop: JointMeasurement    # ankle_y - foot_index_y  (양수=발뒤꿈치 내려감)
    right_heel_drop: JointMeasurement

    # 5. 시선 및 두부
    head_tilt: JointMeasurement          # nose_y - ear_mid_y  (양수=고개 숙임)
    shoulder_level: JointMeasurement     # left_shoulder_y - right_shoulder_y


@dataclass
class Delta:
    user_value: float
    standard_mean: float
    standard_std: float
    error_value: float      # user_value - standard_mean
    error_percent: float    # z-score × 100
    within_one_std: bool


@dataclass
class AnalysisResult:
    job_id: str
    frame_landmarks: list[FrameLandmarks]    # 전체 유효 프레임
    key_point_analysis: KeyPointAnalysis
    deltas: dict[str, Delta]                 # keyed by metric name
    standards: StandardPoseData
    valid_frame_count: int
    total_frame_count: int


# ---------------------------------------------------------------------------
# Agent 3 Output → FastAPI Response
# ---------------------------------------------------------------------------

@dataclass
class Landmark3D:
    index: int
    name: str
    x: float
    y: float
    z: float


@dataclass
class JointScore:
    metric_name: str
    display_name: str
    user_value: float
    standard_mean: float
    delta_value: float
    passed: bool
    severity: str        # "good" | "warning" | "critical"
    correction_hint: str


@dataclass
class CorrectionVector:
    joint_name: str
    direction: tuple[float, float, float]   # 3D unit vector (dx, dy, dz)
    magnitude: float
    display_label: str


@dataclass
class FinalPayload:
    job_id: str
    overall_score: float         # 0–100
    processing_time_ms: float
    status: str                  # "success" | "partial"
    valid_frame_ratio: float
    sanity_failures: list[str]   # metric names that were clamped
    joint_scores: list[JointScore]
    user_skeleton: list[Landmark3D]    # representative frame, user pose
    ideal_skeleton: list[Landmark3D]   # from standards.ideal_skeleton_3d
    correction_vectors: list[CorrectionVector]
