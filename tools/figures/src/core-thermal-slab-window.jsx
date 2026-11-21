// Self-regulating window of a molten U-Pu slab (3 m x 3 m, Pu 15 %, coolant at 1,500 K on the faces).
// Values: analysis/core-thermal/results/pool_study.json (calc: pool.py window, k_eff anchored to OpenMC).
// x: thickness above the cold critical thickness (20.53 cm), in mm. y: self-regulated power, MW (log).
// Each line ends where the hottest point reaches 3,500 K while the slab is still supercritical (runaway).
export default () => <claude.Visualize data-claude-component='core-thermal-slab-window' sources={{pts:{kind:'data', data:[
  {key:'mx1', s:'mixed', x:0.066, p:79.4},{key:'mx2', s:'mixed', x:0.198, p:234.6},{key:'mx3', s:'mixed', x:0.330, p:382.9},{key:'mx4', s:'mixed', x:0.462, p:523.6},{key:'mx5', s:'mixed', x:0.594, p:656.4},{key:'mx6', s:'mixed', x:0.660, p:700.4},
  {key:'nu1', s:'nu10', x:0.047, p:19.3},{key:'nu2', s:'nu10', x:0.141, p:56.7},{key:'nu3', s:'nu10', x:0.235, p:92.2},{key:'nu4', s:'nu10', x:0.329, p:125.8},{key:'nu5', s:'nu10', x:0.423, p:157.3},{key:'nu6', s:'nu10', x:0.470, p:165.8},
  {key:'cd1', s:'cond', x:0.042, p:2.49},{key:'cd2', s:'cond', x:0.126, p:7.31},{key:'cd3', s:'cond', x:0.210, p:11.9},{key:'cd4', s:'cond', x:0.294, p:16.2},{key:'cd5', s:'cond', x:0.378, p:20.2},{key:'cd6', s:'cond', x:0.420, p:21.2},
  {key:'rd1', s:'rad', x:0.050, p:1.22},{key:'rd2', s:'rad', x:0.149, p:3.97},{key:'rd3', s:'rad', x:0.248, p:6.98},{key:'rd4', s:'rad', x:0.347, p:10.1},{key:'rd5', s:'rad', x:0.446, p:13.2},{key:'rd6', s:'rad', x:0.495, p:14.1},
  {key:'of1', s:'one', x:0.044, p:0.72},{key:'of2', s:'one', x:0.131, p:2.10},{key:'of3', s:'one', x:0.219, p:3.40},{key:'of4', s:'one', x:0.306, p:4.61},{key:'of5', s:'one', x:0.394, p:5.75},{key:'of6', s:'one', x:0.438, p:6.04}]}}}>{({pts, datum}) => {
  const xl = 80, xr = 600, yb = 380, yt = 80;
  const X = x => xl + x / 0.7 * (xr - xl);
  const lo = Math.log10(0.5), hi = Math.log10(1000);
  const Y = p => yb - (Math.log10(p) - lo) / (hi - lo) * (yb - yt);
  const ink = 'var(--cds-text-primary)', quiet = 'var(--cds-text-secondary)', grid = 'var(--cds-chart-grid)', axis = 'var(--cds-chart-axis)';
  const blue = 'var(--cds-chart-categorical-1)', muted = 'var(--cds-chart-muted)';
  const series = [
    {s:'mixed', label:'Well mixed liquid, convective faces', col: ink, dash: ''},
    {s:'nu10', label:'Convection Nu = 10', col: ink, dash: '6 4'},
    {s:'cond', label:'Conduction only, two cooled faces', col: blue, dash: ''},
    {s:'rad', label:'Radiation to a 1,500 K wall', col: muted, dash: ''},
    {s:'one', label:'Conduction, one cooled face', col: muted, dash: '6 4'}];
  const yTicks = [1, 10, 100, 1000], xTicks = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7];
  return <svg viewBox='0 0 960 470' role='img' aria-label='A molten U-Pu slab self-regulates only within about half a millimetre of thickness; heat removal sets how much power it makes there' fontSize='12'>
    <text x='24' y='28' fontSize='15' fontWeight='600' fill={ink}>A molten U–Pu slab self-regulates only within ~0.5 mm of thickness</text>
    <text x='24' y='48' fontSize='11.5' fill={quiet}>Self-regulated power vs extra thickness above cold criticality (20.53 cm), 3 m × 3 m slab, Pu 15 %, sink 1,500 K. Calculated (pool.py).</text>
    {yTicks.map(v => <g key={v}><line x1={xl} x2={xr} y1={Y(v)} y2={Y(v)} stroke={grid}/><text x={xl - 8} y={Y(v) + 4} textAnchor='end' fontSize='11.5' fill={quiet}>{v.toLocaleString('en-US')}</text></g>)}
    <text x='24' y='70' fontSize='11.5' fill={quiet}>Power (MW)</text>
    <line x1={xl} x2={xr} y1={yb} y2={yb} stroke={axis}/>
    {xTicks.map(t => <text key={t} x={X(t)} y={yb + 18} textAnchor='middle' fontSize='11.5' fill={quiet}>{t.toFixed(1)}</text>)}
    <text x={xr} y={yb + 40} textAnchor='end' fontSize='11.5' fill={quiet}>Thickness above cold criticality (mm)</text>
    {series.map(({s, label, col, dash}) => {
      const p = pts.filter(r => r.s === s);
      const d = p.map((r, i) => `${i ? 'L' : 'M'}${X(r.x).toFixed(1)} ${Y(r.p).toFixed(1)}`).join('');
      const last = p[p.length - 1];
      return <g key={s}>
        <path d={d} fill='none' stroke={col} strokeWidth='2' strokeDasharray={dash}/>
        {p.map(r => <circle key={r.key} cx={X(r.x)} cy={Y(r.p)} r='4' fill={col} stroke='#ffffff' strokeWidth='2' {...datum(r, 'p')}><title>{`${label}: ${r.p} MW at +${r.x} mm`}</title></circle>)}
        <path d={`M${X(last.x) - 5} ${Y(last.p) - 5}L${X(last.x) + 5} ${Y(last.p) + 5}M${X(last.x) - 5} ${Y(last.p) + 5}L${X(last.x) + 5} ${Y(last.p) - 5}`} stroke={col} strokeWidth='2'/>
        <text x={X(0.7) + 10} y={Y(last.p) + 4} fontSize='11.5' fill={ink}>{`${label}: ${last.p >= 100 ? Math.round(last.p) : last.p} MW`}</text>
      </g>; })}
    <text x='24' y='440' fontSize='11' fill={quiet}>× = runaway: still supercritical when the hottest point reaches 3,500 K. Thinner than 0 mm: subcritical, no power.</text>
    <text x='24' y='456' fontSize='11' fill={quiet}>All feedback from 1,500 K to 3,500 K is only ~200 pcm: Doppler ≈ 0 in this hard spectrum, and expansion nearly cancels in a laterally confined slab.</text>
  </svg>; }}</claude.Visualize>;
