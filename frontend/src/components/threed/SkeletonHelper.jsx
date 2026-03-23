import { useMemo } from 'react'
import * as THREE from 'three'
import { mapSkeleton, buildPosMap, BONE_CONNECTIONS } from '../../utils/coordinate_mapper'

/**
 * 단일 뼈대 라인 (두 관절 연결)
 */
function Bone({ start, end, color, opacity = 1 }) {
  const geometry = useMemo(() => {
    const points = [new THREE.Vector3(...start), new THREE.Vector3(...end)]
    return new THREE.BufferGeometry().setFromPoints(points)
  }, [start, end])

  return (
    <line geometry={geometry}>
      <lineBasicMaterial color={color} transparent opacity={opacity} linewidth={2} />
    </line>
  )
}

/**
 * 관절 구체
 */
function Joint({ position, color, opacity = 1, size = 0.04 }) {
  return (
    <mesh position={position}>
      <sphereGeometry args={[size, 8, 8]} />
      <meshStandardMaterial color={color} transparent opacity={opacity} />
    </mesh>
  )
}

/**
 * 전체 스켈레톤 렌더링
 * @param {Array} skeleton - API의 user_skeleton 또는 ideal_skeleton
 * @param {string} color   - 뼈대 색상
 * @param {number} opacity - 투명도 (이상적 자세는 낮게)
 */
export default function SkeletonHelper({ skeleton, color, opacity = 1 }) {
  const mapped  = useMemo(() => mapSkeleton(skeleton), [skeleton])
  const posMap  = useMemo(() => buildPosMap(mapped), [mapped])

  return (
    <group>
      {/* 뼈대 (bone connections) */}
      {BONE_CONNECTIONS.map(([a, b]) => {
        const pa = posMap.get(a)
        const pb = posMap.get(b)
        if (!pa || !pb) return null
        return (
          <Bone
            key={`bone-${a}-${b}`}
            start={pa}
            end={pb}
            color={color}
            opacity={opacity}
          />
        )
      })}

      {/* 관절 점 */}
      {mapped.map(({ index, pos }) => (
        <Joint
          key={`joint-${index}`}
          position={pos}
          color={color}
          opacity={opacity}
          size={0.05}
        />
      ))}
    </group>
  )
}
