const SEV_STYLES = {
  good:     { border: 'border-green-500/30',  bg: 'bg-green-500/5',   icon: '✅', label: '정상' },
  warning:  { border: 'border-yellow-500/30', bg: 'bg-yellow-500/5',  icon: '⚠️', label: '주의' },
  critical: { border: 'border-red-500/30',    bg: 'bg-red-500/5',     icon: '🔴', label: '교정 필요' },
}

const BODY_ICONS = {
  spine_tilt_angle:         '🏋️',
  weight_transfer_delta_x:  '⚖️',
  left_elbow_angle:         '💪',
  right_elbow_angle:        '💪',
  left_elbow_drop:          '⬆️',
  right_elbow_drop:         '⬆️',
  left_knee_angle:          '🦵',
  right_knee_angle:         '🦵',
  knee_width_distance:      '↔️',
  left_ankle_angle:         '🦶',
  right_ankle_angle:        '🦶',
  left_heel_drop:           '👟',
  right_heel_drop:          '👟',
  head_tilt:                '👁️',
  shoulder_level:           '↕️',
}

export default function CorrectionHints({ payload }) {
  const { joint_scores, correction_vectors } = payload

  // severity 순서로 정렬: critical → warning → good
  const sorted = [...joint_scores].sort((a, b) => {
    const order = { critical: 0, warning: 1, good: 2 }
    return order[a.severity] - order[b.severity]
  })

  // hint가 없는 항목은 교정 섹션에서 제외
  const needsCorrection = sorted.filter(j => j.correction_hint)
  const allGood         = sorted.filter(j => !j.correction_hint)

  return (
    <div className="space-y-4">
      <div className="text-xs font-semibold tracking-widest text-gray-500 uppercase">
        교정 피드백
      </div>

      {/* 교정 필요 항목 */}
      <div className="space-y-2">
        {needsCorrection.map((j) => {
          const s = SEV_STYLES[j.severity]
          // 해당 교정 벡터 찾기
          const vec = correction_vectors?.find(v =>
            v.joint_name === j.metric_name.replace(/_angle|_drop|_distance|_level|_tilt/, '').replace(/left_|right_/, '')
          )

          return (
            <div
              key={j.metric_name}
              className={`flex items-start gap-3 p-3 rounded-xl border ${s.border} ${s.bg}`}
            >
              <span className="text-xl flex-shrink-0 mt-0.5">
                {BODY_ICONS[j.metric_name] || s.icon}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold text-white">{j.display_name}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-bold
                    ${j.severity === 'critical' ? 'bg-red-500/20 text-red-400'
                      : j.severity === 'warning'  ? 'bg-yellow-500/20 text-yellow-400'
                      : 'bg-green-500/20 text-green-400'}`}>
                    {s.label}
                  </span>
                </div>
                <p className="text-sm text-gray-300">{j.correction_hint}</p>
                {vec && (
                  <p className="text-xs text-gray-500 mt-1">
                    → {vec.display_label}
                  </p>
                )}
              </div>
              {/* 델타 수치 */}
              <div className="text-right flex-shrink-0">
                <div className={`text-sm font-bold
                  ${j.severity === 'critical' ? 'text-red-400'
                    : j.severity === 'warning' ? 'text-yellow-400'
                    : 'text-green-400'}`}>
                  {j.delta_value > 0 ? '+' : ''}{j.delta_value.toFixed(2)}
                </div>
                <div className="text-xs text-gray-600">오차</div>
              </div>
            </div>
          )
        })}
      </div>

      {/* 정상 항목 (접이식) */}
      {allGood.length > 0 && (
        <details className="group">
          <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-300 transition-colors">
            ✓ 정상 항목 {allGood.length}개 보기
          </summary>
          <div className="mt-2 space-y-1">
            {allGood.map((j) => (
              <div
                key={j.metric_name}
                className="flex items-center gap-2 px-3 py-2 rounded-lg
                  bg-green-500/5 border border-green-500/20"
              >
                <span className="text-sm">{BODY_ICONS[j.metric_name] || '✅'}</span>
                <span className="text-sm text-gray-400">{j.display_name}</span>
                <span className="ml-auto text-xs text-green-400 font-semibold">정상</span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}
