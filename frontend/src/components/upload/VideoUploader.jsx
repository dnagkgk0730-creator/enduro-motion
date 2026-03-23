import { useRef, useState, useCallback } from 'react'
import useAnalysisStore from '../../store/useAnalysisStore'
import { uploadVideo, pollStatus } from '../../api/client'

// [방어 1] 클라이언트 단 1차 방어 상수
const MAX_SIZE_MB    = 50
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024
const MAX_DURATION_S = 15
const MIN_DURATION_S = 1
const ALLOWED_TYPES  = ['video/mp4', 'video/quicktime']   // mp4, mov

export default function VideoUploader() {
  const inputRef  = useRef(null)
  const abortRef  = useRef(null)   // 폴링 취소용
  const [dragOver, setDragOver] = useState(false)

  const { status, uploadProgress, error, setUploading, setQueued,
          setPollingStatus, setComplete, setError, reset } = useAnalysisStore()

  const busy = ['uploading', 'queued', 'processing'].includes(status)

  // ── 파일 유효성 검증 ─────────────────────────────────────
  function validateFile(file) {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `지원하지 않는 형식입니다 (${file.type}). MP4 또는 MOV만 가능합니다.`
    }
    if (file.size > MAX_SIZE_BYTES) {
      return `파일이 너무 큽니다 (${(file.size / 1024 / 1024).toFixed(1)}MB). 최대 ${MAX_SIZE_MB}MB.`
    }
    return null
  }

  // [방어 1] HTML5 Video 메타데이터로 영상 길이 확인 (백엔드 전송 전 차단)
  function validateDuration(file) {
    return new Promise((resolve) => {
      const url = URL.createObjectURL(file)
      const video = document.createElement('video')
      video.preload = 'metadata'
      video.onloadedmetadata = () => {
        URL.revokeObjectURL(url)
        const dur = video.duration
        if (dur < MIN_DURATION_S) {
          resolve(`영상이 너무 짧습니다 (${dur.toFixed(1)}초). 최소 ${MIN_DURATION_S}초.`)
        } else if (dur > MAX_DURATION_S) {
          resolve(`영상이 너무 깁니다 (${dur.toFixed(1)}초). 최대 ${MAX_DURATION_S}초.`)
        } else {
          resolve(null)
        }
      }
      video.onerror = () => { URL.revokeObjectURL(url); resolve(null) }
      video.src = url
    })
  }

  // ── 업로드 + 폴링 시작 ────────────────────────────────────
  const handleFile = useCallback(async (file) => {
    reset()

    // 1차 검증 (즉시)
    const typeErr = validateFile(file)
    if (typeErr) { setError(typeErr); return }

    // 2차 검증 (비동기 — 영상 길이)
    const durErr = await validateDuration(file)
    if (durErr) { setError(durErr); return }

    try {
      // 업로드
      setUploading(0)
      const { job_id } = await uploadVideo(file, (pct) => setUploading(pct))
      setQueued(job_id)

      // 폴링 시작 (지수 백오프)
      const controller = new AbortController()
      abortRef.current = controller
      pollStatus(job_id, {
        signal:     controller.signal,
        onStatus:   (s) => setPollingStatus(s),
        onComplete: (payload) => setComplete(payload),
        onError:    (err) => setError(err.message),
      })
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }, [reset, setUploading, setQueued, setPollingStatus, setComplete, setError])

  // ── 드래그 앤 드롭 ────────────────────────────────────────
  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  const onCancel = () => {
    abortRef.current?.abort()
    reset()
  }

  // ── 상태별 UI ────────────────────────────────────────────
  const statusLabel = {
    idle:       null,
    uploading:  `업로드 중... ${uploadProgress}%`,
    queued:     '분석 대기 중...',
    processing: '분석 중 (MediaPipe 처리)...',
  }[status]

  const progressColor = {
    uploading:  'bg-accent2',
    queued:     'bg-yellow-500',
    processing: 'bg-accent',
  }[status] || 'bg-accent2'

  if (status === 'complete') return null

  return (
    <div className="w-full max-w-xl mx-auto">
      {/* 드롭 존 */}
      {!busy && (
        <div
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
            transition-colors
            ${dragOver
              ? 'border-accent bg-accent/5'
              : 'border-border bg-surface2 hover:border-accent/60'}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
        >
          <div className="text-5xl mb-4">🏍️</div>
          <h3 className="text-lg font-bold text-white mb-2">영상을 드래그하거나 클릭하여 업로드</h3>
          <p className="text-sm text-gray-400">
            MP4 / MOV · 최대 {MAX_SIZE_MB}MB · {MIN_DURATION_S}–{MAX_DURATION_S}초
          </p>
          <input
            ref={inputRef}
            type="file"
            accept=".mp4,.mov,video/mp4,video/quicktime"
            className="hidden"
            onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
          />
        </div>
      )}

      {/* 진행 상태 */}
      {busy && (
        <div className="bg-surface border border-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-white">{statusLabel}</span>
            <button
              onClick={onCancel}
              className="text-xs text-gray-500 hover:text-red-400 transition-colors"
            >
              취소
            </button>
          </div>
          {/* 진행 바 */}
          <div className="h-2 bg-surface2 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${progressColor}
                ${status === 'processing' ? 'animate-pulse' : ''}`}
              style={{ width: status === 'uploading' ? `${uploadProgress}%` : '100%' }}
            />
          </div>
          {/* 단계 표시 */}
          <div className="flex gap-6 mt-4 text-xs text-gray-500">
            {['uploading', 'queued', 'processing'].map((s, i) => (
              <div key={s} className="flex items-center gap-1">
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold
                  ${status === s
                    ? 'bg-accent text-white'
                    : ['uploading','queued','processing'].indexOf(status) > i
                      ? 'bg-green-600 text-white'
                      : 'bg-surface2 text-gray-600'}`}>
                  {['uploading','queued','processing'].indexOf(status) > i ? '✓' : i + 1}
                </span>
                <span className={status === s ? 'text-white' : ''}>
                  {['업로드', '대기', 'AI 분석'][i]}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 에러 */}
      {status === 'failed' && error && (
        <div className="mt-4 p-4 bg-red-900/30 border border-red-700/50 rounded-xl">
          <p className="text-sm text-red-400 font-semibold mb-1">오류 발생</p>
          <p className="text-xs text-red-300">{error}</p>
          <button
            onClick={reset}
            className="mt-3 text-xs text-red-400 underline hover:text-red-300"
          >
            다시 시도
          </button>
        </div>
      )}
    </div>
  )
}
