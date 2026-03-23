import axios from 'axios'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE })

// ── 영상 업로드 ──────────────────────────────────────────────
export async function uploadVideo(file, onProgress) {
  const form = new FormData()
  form.append('video', file)

  const { data } = await api.post('/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total) onProgress?.(Math.round((e.loaded / e.total) * 100))
    },
  })
  return data   // { job_id, status }
}

// ── 결과 수신 ────────────────────────────────────────────────
export async function fetchResult(jobId) {
  const { data } = await api.get(`/result/${jobId}`)
  return data
}

// ── 스마트 폴링 (지수 백오프) ────────────────────────────────
// [방어 2] 1초 → 2초 → 4초 → 최대 16초로 점진적 간격 증가
// 백엔드 Redis/API 부하를 방어한다.
export function pollStatus(jobId, { onStatus, onComplete, onError, signal }) {
  let attempt = 0
  const BASE_INTERVAL = 1000    // 1초
  const MAX_INTERVAL  = 16000   // 최대 16초
  let timeoutId = null

  async function tick() {
    if (signal?.aborted) return

    try {
      const { data } = await api.get(`/status/${jobId}`)
      const { status } = data

      onStatus?.(status)

      if (status === 'complete') {
        const result = await fetchResult(jobId)
        onComplete?.(result)
        return
      }

      if (status === 'failed') {
        onError?.(new Error('분석 서버에서 오류가 발생했습니다'))
        return
      }

      // 지수 백오프: 2^attempt × BASE_INTERVAL, 최대 MAX_INTERVAL
      const delay = Math.min(BASE_INTERVAL * Math.pow(2, attempt), MAX_INTERVAL)
      attempt++
      timeoutId = setTimeout(tick, delay)
    } catch (err) {
      if (signal?.aborted) return
      onError?.(err)
    }
  }

  tick()

  // 정리 함수 반환 (컴포넌트 언마운트 시 호출)
  return () => {
    if (timeoutId) clearTimeout(timeoutId)
  }
}
