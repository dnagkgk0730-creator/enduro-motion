import { Canvas } from '@react-three/fiber'
import { OrbitControls, Grid } from '@react-three/drei'
import useAnalysisStore from '../../store/useAnalysisStore'
import SkeletonHelper from './SkeletonHelper'
import ArrowHelper from './ArrowHelper'

/**
 * R3F Canvas 진입점
 * 카메라, 조명, 그리드, 두 스켈레톤 + 교정 벡터 렌더링
 */
export default function Scene() {
  const payload = useAnalysisStore((s) => s.payload)

  return (
    <Canvas
      camera={{ position: [0, 1.2, 4.5], fov: 45 }}
      style={{ background: '#0a0d14' }}
    >
      {/* 조명 */}
      <ambientLight intensity={0.6} />
      <directionalLight position={[3, 5, 3]} intensity={1.2} />
      <directionalLight position={[-3, 2, -2]} intensity={0.4} />

      {/* 바닥 그리드 */}
      <Grid
        position={[0, -1.5, 0]}
        args={[10, 10]}
        cellSize={0.5}
        cellThickness={0.5}
        cellColor="#1e2330"
        sectionSize={2}
        sectionThickness={1}
        sectionColor="#2a3147"
        fadeDistance={8}
        fadeStrength={1}
        infiniteGrid
      />

      {/* 스켈레톤 */}
      {payload?.user_skeleton && (
        <SkeletonHelper
          skeleton={payload.user_skeleton}
          color="#f97316"   /* 사용자: 주황 */
          opacity={1}
        />
      )}
      {payload?.ideal_skeleton && (
        <SkeletonHelper
          skeleton={payload.ideal_skeleton}
          color="#3b82f6"   /* 이상적: 파랑, 반투명 */
          opacity={0.35}
        />
      )}

      {/* 교정 벡터 화살표 */}
      {payload?.correction_vectors?.length > 0 && payload?.user_skeleton && (
        <ArrowHelper
          correctionVectors={payload.correction_vectors}
          userSkeleton={payload.user_skeleton}
        />
      )}

      {/* 궤도 컨트롤 */}
      <OrbitControls
        enablePan={false}
        minDistance={2}
        maxDistance={10}
        target={[0, 0.3, 0]}
      />
    </Canvas>
  )
}
