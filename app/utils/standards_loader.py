from __future__ import annotations

import json
import os

from app.models.contracts import JointStats, StandardPoseData

# 싱글톤 — 프로세스당 1회만 디스크에서 읽음
_standards: StandardPoseData | None = None


def load_standards(path: str | None = None) -> StandardPoseData:
    """
    표준값 JSON을 로드한다.
    두 번째 호출부터는 메모리 캐시를 반환 (디스크 읽기 없음).
    """
    global _standards
    if _standards is not None:
        return _standards

    if path is None:
        path = os.environ.get("STANDARDS_PATH", "standards/enduro_standard.json")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    _standards = _parse(data)
    return _standards


def reset_standards() -> None:
    """테스트 전용 — 싱글톤 초기화."""
    global _standards
    _standards = None


def _parse(data: dict) -> StandardPoseData:
    def js(key: str) -> JointStats:
        d = data["angles"][key]
        return JointStats(
            mean=d["mean"],
            std=d["std"],
            min_valid=d["min_valid"],
            max_valid=d["max_valid"],
        )

    return StandardPoseData(
        version=data.get("version", "1.0.0"),
        sample_count=data.get("sample_count", 0),
        spine_tilt_angle=js("spine_tilt_angle"),
        weight_transfer_delta_x=js("weight_transfer_delta_x"),
        left_elbow_angle=js("left_elbow_angle"),
        right_elbow_angle=js("right_elbow_angle"),
        left_elbow_drop=js("left_elbow_drop"),
        right_elbow_drop=js("right_elbow_drop"),
        left_knee_angle=js("left_knee_angle"),
        right_knee_angle=js("right_knee_angle"),
        knee_width_distance=js("knee_width_distance"),
        left_ankle_angle=js("left_ankle_angle"),
        right_ankle_angle=js("right_ankle_angle"),
        left_heel_drop=js("left_heel_drop"),
        right_heel_drop=js("right_heel_drop"),
        head_tilt=js("head_tilt"),
        shoulder_level=js("shoulder_level"),
        ideal_skeleton_3d=data.get("ideal_skeleton_3d", []),
    )
