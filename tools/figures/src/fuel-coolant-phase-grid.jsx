// Fuel phase x coolant phase grid. Verdicts are the study's qualitative judgements (docs/studies/geometry-by-phase.md).
// v: 3 promising, 2 possible with caveats, 1 unlikely, 0 ruled out, null not meaningful.
export default () => {
  const cols = [['K-S', 'Solid', 'conduction'], ['K-P', 'Granular', 'solid'], ['K-M', 'Melting', 'carrier'], ['K-L', 'Liquid', ''], ['K-B', 'Boiling /', 'heat pipe'], ['K-SC', 'Super-', 'critical'], ['K-G', 'Gas', ''], ['K-PL', 'Plasma', ''], ['K-R', 'Radiative', '']];
  const rows = [
    ['Solid fuel', [[1, 'S7'], [2, 'S8'], [1, ''], [3, 'S1 S2 S3 S6'], [2, 'S3 + HP'], [2, 'S1'], [3, 'S1 S4 S5 S6'], [1, 'S4'], [2, 'S9']]],
    ['Liquid fuel', [[null, ''], [1, ''], [2, 'L4-M'], [3, 'L1 L2 L3 L5'], [2, 'L4 (X3)'], [1, ''], [2, 'L4'], [1, ''], [2, 'L7']]],
    ['Gas / plasma fuel', [[null, ''], [null, ''], [null, ''], [0, ''], [0, ''], [0, ''], [0, 'G1 G2'], [0, 'G1'], [0, 'G2']]],
  ];
  const ink = 'var(--cds-text-primary)', quiet = 'var(--cds-text-secondary)', grid = 'var(--cds-chart-grid)', acc = 'var(--cds-chart-categorical-1)', grey = 'var(--cds-chart-muted)';
  const x0 = 150, cw = 64, y0 = 108, rh = 74;
  const fillFor = v => v === 3 ? acc : v === 2 ? acc : v === 1 ? grey : v === 0 ? 'none' : 'none';
  const opFor = v => v === 3 ? 0.85 : v === 2 ? 0.35 : v === 1 ? 0.5 : 0;
  const mark = (v, x, y) => v === null ? <text x={x} y={y + 4} textAnchor='middle' fill={quiet}>—</text>
    : v === 0 ? <g stroke={grey} strokeWidth='2'><line x1={x - 7} y1={y - 7} x2={x + 7} y2={y + 7}/><line x1={x + 7} y1={y - 7} x2={x - 7} y2={y + 7}/></g>
    : <circle cx={x} cy={y} r={v === 3 ? 13 : v === 2 ? 11 : 8} fill={fillFor(v)} fillOpacity={opFor(v)} stroke={v === 1 ? grey : acc} strokeWidth='1.5'/>;
  return <svg viewBox='0 0 760 392' role='img' aria-label='Fuel phase by coolant phase: where high-temperature breeder concepts can live' fontSize='11'>
    <text data-claude-text-id='title' x='24' y='30' fontSize='15' fontWeight='600' fill={ink}>Condensed fuel with liquid or gas coolant is the core of the space; gas fuel cannot breed</text>
    <text data-claude-text-id='subtitle' x='24' y='50' fontSize='11.5' fill={quiet}>Fuel phase by coolant phase (heat-transport mode). Labels are geometry IDs from the study page.</text>
    {cols.map(([code, a, b], i) => <g key={code}><text x={x0 + i * cw + cw / 2} y={76} textAnchor='middle' fontWeight='600' fill={ink}>{a}</text><text x={x0 + i * cw + cw / 2} y={90} textAnchor='middle' fill={quiet}>{b || ' '}</text></g>)}
    {rows.map(([name, cells], r) => <g key={name}>
      <line x1='24' x2={x0 + 9 * cw} y1={y0 + r * rh - 4} y2={y0 + r * rh - 4} stroke={grid}/>
      <text x='24' y={y0 + r * rh + 30} fontSize='12' fontWeight='600' fill={ink}>{name}</text>
      {cells.map(([v, ids], i) => <g key={i}>{mark(v, x0 + i * cw + cw / 2, y0 + r * rh + 24)}<text x={x0 + i * cw + cw / 2} y={y0 + r * rh + 54} textAnchor='middle' fontSize='10' fill={quiet}>{ids}</text></g>)}
    </g>)}
    <g data-claude-anchor='legend'>
      <circle cx='34' cy='350' r='11' fill={acc} fillOpacity='0.85' stroke={acc} strokeWidth='1.5'/><text data-claude-text-id='leg-3' x='52' y='354' fill={quiet}>Promising</text>
      <circle cx='150' cy='350' r='9' fill={acc} fillOpacity='0.35' stroke={acc} strokeWidth='1.5'/><text data-claude-text-id='leg-2' x='166' y='354' fill={quiet}>Possible with caveats</text>
      <circle cx='310' cy='350' r='7' fill={grey} fillOpacity='0.5' stroke={grey} strokeWidth='1.5'/><text data-claude-text-id='leg-1' x='324' y='354' fill={quiet}>Unlikely</text>
      <g stroke={grey} strokeWidth='2'><line x1='413' y1='344' x2='425' y2='356'/><line x1='425' y1='344' x2='413' y2='356'/></g><text data-claude-text-id='leg-0' x='434' y='354' fill={quiet}>Ruled out (not a breeder)</text>
      <text x='600' y='354' fill={quiet}>—</text><text data-claude-text-id='leg-na' x='614' y='354' fill={quiet}>Not meaningful</text>
      <text data-claude-text-id='note' x='24' y='378' fill={quiet}>Qualitative judgements from the study, to be replaced by screening results. HP: heat pipes.</text>
    </g>
  </svg>;
};
