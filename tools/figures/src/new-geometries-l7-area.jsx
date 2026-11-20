// L7 radiatively coupled pool: radiating area needed for 1,000 MWth vs coolant outlet temperature.
// Values: analysis/new-geometries/thermal.py -> results/thermal.json (L7.flux_grid, Al/AlN panel,
// coolant inlet 1,000 C, hot container surface uniform). Emissivities approximate (W bare 0.3,
// coated 0.8; AlN receiver 0.8). A2 point from docs/designs/A2.md (3 MW/m2 through the tube wall,
// Al outlet ~1,750 C).
export default () => <claude.Visualize data-claude-component='new-geometries-l7-area' sources={{grid:{kind:'data', data:[{Th:2000,Tout:1300,eps:0.3,area:2837},{Th:2000,Tout:1500,eps:0.3,area:3069},{Th:2000,Tout:1700,eps:0.3,area:3492},{Th:2000,Tout:1300,eps:0.8,area:1202},{Th:2000,Tout:1500,eps:0.8,area:1304},{Th:2000,Tout:1700,eps:0.8,area:1490},{Th:2200,Tout:1300,eps:0.3,area:1920},{Th:2200,Tout:1500,eps:0.3,area:2021},{Th:2200,Tout:1700,eps:0.3,area:2181},{Th:2200,Tout:1300,eps:0.8,area:814},{Th:2200,Tout:1500,eps:0.8,area:859},{Th:2200,Tout:1700,eps:0.8,area:931}]}, a2:{kind:'data', data:[{Tout:1750, area:333}]}}}>{({grid, a2, datum}) => {
  const xl = 80, xr = 560, yb = 390, yt = 105;
  const X = t => xl + (t - 1250) / 600 * (xr - xl), Y = a => yb - a / 4000 * (yb - yt);
  const ink = 'var(--cds-text-primary)', quiet = 'var(--cds-text-secondary)', grey = 'var(--cds-chart-muted)', gridc = 'var(--cds-chart-grid)', axis = 'var(--cds-chart-axis)', acc = 'var(--cds-chart-categorical-1)';
  const series = [
    {Th: 2000, eps: 0.3, c: grey, dash: '', label: 'Bare W (ε 0.3), can at 2,000 °C', short: 'Bare W, can 2,000 °C'},
    {Th: 2200, eps: 0.3, c: grey, dash: '5 4', label: 'Bare W (ε 0.3), can at 2,200 °C', short: 'Bare W, can 2,200 °C'},
    {Th: 2000, eps: 0.8, c: acc, dash: '', label: 'Coated W (ε 0.8), can at 2,000 °C', short: 'Coated W, can 2,000 °C'},
    {Th: 2200, eps: 0.8, c: acc, dash: '5 4', label: 'Coated W (ε 0.8), can at 2,200 °C', short: 'Coated W, can 2,200 °C'},
  ];
  const pts = s => grid.filter(r => r.Th === s.Th && r.eps === s.eps).sort((a, b) => a.Tout - b.Tout);
  const p = a2.at(0);
  return <svg viewBox='0 0 820 460' role='img' aria-label='Radiating area needed for 1,000 MWth: 800 to 3,500 square metres, 2.5 to 10 times A2' fontSize='12'>
    <text x='24' y='28' fontSize='15' fontWeight='600' fill={ink}>L7 needs 2.5–10× the heat-transfer area of A2</text>
    <text x='24' y='48' fontSize='11.5' fill={quiet}>Radiating area for 1,000 MWth vs coolant outlet; coolant inlet 1,000 °C, AlN receiver ε 0.8 (approx.).</text>
    <text x='24' y='64' fontSize='11.5' fill={quiet}>Calculated with analysis/new-geometries/thermal.py; A2 value from the A2 design page.</text>
    <g>{[0, 1000, 2000, 3000, 4000].map(v => <g key={v}><line x1={xl} x2={xr} y1={Y(v)} y2={Y(v)} stroke={gridc}/><text x={xl - 8} y={Y(v) + 4} textAnchor='end' fontSize='11.5' fill={quiet}>{v.toLocaleString('en-US')}</text></g>)}
      <text x='24' y='90' fontSize='11.5' fill={quiet}>Area (m²)</text></g>
    <g><line x1={xl} x2={xr} y1={yb} y2={yb} stroke={axis}/>{[1300, 1500, 1700].map(t => <text key={t} x={X(t)} y={yb + 18} textAnchor='middle' fontSize='11.5' fill={quiet}>{t.toLocaleString('en-US')}</text>)}
      <text x={xr} y={yb + 40} textAnchor='end' fontSize='11.5' fill={quiet}>Coolant outlet temperature (°C)</text></g>
    {series.map(s => { const q = pts(s); const d = q.map((r, i) => `${i ? 'L' : 'M'}${X(r.Tout).toFixed(1)} ${Y(r.area).toFixed(1)}`).join('');
      return <g key={s.label}><path d={d} fill='none' stroke={s.c} strokeWidth='2' strokeDasharray={s.dash}/>{q.map(r => <circle key={r.Tout} cx={X(r.Tout)} cy={Y(r.area)} r='3.5' fill={s.c} {...datum(r, 'area')}><title>{`${s.label}, outlet ${r.Tout} °C: ${r.area.toLocaleString('en-US')} m²`}</title></circle>)}</g>; })}
    <circle cx={X(p.Tout)} cy={Y(p.area)} r='5' fill={ink} {...datum(p, 'area')}/>
    <text x={X(p.Tout) - 8} y={Y(p.area) - 10} textAnchor='end' fontSize='11.5' fill={ink}>A2 tube wall, 3 MW/m² (333 m²)</text>
    <g>{series.map((s, i) => <g key={s.label}><line x1='590' x2='620' y1={110 + i * 26} y2={110 + i * 26} stroke={s.c} strokeWidth='2' strokeDasharray={s.dash}/><text x='628' y={114 + i * 26} fontSize='11.5' fill={quiet}>{s.short}</text></g>)}</g>
  </svg>; }}</claude.Visualize>;
