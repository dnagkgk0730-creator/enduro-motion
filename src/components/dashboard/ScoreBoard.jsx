const SEV_COLOR = {
  good:     'text-green-400',
  warning:  'text-yellow-400',
  critical: 'text-red-400',
}
const SEV_BG = {
  good:     'bg-green-400/10 border-green-400/30',
  warning:  'bg-yellow-400/10 border-yellow-400/30',
  critical: 'bg-red-400/10 border-red-400/30',
}
const SEV_BAR = {
  good:     'bg-green-400',
  warning:  'bg-yellow-400',
  critical: 'bg-red-400',
}
const SEV_LABEL = { good: '정상', warning: '주의', critical: '교정 필요' }

export default function ScoreBoard({ payload }) {
  const { overall_score, joint_scores, valid_frame_ratio, sanity_failures, status } = payload

  const counts = { good: 0, warning: 0, critical: 0 }
  joint_scores.forEach(j => counts[j.severity]++)

  // 점수 원형 게이지 (SVG)
  const R = 52, C = 2 * Math.PI * R
  const dashOffset = C - (overall_score / 100) * C
  const scoreColor = overall_score >= 75 ? '#22c55e' : overall_score >= 50 ? '#eab308' : '#ef4444'

  return (
    <div className="space-y-5">
      {/* 종합 점수 */}
      <div className="bg-surface border border-border rounded-xl p-5 flex items-center gap-6">
        <div className="relative w-28 h-28 flex-shrink-0">
          <svg className="-rotate-90" width="112" height="112" viewBox="0 0 112 112">
            <circle cx="56" cy="56" r={R} fill="none" stroke="#1e2330" strokeWidth="10" />
            <circle cx="56" cy="56" r={R} fill="none"
              stroke={scoreColor} strokeWidth="10"
              strokeDasharray={C} strokeDashoffset={dashOffset}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 1s ease' }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-black" style={{ color: scoreColor }}>
              {Math.round(overall_score)}
            </span>
            <span className="text-xs text-gray-500 -mt-1">점수</span>
          </div>
        </div>

        <div className="flex-1">
          <h2 className="text-lg font-bold text-white mb-1">분석 완료</h2>
          <p className="text-sm text-gray-400">
            세계 정상권 표준 자세 대비 {joint_scores.length}개 지표 종합
          </p>
          <div className="flex gap-4 mt-3">
            {Object.entries(counts).map(([sev, n]) => (
              <div key={sev}>
                <div className={`text-xl font-black ${SEV_COLOR[sev]}`}>{n}</div>
                <div className="text-xs text-gray-500">{SEV_LABEL[sev]}</div>
              </div>
            ))}
          </div>
        </div>

        {/* 메타 */}
        <div className="text-right text-xs text-gray-500 space-y-1">
          <div>유효 프레임 <span className="text-white font-semibold">
            {(valid_frame_ratio * 100).toFixed(0)}%
          </span></div>
          {sanity_failures?.length > 0 && (
            <div className="text-yellow-500">
              이상치 클램핑 {sanity_failures.length}건
            </div>
          )}
          {status === 'partial' && (
            <div className="text-yellow-500">일부 프레임 품질 불량</div>
          )}
        </div>
      </div>

      {/* 지표별 게이지 */}
      <div className="bg-surface border border-border rounded-xl p-5">
        <div className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-4">
          포인트별 상세
        </div>
        <div className="space-y-3">
          {joint_scores.map((j) => {
            // 표준값을 기준으로 상대적 위치 계산
            const maxVal = Math.max(Math.abs(j.user_value), Math.abs(j.standard_mean)) * 1.3 || 1
            const userPct = Math.min(100, (Math.abs(j.user_value) / maxVal) * 100)
            const stdPct  = Math.min(100, (Math.abs(j.standard_mean) / maxVal) * 100)
            const deltaAbs = Math.abs(j.delta_value)

            return (
              <div key={j.metric_name}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium text-white">{j.display_name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">
                      {j.user_value.toFixed(2)}
                      {j.delta_value !== 0 && (
                        <span className={deltaAbs > 0.01 ? SEV_COLOR[j.severity] : 'text-gray-500'}>
                          {' '}({j.delta_value > 0 ? '+' : ''}{j.delta_value.toFixed(2)})
                        </span>
                      )}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full border font-semibold
                      ${SEV_BG[j.severity]} ${SEV_COLOR[j.severity]}`}>
                      {SEV_LABEL[j.severity]}
                    </span>
                  </div>
                </div>
                {/* 바 */}
                <div className="relative h-1.5 bg-surface2 rounded-full overflow-visible">
                  {/* 표준 범위 마커 */}
                  <div
                    className="absolute top-0 h-full bg-white/10 rounded-full"
                    style={{ left: `${Math.max(0, stdPct - 5)}%`, width: '10%' }}
                  />
                  {/* 사용자 값 바 */}
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${SEV_BAR[j.severity]}`}
                    style={{ width: `${userPct}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
