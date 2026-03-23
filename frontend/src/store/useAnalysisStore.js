import { create } from 'zustand'

/**
 * 전역 분석 상태 (Zustand)
 *
 * status 라이프사이클:
 *   idle → uploading → queued → processing → complete
 *                                           ↘ failed
 */
const useAnalysisStore = create((set) => ({
  // ── 상태 ──────────────────────────────────────────────
  status: 'idle',        // idle | uploading | queued | processing | complete | failed
  jobId: null,
  uploadProgress: 0,     // 0–100
  payload: null,         // FinalPayload (분석 완료 시)
  error: null,

  // ── 액션 ──────────────────────────────────────────────
  setUploading: (progress) => set({ status: 'uploading', uploadProgress: progress, error: null }),

  setQueued: (jobId) => set({ status: 'queued', jobId, uploadProgress: 100 }),

  setPollingStatus: (serverStatus) => set({ status: serverStatus }),

  setComplete: (payload) => set({ status: 'complete', payload }),

  setError: (message) => set({ status: 'failed', error: message }),

  reset: () => set({
    status: 'idle',
    jobId: null,
    uploadProgress: 0,
    payload: null,
    error: null,
  }),
}))

export default useAnalysisStore
