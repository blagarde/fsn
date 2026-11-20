// Saturation solubility of wall materials in liquid aluminium vs temperature.
// Values: analysis/a-family/results/chemistry.json (calc). ZrB2: COST 507 Al-B-Zr liquid with a ZrB2 phase
// added from NIST-JANAF; TiB2 and AlN: COST 507 only. Metal (Zr, Ti) or N atom % in the liquid.
// The 0.1 at% line is the default R2 margin in docs/framework/materials-selection.md.
export default () => <claude.Visualize data-claude-component='a-family-solubility' sources={{pts:{kind:'data', data:[
  {key:'zrb2-1600', m:'ZrB2', T:1600, x:0.0454},{key:'zrb2-1900', m:'ZrB2', T:1900, x:0.1854},{key:'zrb2-2100', m:'ZrB2', T:2100, x:0.3815},{key:'zrb2-2300', m:'ZrB2', T:2300, x:0.699},
  {key:'tib2-1600', m:'TiB2', T:1600, x:0.0206},{key:'tib2-1900', m:'TiB2', T:1900, x:0.0828},{key:'tib2-2100', m:'TiB2', T:2100, x:0.1715},{key:'tib2-2300', m:'TiB2', T:2300, x:0.3196},
  {key:'aln-1600', m:'AlN', T:1600, x:0.0814},{key:'aln-1900', m:'AlN', T:1900, x:0.1059},{key:'aln-2100', m:'AlN', T:2100, x:0.1211},{key:'aln-2300', m:'AlN', T:2300, x:0.1352}]},
  marks:{kind:'data', data:[{key:'a1', label:'A1 outlet ~1,570 °C', T:1843},{key:'a2', label:'A2 outlet ~1,750 °C', T:2023}]}}}>{({pts, marks, datum}) => {
  const xl = 80, xr = 640, yb = 360, yt = 80;
  const X = T => xl + (T - 1500) / 900 * (xr - xl);
  const lo = Math.log10(0.01), hi = Math.log10(1.0);
  const Y = x => yb - (Math.log10(x) - lo) / (hi - lo) * (yb - yt);
  const ink = 'var(--cds-text-primary)', quiet = 'var(--cds-text-secondary)', grid = 'var(--cds-chart-grid)', axis = 'var(--cds-chart-axis)', refc = 'var(--cds-chart-reference)';
  const col = {ZrB2: 'var(--cds-chart-categorical-1)', TiB2: 'var(--cds-chart-muted)', AlN: 'var(--cds-text-primary)'};
  const series = ['ZrB2', 'TiB2', 'AlN'];
  const yTicks = [0.01, 0.03, 0.1, 0.3, 1.0], xTicks = [1500, 1700, 1900, 2100, 2300];
  return <svg viewBox='0 0 760 430' role='img' aria-label='Diborides dissolve ten times more between 1,600 and 2,100 K; AlN solubility is high but flat' fontSize='12'>
    <text x='24' y='28' fontSize='15' fontWeight='600' fill={ink}>Above ~1,800 K, liquid Al dissolves more than 0.1 at% of every Al-side wall</text>
    <text x='24' y='48' fontSize='11.5' fill={quiet}>Saturation content of Zr, Ti or N in liquid Al (atom %, log scale). Calculated: COST 507 CALPHAD; ZrB2 phase added from NIST-JANAF.</text>
    <g>{yTicks.map(v => <g key={v}><line x1={xl} x2={xr} y1={Y(v)} y2={Y(v)} stroke={grid}/><text x={xl - 8} y={Y(v) + 4} textAnchor='end' fontSize='11.5' fill={quiet}>{`${v}%`}</text></g>)}
      <text x='24' y='70' fontSize='11.5' fill={quiet}>Solute in liquid Al</text></g>
    <line x1={xl} x2={xr} y1={Y(0.1)} y2={Y(0.1)} stroke={refc} strokeWidth='1.5' strokeDasharray='5 4'/>
    <text x={xl + 6} y={Y(0.1) - 6} fontSize='11.5' fill={quiet}>R2 margin 0.1 at%</text>
    {marks.map(m => <g key={m.key}><line x1={X(m.T)} x2={X(m.T)} y1={yt} y2={yb} stroke={axis} strokeDasharray='2 3' {...datum(m)}/><text x={X(m.T) + 4} y={yt + 12} fontSize='11' fill={quiet}>{m.label}</text></g>)}
    <g><line x1={xl} x2={xr} y1={yb} y2={yb} stroke={axis}/>{xTicks.map(t => <text key={t} x={X(t)} y={yb + 18} textAnchor='middle' fontSize='11.5' fill={quiet}>{t.toLocaleString('en-US')}</text>)}
      <text x={xr} y={yb + 40} textAnchor='end' fontSize='11.5' fill={quiet}>Temperature (K)</text></g>
    {series.map(s => { const p = pts.filter(r => r.m === s); const d = p.map((r, i) => `${i ? 'L' : 'M'}${X(r.T).toFixed(1)} ${Y(r.x).toFixed(1)}`).join('');
      const last = p[p.length - 1];
      return <g key={s}><path d={d} fill='none' stroke={col[s]} strokeWidth='2'/>{p.map(r => <circle key={r.key} cx={X(r.T)} cy={Y(r.x)} r='3.5' fill={col[s]} {...datum(r, 'x')}><title>{`${s} at ${r.T} K: ${r.x}% in liquid Al`}</title></circle>)}
        <text x={X(last.T) + 8} y={Y(last.x) + 4} fontSize='12' fontWeight='600' fill={ink}>{s}</text></g>; })}
  </svg>; }}</claude.Visualize>;
