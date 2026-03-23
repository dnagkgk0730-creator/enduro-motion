import { useMemo } from 'react'
import * as THREE from 'three'
import { mapSkeleton, mapCorrectionVector, buildPosMap } from '../../utils/coordinate_mapper'

// 교정 방향별 화살표 색상
const VECTOR_COLORS = {
  torso:       '#f97316',   // 주황 (상체)
  hip:         '#eab308',   // 노란 (체중이동)
  left_elbow:  '#a78bfa',   // 보라 (팔꿈치)
  right_elbow: '#a78bfa',
  left_knee:   '#3b82f6',   // 파랑 (무릎)
  right_knee:  '#3b82f6',
}

/**
 * 화살표 헬퍼
 * Three.js ArrowHelper를 React 선언형으로 래핑
 */
function Arrow({ origin, direction, length, color }) {
  const arrow = useMemo(() => {
    const dir = new THREE.Vector3(...direction).normalize()
    const ori = new THREE.Vector3(...origin)
    return new THREE.ArrowHelper(dir, ori, length, color, length * 0.3, length * 0.15)
  }, [origin, direction, length, color])

  return <primitive object={arrow} />
}

/**
 * 모든 교정 벡터를 사용자 스켈레톤 위에 렌더링
 *
 * @param {Array} correctionVectors - API의 correction_vectors
 * @param {Array} userSkeleton      - API의 user_skeleton (화살표 시작점 결정용)
 */
export default function ArrowHelper({ correctionVectors, userSkeleton }) {
  const mappedSkeleton = useMemo(() => mapSkeleton(userSkeleton), [userSkeleton])
  const posMap = useMemo(() => buildPosMap(mappedSkeleton), [mappedSkeleton])

  // 관절 이름 → 랜드마크 인덱스 매핑
  const JOINT_TO_INDEX = {
    torso:       23,   // left_hip (골반 중앙 근처)
    hip:         23,
    left_elbow:  13,
    right_elbow: 14,
    left_knee:   25,
    right_knee:  26,
    head:        0,
  }

  return (
    <group>
      {correctionVectors.map((vec, i) => {
        const mapped = mapCorrectionVector(vec)
        const idx = JOINT_TO_INDEX[vec.joint_name]
        const origin = posMap.get(idx) || [0, 0, 0]
        const color = VECTOR_COLORS[vec.joint_name] || '#ffffff'

        return (
          <Arrow
            key={`arrow-${i}-${vec.joint_name}`}
            origin={origin}
            direction={mapped.direction}
            length={Math.max(0.3, mapped.magnitude)}
            color={color}
          />
        )
      })}
    </group>
  )
}
