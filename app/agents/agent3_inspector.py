from __future__ import annotations

import logging
import math
import time

import numpy as np

from app.models.contracts import (
    AnalysisResult,
    CorrectionVector,
    Delta,
    FinalPayload,
    JointScore,
    Landmark3D,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sanity check 범위 (물리적으로 불가능한 값 클램핑)
# ---------------------------------------------------------------------------
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

# 표시 이름 (React 렌더링용)
DISPLAY_NAMES: dict[str, str] = {
    "spine_tilt_angle":         "상체 전경각",
    "weight_transfer_delta_x":  "체중이동 (ΔX)",
    "left_elbow_angle":         "왼쪽 팔꿈치 각도",
    "right_elbow_angle":        "오른쪽 팔꿈치 각도",
    "left_elbow_drop":          "왼쪽 팔꿈치 처짐",
    "right_elbow_drop":         "오른쪽 팔꿈치 처짐",
    "left_knee_angle":          "왼쪽 무릎 굽힘",
    "right_knee_angle":         "오른쪽 무릎 굽힘",
    "knee_width_distance":      "무릎 간격 (탱크 밀착)",
    "left_ankle_angle":         "왼쪽 발목 각도",
    "right_ankle_angle":        "오른쪽 발목 각도",
    "left_heel_drop":           "왼쪽 발뒤꿈치 하중",
    "right_heel_drop":          "오른쪽 발뒤꿈치 하중",
    "head_tilt":                "시선 (고개 숙임)",
    "shoulder_level":           "어깨 수평",
}

# 심각도 기준: z-score 절댓값
SEVERITY_THRESHOLDS = {
    "good":     1.0,   # |z| <= 1.0
    "warning":  2.0,   # 1.0 < |z| <= 2.0
    # |z| > 2.0 → "critical"
}


class InspectionAgent:
    """
    Agent 3: 결과 정합성 검수 + 3D 시각화 페이로드 생성 + JSON 패키징.

    책임:
    - 물리적으로 불가능한 값 클램핑 (reject 아님)
    - 3D 스켈레톤 + 교정 벡터 데이터 조립
    - React가 즉시 렌더링할 수 있는 FinalPayload 반환
    """

    def run(
        self,
        analysis: AnalysisResult,
        start_time_ns: float | None = None,
    ) -> FinalPayload:
        job_id = analysis.job_id
        logger.info(f"[{job_id}] Agent 3 start")

        # 1. Sanity check — 클램핑
        sanity_failures, clamped_deltas = _sanity_check(analysis.deltas)
        if sanity_failures:
            logger.warning(f"[{job_id}] Clamped {len(sanity_failures)} metrics: {sanity_failures}")

        # 2. JointScore 리스트 생성
        joint_scores = _build_joint_scores(clamped_deltas)

        # 3. 대표 프레임 선택 (가운데 프레임)
        rep_frame_idx = len(analysis.frame_landmarks) // 2
        rep_frame = analysis.frame_landmarks[rep_frame_idx]

        user_skeleton = [
            Landmark3D(
                index=i,
                name=_landmark_name(i),
                x=lm.x,
                y=lm.y,
                z=lm.z,
            )
            for i, lm in enumerate(rep_frame.landmarks)
        ]

        # 4. 이상적 스켈레톤
        ideal_skeleton = [
            Landmark3D(
                index=d["index"],
                name=d["name"],
                x=d["x"],
                y=d["y"],
                z=d["z"],
            )
            for d in analysis.standards.ideal_skeleton_3d
        ]

        # 5. 교정 벡터
        correction_vectors = _build_correction_vectors(clamped_deltas)

        # 6. 종합 점수 (0–100)
        overall_score = _compute_score(joint_scores)

        # 7. 처리 시간
        elapsed_ms = 0.0
        if start_time_ns is not None:
            elapsed_ms = (time.perf_counter_ns() - start_time_ns) / 1e6

        status = "partial" if sanity_failures else "success"
        valid_ratio = (
            analysis.valid_frame_count / analysis.total_frame_count
            if analysis.total_frame_count > 0
            else 0.0
        )

        logger.info(
            f"[{job_id}] Agent 3 complete — score={overall_score:.1f}, "
            f"status={status}, failures={sanity_failures}"
        )

        return FinalPayload(
            job_id=job_id,
            overall_score=overall_score,
            processing_time_ms=elapsed_ms,
            status=status,
            valid_frame_ratio=valid_ratio,
            sanity_failures=sanity_failures,
            joint_scores=joint_scores,
            user_skeleton=user_skeleton,
            ideal_skeleton=ideal_skeleton,
            correction_vectors=correction_vectors,
        )


# ---------------------------------------------------------------------------
# 내부 함수
# ---------------------------------------------------------------------------

def _sanity_check(
    deltas: dict[str, Delta],
) -> tuple[list[str], dict[str, Delta]]:
    """물리적으로 불가능한 user_value를 클램핑, 수정된 deltas 반환."""
    failures: list[str] = []
    clamped: dict[str, Delta] = {}

    for name, delta in deltas.items():
        bounds = SANITY_BOUNDS.get(name)
        if bounds is None:
            clamped[name] = delta
            continue

        lo, hi = bounds
        val = delta.user_value
        if val < lo or val > hi:
            clamped_val = max(lo, min(hi, val))
            failures.append(name)
            err = clamped_val - delta.standard_mean
            err_pct = (err / delta.standard_std * 100.0) if delta.standard_std > 1e-9 else 0.0
            clamped[name] = Delta(
                user_value=clamped_val,
                standard_mean=delta.standard_mean,
                standard_std=delta.standard_std,
                error_value=err,
                error_percent=err_pct,
                within_one_std=abs(err) <= delta.standard_std,
            )
        else:
            clamped[name] = delta

    return failures, clamped


def _severity(delta: Delta) -> str:
    z = abs(delta.error_percent) / 100.0  # z-score
    if z <= SEVERITY_THRESHOLDS["good"]:
        return "good"
    elif z <= SEVERITY_THRESHOLDS["warning"]:
        return "warning"
    return "critical"


def _correction_hint(name: str, delta: Delta) -> str:
    err = delta.error_value
    abs_err = abs(err)

    if abs_err < 1e-3:
        return ""

    hints = {
        "spine_tilt_angle": (
            f"상체를 {abs_err:.1f}° 더 앞으로 숙이세요" if err > 0
            else f"상체를 {abs_err:.1f}° 더 세우세요"
        ),
        "weight_transfer_delta_x": (
            f"체중을 {abs_err:.3f} 앞으로 이동하세요" if err > 0
            else f"체중을 {abs_err:.3f} 뒤로 이동하세요"
        ),
        "left_elbow_angle": (
            f"왼쪽 팔꿈치를 {abs_err:.1f}° 더 구부리세요" if err > 0
            else f"왼쪽 팔꿈치를 {abs_err:.1f}° 더 펴세요"
        ),
        "right_elbow_angle": (
            f"오른쪽 팔꿈치를 {abs_err:.1f}° 더 구부리세요" if err > 0
            else f"오른쪽 팔꿈치를 {abs_err:.1f}° 더 펴세요"
        ),
        "left_elbow_drop": (
            f"왼쪽 팔꿈치가 처졌습니다. {abs_err:.3f} 위로 올리세요" if err > 0
            else ""
        ),
        "right_elbow_drop": (
            f"오른쪽 팔꿈치가 처졌습니다. {abs_err:.3f} 위로 올리세요" if err > 0
            else ""
        ),
        "left_knee_angle": (
            f"왼쪽 무릎을 {abs_err:.1f}° 더 구부리세요" if err > 0
            else f"왼쪽 무릎을 {abs_err:.1f}° 더 펴세요"
        ),
        "right_knee_angle": (
            f"오른쪽 무릎을 {abs_err:.1f}° 더 구부리세요" if err > 0
            else f"오른쪽 무릎을 {abs_err:.1f}° 더 펴세요"
        ),
        "knee_width_distance": (
            f"무릎을 {abs_err:.3f} 더 벌려 탱크를 홀딩하세요" if err > 0
            else f"무릎을 {abs_err:.3f} 더 좁혀 탱크를 밀착하세요"
        ),
        "left_ankle_angle": (
            f"왼쪽 발목 각도를 {abs_err:.1f}° 조정하세요" if err > 0 else ""
        ),
        "right_ankle_angle": (
            f"오른쪽 발목 각도를 {abs_err:.1f}° 조정하세요" if err > 0 else ""
        ),
        "left_heel_drop": (
            f"왼쪽 발뒤꿈치를 더 내려 하중을 실으세요" if err < 0 else ""
        ),
        "right_heel_drop": (
            f"오른쪽 발뒤꿈치를 더 내려 하중을 실으세요" if err < 0 else ""
        ),
        "head_tilt": (
            f"고개가 숙여졌습니다. 전방 {abs_err:.3f} 더 멀리 바라보세요" if err > 0 else ""
        ),
        "shoulder_level": (
            f"어깨가 기울어졌습니다. 수평을 유지하세요" if abs_err > 0.05 else ""
        ),
    }
    return hints.get(name, "")


def _build_joint_scores(deltas: dict[str, Delta]) -> list[JointScore]:
    scores = []
    for name, delta in deltas.items():
        sev = _severity(delta)
        scores.append(JointScore(
            metric_name=name,
            display_name=DISPLAY_NAMES.get(name, name),
            user_value=delta.user_value,
            standard_mean=delta.standard_mean,
            delta_value=delta.error_value,
            passed=sev == "good",
            severity=sev,
            correction_hint=_correction_hint(name, delta),
        ))
    return scores


def _build_correction_vectors(deltas: dict[str, Delta]) -> list[CorrectionVector]:
    vectors = []

    # 상체 전경각 → 전후 방향 화살표
    if "spine_tilt_angle" in deltas:
        d = deltas["spine_tilt_angle"]
        if abs(d.error_value) > 2.0:
            # 앞숙임 필요: z축 방향
            sign = 1.0 if d.error_value > 0 else -1.0
            mag = min(abs(d.error_value) / 45.0, 1.0)  # 45°를 최대 magnitude 1.0으로 정규화
            vectors.append(CorrectionVector(
                joint_name="torso",
                direction=(0.0, 0.0, sign),
                magnitude=mag,
                display_label=f"{'앞으로' if sign > 0 else '뒤로'} {abs(d.error_value):.1f}°",
            ))

    # 체중이동 → 수평 화살표
    if "weight_transfer_delta_x" in deltas:
        d = deltas["weight_transfer_delta_x"]
        if abs(d.error_value) > 0.05:
            sign = 1.0 if d.error_value > 0 else -1.0
            mag = min(abs(d.error_value) * 2.0, 1.0)
            vectors.append(CorrectionVector(
                joint_name="hip",
                direction=(sign, 0.0, 0.0),
                magnitude=mag,
                display_label=f"체중 {'앞' if sign > 0 else '뒤'}으로 이동",
            ))

    # 팔꿈치 처짐 → 위 방향 화살표
    for side, key in [("left", "left_elbow_drop"), ("right", "right_elbow_drop")]:
        if key in deltas:
            d = deltas[key]
            if d.error_value > 0.05:
                vectors.append(CorrectionVector(
                    joint_name=f"{side}_elbow",
                    direction=(0.0, -1.0, 0.0),   # y축 위 방향
                    magnitude=min(d.error_value * 3.0, 1.0),
                    display_label=f"{'왼쪽' if side == 'left' else '오른쪽'} 팔꿈치 올리기",
                ))

    # 무릎 → 굽힘/펴기
    for side, key in [("left", "left_knee_angle"), ("right", "right_knee_angle")]:
        if key in deltas:
            d = deltas[key]
            if abs(d.error_value) > 5.0:
                mag = min(abs(d.error_value) / 90.0, 1.0)
                label = (
                    f"{'왼쪽' if side == 'left' else '오른쪽'} 무릎 "
                    f"{'펴기' if d.error_value < 0 else '구부리기'} {abs(d.error_value):.1f}°"
                )
                vectors.append(CorrectionVector(
                    joint_name=f"{side}_knee",
                    direction=(0.0, 1.0 if d.error_value < 0 else -1.0, 0.0),
                    magnitude=mag,
                    display_label=label,
                ))

    return vectors


def _compute_score(joint_scores: list[JointScore]) -> float:
    if not joint_scores:
        return 0.0
    # good=100, warning=60, critical=20 → 가중 평균
    sev_map = {"good": 100.0, "warning": 60.0, "critical": 20.0}
    vals = [sev_map[js.severity] for js in joint_scores]
    return float(np.mean(vals))


def _landmark_name(index: int) -> str:
    from app.utils.mediapipe_runner import LANDMARK_NAMES
    return LANDMARK_NAMES.get(index, f"LANDMARK_{index}")
