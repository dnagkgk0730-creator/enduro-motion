/**
 * [방어 3] MediaPipe → Three.js 좌표계 변환 무결성
 *
 * MediaPipe world_landmarks 좌표계:
 *   - 원점: 골반 중앙
 *   - Y축: 위로 갈수록 음수 (화면 좌표계 관습)
 *   - 단위: 미터(meter) 근사
 *
 * Three.js 좌표계:
 *   - Y축: 위로 갈수록 양수 (수학적 좌표계)
 *   - 스케일: 시각적으로 적절한 크기 필요
 *
 * 변환 규칙:
 *   three_x = mp_x  * SCALE
 *   three_y = -mp_y * SCALE   ← Y축 반전 (핵심)
 *   three_z = -mp_z * SCALE   ← Z축 반전 (Three.js는 -Z가 화면 안쪽)
 */

const SCALE = 3.0   // 미터 단위 → Three.js 씬 단위 (3배 확대로 가시성 확보)

/**
 * 단일 랜드마크 변환
 * @param {{ x: number, y: number, z: number }} lm - MediaPipe 랜드마크
 * @returns {[number, number, number]} Three.js [x, y, z]
 */
export function mapLandmark(lm) {
  return [
    lm.x  *  SCALE,
    lm.y  * -SCALE,   // Y축 반전
    lm.z  * -SCALE,   // Z축 반전
  ]
}

/**
 * 스켈레톤 전체 변환
 * @param {Array<{index, name, x, y, z}>} skeleton
 * @returns {Array<{index, name, pos: [x,y,z]}>}
 */
export function mapSkeleton(skeleton) {
  return skeleton.map((lm) => ({
    index: lm.index,
    name:  lm.name,
    pos:   mapLandmark(lm),
  }))
}

/**
 * 교정 벡터 변환
 * direction은 단위 벡터이므로 Y·Z 부호만 반전 (스케일 없음)
 * magnitude는 시각적 길이를 위해 SCALE 적용
 *
 * @param {{ joint_name, direction: [dx,dy,dz], magnitude, display_label }} vec
 * @returns {{ joint_name, direction: [dx,dy,dz], magnitude, display_label }}
 */
export function mapCorrectionVector(vec) {
  const [dx, dy, dz] = vec.direction
  return {
    ...vec,
    direction: [dx, -dy, -dz],
    magnitude: vec.magnitude * SCALE,
  }
}

/**
 * MediaPipe bone connection 정의 (33포인트 중 사용 인덱스)
 * 각 쌍 [a, b]는 연결된 두 랜드마크 인덱스
 */
export const BONE_CONNECTIONS = [
  // 머리
  [0, 7], [0, 8],
  // 어깨
  [11, 12],
  // 왼팔
  [11, 13], [13, 15],
  // 오른팔
  [12, 14], [14, 16],
  // 몸통
  [11, 23], [12, 24], [23, 24],
  // 왼다리
  [23, 25], [25, 27], [27, 31],
  // 오른다리
  [24, 26], [26, 28], [28, 32],
]

/**
 * 인덱스로 매핑된 스켈레톤에서 빠른 조회용 맵 생성
 * @param {ReturnType<typeof mapSkeleton>} mappedSkeleton
 * @returns {Map<number, [x,y,z]>}
 */
export function buildPosMap(mappedSkeleton) {
  const map = new Map()
  mappedSkeleton.forEach(({ index, pos }) => map.set(index, pos))
  return map
}
