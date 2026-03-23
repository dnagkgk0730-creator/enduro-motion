from __future__ import annotations

import cv2
import mediapipe as mp
import numpy as np

from app.models.contracts import FrameLandmarks, LandmarkPoint

# MediaPipe landmark index → name 매핑 (사용하는 포인트만)
LANDMARK_NAMES: dict[int, str] = {
    0:  "NOSE",
    7:  "LEFT_EAR",
    8:  "RIGHT_EAR",
    11: "LEFT_SHOULDER",
    12: "RIGHT_SHOULDER",
    13: "LEFT_ELBOW",
    14: "RIGHT_ELBOW",
    15: "LEFT_WRIST",
    16: "RIGHT_WRIST",
    23: "LEFT_HIP",
    24: "RIGHT_HIP",
    25: "LEFT_KNEE",
    26: "RIGHT_KNEE",
    27: "LEFT_ANKLE",
    28: "RIGHT_ANKLE",
    31: "LEFT_FOOT_INDEX",
    32: "RIGHT_FOOT_INDEX",
}

# 분석에 필요한 랜드마크 인덱스 집합
REQUIRED_INDICES: set[int] = set(LANDMARK_NAMES.keys())


def extract_world_landmarks(
    frames_bgr: list[np.ndarray],
    model_complexity: int = 1,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
) -> list[FrameLandmarks | None]:
    """
    프레임 리스트에서 MediaPipe world_landmarks를 추출한다.

    중요:
    - 반드시 pose_world_landmarks 사용 (pose_landmarks 사용 금지)
    - world_landmarks: 골반 원점 기준 실제 미터(meter) 단위 3D 좌표
    - Context Manager로 MediaPipe 객체 자동 해제 (OOM 방지)
    - 영상 1개당 Context를 유지해 temporal tracking 활용
    """
    results: list[FrameLandmarks | None] = []

    with mp.solutions.pose.Pose(
        model_complexity=model_complexity,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
        smooth_landmarks=True,
    ) as pose:
        for i, frame_bgr in enumerate(frames_bgr):
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_result = pose.process(frame_rgb)

            # 반드시 pose_world_landmarks 사용
            if mp_result.pose_world_landmarks is None:
                results.append(None)
                continue

            landmarks = _parse_world_landmarks(mp_result.pose_world_landmarks, i)
            results.append(landmarks)

    return results


def _parse_world_landmarks(
    world_lms: any,
    frame_index: int,
) -> FrameLandmarks:
    points: list[LandmarkPoint] = []
    for idx, lm in enumerate(world_lms.landmark):
        points.append(LandmarkPoint(
            x=lm.x,
            y=lm.y,
            z=lm.z,
            visibility=lm.visibility,
        ))
    return FrameLandmarks(
        frame_index=frame_index,
        timestamp_ms=0.0,   # orchestrator에서 채움
        landmarks=points,
    )


def get_landmark(frame: FrameLandmarks, index: int) -> LandmarkPoint:
    return frame.landmarks[index]


def midpoint(a: LandmarkPoint, b: LandmarkPoint) -> tuple[float, float, float]:
    return ((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2)


def distance_3d(a: LandmarkPoint, b: LandmarkPoint) -> float:
    return float(np.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2))


def angle_three_points(
    a: LandmarkPoint,
    vertex: LandmarkPoint,
    b: LandmarkPoint,
) -> float:
    """
    vertex에서의 내각 (degrees, 0–180).
    arccos NaN 방지: dot product를 [-1, 1]로 클램핑.
    """
    va = np.array([a.x - vertex.x, a.y - vertex.y, a.z - vertex.z])
    vb = np.array([b.x - vertex.x, b.y - vertex.y, b.z - vertex.z])

    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)

    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0

    cos_val = float(np.dot(va, vb) / (norm_a * norm_b))
    cos_val = max(-1.0, min(1.0, cos_val))   # arccos NaN 방지
    return float(np.degrees(np.arccos(cos_val)))


def mean_visibility(frame: FrameLandmarks, indices: list[int]) -> float:
    vals = [frame.landmarks[i].visibility for i in indices if i < len(frame.landmarks)]
    return float(np.mean(vals)) if vals else 0.0
