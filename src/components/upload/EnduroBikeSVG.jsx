/**
 * KTM EXC 스타일 엔듀로 바이크 SVG 일러스트
 * 오렌지/블루 컬러, 스포크 휠, 골드 포크, 머플러 등 실제 바이크 구조 반영
 */
export default function EnduroBikeSVG({ width = 300, height = 188 }) {
  // 스포크 좌표 계산
  const spokeLines = (cx, cy, rHub, rRim, n = 18) =>
    Array.from({ length: n }, (_, i) => {
      const a = (i / n) * 2 * Math.PI
      return [
        cx + rHub * Math.cos(a), cy + rHub * Math.sin(a),
        cx + rRim * Math.cos(a), cy + rRim * Math.sin(a),
      ]
    })

  // 타이어 노브 위치 계산
  const knobs = (cx, cy, r, n = 22) =>
    Array.from({ length: n }, (_, i) => {
      const a = (i / n) * 2 * Math.PI
      return { px: cx + r * Math.cos(a), py: cy + r * Math.sin(a), deg: (a * 180) / Math.PI }
    })

  const rearSpokes  = spokeLines(68, 148, 6, 28, 18)
  const frontSpokes = spokeLines(220, 148, 6, 28, 18)
  const rearKnobs   = knobs(68, 148, 38, 22)
  const frontKnobs  = knobs(220, 148, 38, 22)

  return (
    <svg width={width} height={height} viewBox="0 0 290 188" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="eb_orange" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#ff8000" />
          <stop offset="100%" stopColor="#cc3d00" />
        </linearGradient>
        <linearGradient id="eb_fork_upper" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#2a2a2a" />
          <stop offset="40%" stopColor="#555" />
          <stop offset="100%" stopColor="#1a1a1a" />
        </linearGradient>
        <linearGradient id="eb_fork_lower" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#a06000" />
          <stop offset="40%" stopColor="#d48000" />
          <stop offset="100%" stopColor="#8a5200" />
        </linearGradient>
        <linearGradient id="eb_exhaust" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#888" />
          <stop offset="50%" stopColor="#ddd" />
          <stop offset="100%" stopColor="#aaa" />
        </linearGradient>
        <linearGradient id="eb_frame" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#888" />
          <stop offset="100%" stopColor="#555" />
        </linearGradient>
        <radialGradient id="eb_hub" cx="35%" cy="35%" r="65%">
          <stop offset="0%" stopColor="#d0d0d0" />
          <stop offset="100%" stopColor="#808080" />
        </radialGradient>
      </defs>

      {/* ── 지면 그림자 ── */}
      <ellipse cx="144" cy="178" rx="115" ry="6" fill="black" opacity="0.18" />

      {/* ══════════════════ 뒷바퀴 ══════════════════ */}
      {/* 타이어 */}
      <circle cx="68" cy="148" r="41" fill="#0e0e0e" />
      <circle cx="68" cy="148" r="38" fill="none" stroke="#181818" strokeWidth="6" />
      {/* 노브 (트레드) */}
      {rearKnobs.map(({ px, py, deg }, i) => (
        <rect key={i}
          x={px - 3} y={py - 4} width={6} height={7} rx={1.2}
          fill="#1a1a1a" stroke="#2e2e2e" strokeWidth="0.5"
          transform={`rotate(${deg} ${px} ${py})`}
        />
      ))}
      {/* 림 */}
      <circle cx="68" cy="148" r="30" fill="none" stroke="#aaa" strokeWidth="2.5" />
      <circle cx="68" cy="148" r="27.5" fill="none" stroke="#888" strokeWidth="0.8" />
      {/* 브레이크 디스크 */}
      <circle cx="68" cy="148" r="19" fill="none" stroke="#666" strokeWidth="3" strokeDasharray="7 4" />
      <circle cx="68" cy="148" r="16" fill="none" stroke="#555" strokeWidth="1" />
      {/* 스포크 */}
      {rearSpokes.map(([x1, y1, x2, y2], i) => (
        <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#999" strokeWidth="0.9" />
      ))}
      {/* 허브 */}
      <circle cx="68" cy="148" r="8" fill="url(#eb_hub)" stroke="#aaa" strokeWidth="1" />
      <circle cx="68" cy="148" r="4.5" fill="#555" />
      <circle cx="68" cy="148" r="2" fill="#aaa" />

      {/* ══════════════════ 앞바퀴 ══════════════════ */}
      <circle cx="220" cy="148" r="41" fill="#0e0e0e" />
      <circle cx="220" cy="148" r="38" fill="none" stroke="#181818" strokeWidth="6" />
      {frontKnobs.map(({ px, py, deg }, i) => (
        <rect key={i}
          x={px - 3} y={py - 4} width={6} height={7} rx={1.2}
          fill="#1a1a1a" stroke="#2e2e2e" strokeWidth="0.5"
          transform={`rotate(${deg} ${px} ${py})`}
        />
      ))}
      <circle cx="220" cy="148" r="30" fill="none" stroke="#aaa" strokeWidth="2.5" />
      <circle cx="220" cy="148" r="27.5" fill="none" stroke="#888" strokeWidth="0.8" />
      <circle cx="220" cy="148" r="19" fill="none" stroke="#666" strokeWidth="3" strokeDasharray="7 4" />
      <circle cx="220" cy="148" r="16" fill="none" stroke="#555" strokeWidth="1" />
      {frontSpokes.map(([x1, y1, x2, y2], i) => (
        <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#999" strokeWidth="0.9" />
      ))}
      <circle cx="220" cy="148" r="8" fill="url(#eb_hub)" stroke="#aaa" strokeWidth="1" />
      <circle cx="220" cy="148" r="4.5" fill="#555" />
      <circle cx="220" cy="148" r="2" fill="#aaa" />

      {/* ══════════════════ 스윙암 ══════════════════ */}
      <path d="M68,148 L72,142 L120,112 L118,118 Z" fill="#444" />
      <path d="M70,145 L119,114" stroke="url(#eb_frame)" strokeWidth="4.5" strokeLinecap="round" />
      <path d="M72,142 L121,111" stroke="#666" strokeWidth="2" strokeLinecap="round" />

      {/* ══════════════════ 배기 시스템 ══════════════════ */}
      {/* 헤더 파이프 */}
      <path d="M138,128 Q122,150 102,158 Q86,163 74,160 Q68,158 68,153"
        stroke="#999" strokeWidth="5.5" fill="none" strokeLinecap="round" />
      <path d="M138,128 Q122,150 102,158 Q86,163 74,160 Q68,158 68,153"
        stroke="#ccc" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeDasharray="2 4" opacity="0.5" />
      {/* 메인 파이프 → 머플러 */}
      <path d="M138,128 Q148,152 172,160 Q194,165 215,160 Q228,156 232,149"
        stroke="url(#eb_exhaust)" strokeWidth="7" fill="none" strokeLinecap="round" />
      {/* 머플러 본체 */}
      <rect x="218" y="142" width="44" height="16" rx="7" fill="url(#eb_exhaust)" stroke="#888" strokeWidth="1.2" />
      {/* 머플러 엔드캡 */}
      <circle cx="262" cy="150" r="6.5" fill="#aaa" stroke="#777" strokeWidth="1" />
      <circle cx="262" cy="150" r="4" fill="#666" />
      <circle cx="262" cy="150" r="1.5" fill="#888" />
      {/* 히트 실드 */}
      <rect x="220" y="143" width="28" height="6" rx="3" fill="#e0e0e0" opacity="0.55" />
      <rect x="220" y="149" width="28" height="3" rx="1.5" fill="#e0e0e0" opacity="0.3" />

      {/* ══════════════════ 메인 프레임 ══════════════════ */}
      {/* 백본 (상부 프레임) */}
      <path d="M194,68 L158,68 L130,82 L78,93"
        stroke="url(#eb_frame)" strokeWidth="5.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      {/* 다운튜브 */}
      <path d="M194,74 L148,133"
        stroke="url(#eb_frame)" strokeWidth="5" fill="none" strokeLinecap="round" />
      {/* 시트 레일 */}
      <path d="M78,93 L66,118 L68,148"
        stroke="#555" strokeWidth="3.5" fill="none" strokeLinecap="round" />
      {/* 엔진 하부 마운트 */}
      <path d="M148,133 L120,133 L119,114"
        stroke="#555" strokeWidth="3.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      {/* 서브프레임 */}
      <path d="M78,93 L120,84 L130,82"
        stroke="#555" strokeWidth="2.5" fill="none" strokeLinecap="round" />

      {/* ══════════════════ 엔진 ══════════════════ */}
      {/* 엔진 케이스 */}
      <path d="M120,114 L154,112 L156,133 L120,133 Z" fill="#222" stroke="#3a3a3a" strokeWidth="1" />
      {/* 실린더 헤드 */}
      <rect x="138" y="95" width="18" height="20" rx="2" fill="#2a2a2a" stroke="#444" strokeWidth="1" />
      {/* 냉각 핀 */}
      {[98, 101, 104, 108, 111].map(y => (
        <line key={y} x1="139" y1={y} x2="155" y2={y} stroke="#444" strokeWidth="1" />
      ))}
      {/* 흡기 */}
      <path d="M138,100 Q128,95 122,98 Q118,101 120,106"
        stroke="#333" strokeWidth="4" fill="none" strokeLinecap="round" />
      {/* 클러치 커버 */}
      <ellipse cx="128" cy="124" rx="9" ry="11" fill="#282828" stroke="#444" strokeWidth="1" />
      <ellipse cx="128" cy="124" rx="5" ry="7" fill="#222" stroke="#3a3a3a" strokeWidth="0.8" />
      {/* 스프라켓 커버 */}
      <ellipse cx="100" cy="138" rx="11" ry="9" fill="#2e2e2e" stroke="#444" strokeWidth="1" />
      <circle cx="100" cy="138" r="4" fill="#1a1a1a" stroke="#444" strokeWidth="0.8" />

      {/* ══════════════════ 바디 패널 ══════════════════ */}
      {/* 연료탱크 */}
      <path d="M130,82 L160,68 L194,66 L198,80 L170,93 L138,93 Z"
        fill="url(#eb_orange)" stroke="#a03000" strokeWidth="1" />
      {/* 탱크 블루 그래픽 */}
      <path d="M148,72 L182,69 L186,79 L152,82 Z" fill="#1a3580" opacity="0.88" />
      {/* 탱크 화이트 스트라이프 */}
      <path d="M150,71 L183,68" stroke="white" strokeWidth="1.5" opacity="0.7" strokeLinecap="round" />
      <path d="M153,81 L184,78" stroke="white" strokeWidth="1" opacity="0.4" strokeLinecap="round" />
      {/* 탱크 하이라이트 */}
      <path d="M135,83 L162,70 L165,73 L140,86 Z" fill="white" opacity="0.08" />

      {/* 사이드 패널 */}
      <path d="M105,95 L138,91 L156,110 L148,133 L100,130 L92,112 Z"
        fill="url(#eb_orange)" stroke="#a03000" strokeWidth="1" />
      {/* 사이드 패널 블루 그래픽 */}
      <path d="M110,98 L136,93 L146,110 L118,112 Z" fill="#1a3580" opacity="0.75" />
      {/* 사이드 화이트 라인 */}
      <path d="M112,97 L138,93" stroke="white" strokeWidth="1.2" opacity="0.6" strokeLinecap="round" />
      {/* 사이드 하이라이트 */}
      <path d="M108,96 L138,91 L140,95 L112,100 Z" fill="white" opacity="0.07" />

      {/* 라디에이터 슈라우드 (탱크 옆) */}
      <path d="M160,70 L194,68 L198,80 L164,80 Z" fill="#e06000" stroke="#b04800" strokeWidth="0.8" />
      {/* 라디에이터 */}
      <rect x="164" y="72" width="28" height="22" rx="2" fill="#2a2a2a" stroke="#444" strokeWidth="1" />
      {[74, 77, 80, 83, 86, 89].map(y => (
        <line key={y} x1="165" y1={y} x2="191" y2={y} stroke="#3a3a3a" strokeWidth="1" />
      ))}
      {/* 라디에이터 캡 */}
      <circle cx="194" cy="68" r="4" fill="#555" stroke="#666" />

      {/* 시트 */}
      <path d="M78,91 L130,81 L138,91 L108,101 Z" fill="#152a5a" stroke="#0e1f45" strokeWidth="1" />
      {/* 시트 하이라이트 */}
      <path d="M82,92 L128,83 L132,87 L92,96 Z" fill="#1e3a7a" opacity="0.5" />
      {/* 시트 스티치 */}
      <path d="M85,93 L126,84" stroke="#2244aa" strokeWidth="0.8" strokeDasharray="3 2" opacity="0.6" />

      {/* 뒷 펜더 */}
      <path d="M56,106 Q49,93 58,86 Q66,80 76,90 L68,110 Z"
        fill="url(#eb_orange)" stroke="#a03000" strokeWidth="1" />
      <path d="M54,104 Q48,91 57,85 Q65,79 74,88"
        stroke="#e06000" strokeWidth="2" fill="none" strokeLinecap="round" />

      {/* ══════════════════ 앞 포크 ══════════════════ */}
      {/* 상단 (어두운, 역도립식) */}
      <line x1="193" y1="73" x2="210" y2="128" stroke="#1a1a1a" strokeWidth="10" strokeLinecap="round" />
      <line x1="199" y1="73" x2="216" y2="128" stroke="#111" strokeWidth="9" strokeLinecap="round" />
      {/* 포크 하이라이트 */}
      <line x1="194" y1="75" x2="210" y2="126" stroke="#4a4a4a" strokeWidth="2" strokeLinecap="round" />
      {/* 하단 (골드, WP 컬러) */}
      <line x1="209" y1="122" x2="214" y2="148" stroke="#a06a00" strokeWidth="10" strokeLinecap="round" />
      <line x1="215" y1="122" x2="220" y2="148" stroke="#8a5800" strokeWidth="9" strokeLinecap="round" />
      <line x1="210" y1="122" x2="214" y2="148" stroke="#d48800" strokeWidth="3" strokeLinecap="round" />
      {/* 포크 씰 영역 */}
      <line x1="208" y1="120" x2="212" y2="132" stroke="#555" strokeWidth="11" strokeLinecap="round" opacity="0.5" />

      {/* ══════════════════ 앞 펜더 ══════════════════ */}
      <path d="M202,93 Q222,97 225,115 L218,118 Q217,98 206,96 Z"
        fill="url(#eb_orange)" stroke="#a03000" strokeWidth="1" />
      <path d="M200,94 Q220,98 222,115" stroke="#e06000" strokeWidth="2" fill="none" strokeLinecap="round" />
      {/* 펜더 하이라이트 */}
      <path d="M203,94 Q218,98 220,110 L218,109 Q217,97 206,94 Z" fill="white" opacity="0.1" />

      {/* ══════════════════ 스티어링 헤드 ══════════════════ */}
      <rect x="187" y="62" width="11" height="17" rx="4" fill="#444" stroke="#555" strokeWidth="1" />
      <rect x="189" y="64" width="7" height="13" rx="2" fill="#555" />

      {/* ══════════════════ 핸들바 ══════════════════ */}
      {/* 마운트 */}
      <rect x="184" y="49" width="12" height="8" rx="3" fill="#333" stroke="#444" strokeWidth="1" />
      {/* 크로스바 */}
      <path d="M174,54 Q185,46 212,44 Q220,44 226,48"
        stroke="#1e1e1e" strokeWidth="5" fill="none" strokeLinecap="round" />
      {/* 바 패드 */}
      <rect x="190" y="44" width="22" height="5.5" rx="2.5" fill="#111" stroke="#222" />
      {/* 그립 (좌) */}
      <rect x="169" y="51" width="16" height="5.5" rx="2.5" fill="#111" stroke="#222" strokeWidth="0.8" />
      {/* 그립 (우) */}
      <rect x="224" y="45" width="12" height="5.5" rx="2.5" fill="#111" stroke="#222" strokeWidth="0.8" />
      {/* 브레이크 레버 */}
      <path d="M174,53 L166,61" stroke="#777" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M226,47 L234,55" stroke="#777" strokeWidth="2.5" strokeLinecap="round" />

      {/* ══════════════════ 넘버 플레이트 ══════════════════ */}
      <rect x="173" y="52" width="16" height="11" rx="2" fill="#ff6600" stroke="#cc4400" strokeWidth="1" />
      <rect x="175" y="54" width="12" height="7" rx="1" fill="white" />

      {/* ══════════════════ 풋페그 ══════════════════ */}
      <rect x="99" y="136" width="22" height="4.5" rx="1.5" fill="#555" stroke="#3a3a3a" strokeWidth="0.8" />
      {[103, 115].map(x => (
        <line key={x} x1={x} y1="128" x2={x} y2="136" stroke="#444" strokeWidth="2.5" strokeLinecap="round" />
      ))}
      {/* 그루브 */}
      {[102, 106, 110, 114, 118].map(x => (
        <line key={x} x1={x} y1="137" x2={x} y2="140" stroke="#3a3a3a" strokeWidth="1" />
      ))}

      {/* ══════════════════ 체인 ══════════════════ */}
      <path d="M69,152 Q94,162 119,148"
        stroke="#222" strokeWidth="3.5" fill="none" strokeLinecap="round" />
      <path d="M70,150 Q95,160 120,146"
        stroke="#444" strokeWidth="1.2" fill="none" strokeLinecap="round" strokeDasharray="3 2" />
    </svg>
  )
}
