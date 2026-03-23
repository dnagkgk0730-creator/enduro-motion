import { Suspense } from 'react'
import useAnalysisStore from './store/useAnalysisStore'
import VideoUploader from './components/upload/VideoUploader'
import ScoreBoard from './components/dashboard/ScoreBoard'
import CorrectionHints from './components/dashboard/CorrectionHints'
import Scene from './components/threed/Scene'

function Header() {
  const { status, reset } = useAnalysisStore()
  const done = status === 'complete'

  return (
    <header className="h-14 border-b border-border bg-surface flex items-center px-6 gap-4 flex-shrink-0">
      <span className="text-xl">🏍️</span>
      <span className="font-black text-white tracking-tight">EnduroMotion</span>
      <span className="text-xs text-gray-500 font-medium">AI 라이딩 자세 분석</span>
      {done && (
        <button
          onClick={reset}
          className="ml-auto text-xs px-3 py-1.5 rounded-lg bg-surface2 border border-border
            text-gray-400 hover:text-white hover:border-accent/50 transition-colors"
        >
          새 분석
        </button>
      )}
    </header>
  )
}

function UploadPhase() {
  return (
    <div className="flex flex-1 items-center justify-center p-8">
      <div className="w-full max-w-xl space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-black text-white">라이딩 자세 분석</h1>
          <p className="text-gray-400 text-sm">
            세계 정상권 선수의 표준 자세와 비교해 실시간 교정 피드백을 받으세요
          </p>
        </div>
        <VideoUploader />
      </div>
    </div>
  )
}

function ResultPhase({ payload }) {
  return (
    <div className="flex flex-1 overflow-hidden">
      {/* 3D 뷰어 */}
      <div className="flex-1 min-w-0">
        <Suspense fallback={
          <div className="w-full h-full flex items-center justify-center bg-bg">
            <span className="text-gray-500 text-sm">3D 렌더링 로딩...</span>
          </div>
        }>
          <Scene />
        </Suspense>
      </div>

      {/* 사이드 패널 */}
      <div className="w-96 flex-shrink-0 border-l border-border overflow-y-auto bg-bg">
        <div className="p-5 space-y-5">
          <ScoreBoard payload={payload} />
          <CorrectionHints payload={payload} />
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const { status, payload } = useAnalysisStore()
  const isComplete = status === 'complete' && payload

  return (
    <div className="flex flex-col h-screen bg-bg text-white overflow-hidden">
      <Header />
      {isComplete
        ? <ResultPhase payload={payload} />
        : <UploadPhase />
      }
    </div>
  )
}
