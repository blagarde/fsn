// Proposed boiling-capped pressure-cooker core (docs/studies/boiling-pressure-cooker.md).
// Numbers: analysis/boiling-pool/results/design.json (calc). Not to scale.
export default () => {
  const ink = 'var(--cds-text-primary)', quiet = 'var(--cds-text-secondary)', grid = 'var(--cds-chart-grid)';
  const muted = 'var(--cds-chart-muted)', tint = 'var(--cds-chart-reference-tint)', blue = 'var(--cds-chart-categorical-1)', axis = 'var(--cds-chart-axis)';
  const pins = [0, 1, 2, 3, 4, 5, 6, 7, 8];
  // left panel geometry
  const cx0 = 70, cx1 = 410, coreTop = 250, coreBot = 400;
  const pinX = i => cx0 + 30 + i * 35;
  return <svg viewBox='0 0 1130 610' role='img' aria-label='Proposed pressure-cooker core: about 1,930 sealed liquid U-Pu pins with a boiling lead cap, in flowing aluminium; detail of one pin' fontSize='12'>
    <defs>
      <marker id='arr' viewBox='0 0 10 10' refX='8' refY='5' markerWidth='7' markerHeight='7' orient='auto-start-reverse'>
        <path d='M0 0L10 5L0 10z' fill={quiet}/></marker>
      <pattern id='hatch' width='6' height='6' patternUnits='userSpaceOnUse' patternTransform='rotate(45)'>
        <rect width='6' height='6' fill={tint}/><line x1='0' y1='0' x2='0' y2='6' stroke={muted} strokeWidth='2'/></pattern>
    </defs>
    <text x='24' y='30' fontSize='15' fontWeight='600' fill={ink}>Proposed design: sealed U–Pu “pressure-cooker” pins with a boiling Pb cap, in flowing Al</text>
    <text x='24' y='50' fontSize='11.5' fill={quiet}>1 GWth reference (calc): ~1,930 pins, 3.8 m³ (59 t) liquid U–Pu, core 3.4 m × 1 m, Al 1,300 → 1,500 K. Not to scale.</text>

    {/* ---------- left: core side cut ---------- */}
    <text x={cx0 - 40} y='80' fontSize='13' fontWeight='600' fill={ink}>Core, side cut</text>
    {/* blanket and reflector */}
    <rect x={cx0 - 40} y={coreTop - 40} width={cx1 - cx0 + 80} height={coreBot - coreTop + 80} fill={grid} stroke={axis}/>
    <rect x={cx0 - 20} y={coreTop - 20} width={cx1 - cx0 + 40} height={coreBot - coreTop + 40} fill='url(#hatch)' stroke={axis}/>
    {/* Al plenum: core region and upper plenum */}
    <rect x={cx0} y={110} width={cx1 - cx0} height={coreBot - 110} fill={tint} stroke={ink}/>
    {pins.map(i => <g key={i}>
      <rect x={pinX(i) - 8} y={coreTop} width='16' height={coreBot - coreTop} fill={blue} stroke={ink}/>
      <rect x={pinX(i) - 8} y={coreTop - 8} width='16' height='8' fill={muted} stroke={ink}/>
      <rect x={pinX(i) - 8} y={150} width='16' height={coreTop - 158} fill='#ffffff' stroke={ink}/>
      <line x1={pinX(i)} y1={150} x2={pinX(i)} y2={130} stroke={ink}/>
    </g>)}
    {/* pressure header */}
    <line x1={pinX(0)} y1={130} x2={pinX(8)} y2={130} stroke={ink} strokeWidth='3'/>
    <line x1={pinX(8)} y1={130} x2={cx1 + 60} y2={130} stroke={ink} strokeWidth='3'/>
    <circle cx={cx1 + 70} cy={130} r='10' fill='#ffffff' stroke={ink} strokeWidth='2'/>
    <text x={cx1 + 70} y={134} textAnchor='middle' fontSize='11' fill={ink}>P</text>
    <text x={cx1 + 86} y={126} fontSize='11.5' fill={ink}>Ar pressure</text>
    <text x={cx1 + 86} y={141} fontSize='11.5' fill={quiet}>sets the cap</text>
    <text x={pinX(0)} y={122} fontSize='11.5' fill={quiet}>common gas header</text>
    {/* Al flow arrows */}
    <line x1={cx0 + 12} y1={coreBot + 70} x2={cx0 + 12} y2={coreBot - 4} stroke={quiet} strokeWidth='2' markerEnd='url(#arr)'/>
    <line x1={cx1 - 12} y1={coreBot + 70} x2={cx1 - 12} y2={coreBot - 4} stroke={quiet} strokeWidth='2' markerEnd='url(#arr)'/>
    <text x={cx0 + 20} y={coreBot + 64} fontSize='11.5' fill={ink}>Al in 1,300 K</text>
    <line x1={cx1 - 30} y1={168} x2={cx1 + 50} y2={168} stroke={quiet} strokeWidth='2' markerEnd='url(#arr)'/>
    <text x={cx1 + 54} y={172} fontSize='11.5' fill={ink}>Al out 1,500 K</text>
    <text x={cx1 + 54} y={187} fontSize='11.5' fill={quiet}>4,250 kg/s</text>
    {/* labels */}
    <text x={cx1 + 54} y={coreTop + 40} fontSize='11.5' fill={ink}>Active core</text>
    <text x={cx1 + 54} y={coreTop + 55} fontSize='11.5' fill={quiet}>3.4 m wide × 1 m</text>
    <line x1={cx1 + 50} y1={coreTop + 45} x2={cx1 - 4} y2={coreTop + 45} stroke={quiet}/>
    <text x={cx1 + 54} y={coreBot + 8} fontSize='11.5' fill={ink}>W reflector 20 cm</text>
    <line x1={cx1 + 50} y1={coreBot + 4} x2={cx1 + 10} y2={coreBot + 4} stroke={quiet}/>
    <text x={cx1 + 54} y={coreBot + 30} fontSize='11.5' fill={ink}>Depleted-U blanket</text>
    <line x1={cx1 + 50} y1={coreBot + 26} x2={cx1 + 30} y2={coreBot + 26} stroke={quiet}/>
    <text x={cx0 - 40} y={coreBot + 108} fontSize='11.5' fill={quiet}>Pins hang in the Al stream; fuel never touches</text>
    <text x={cx0 - 40} y={coreBot + 123} fontSize='11.5' fill={quiet}>the Al. Each pin is a small sealed pressure cooker.</text>

    {/* ---------- right: one pin ---------- */}
    <g transform='translate(170,0)'>
    <text x='640' y='80' fontSize='13' fontWeight='600' fill={ink}>One pin (r 2.5 cm)</text>
    {/* Al flow either side */}
    <rect x='640' y='95' width='150' height='450' fill={tint}/>
    <line x1='652' y1='530' x2='652' y2='110' stroke={quiet} strokeWidth='2' markerEnd='url(#arr)'/>
    <line x1='778' y1='530' x2='778' y2='110' stroke={quiet} strokeWidth='2' markerEnd='url(#arr)'/>
    {/* tube: TiB2 outer, W-25Re, contents */}
    <rect x='670' y='110' width='90' height='420' rx='6' fill={muted} stroke={ink}/>
    <rect x='676' y='110' width='78' height='414' rx='4' fill={ink}/>
    <rect x='682' y='116' width='66' height='164' fill='#ffffff'/>
    <rect x='682' y='280' width='66' height='14' fill={muted}/>
    <rect x='682' y='294' width='66' height='224' fill={blue}/>
    {/* bubbles hint on overpower */}
    {[[700, 320], [725, 350], [710, 390], [732, 300]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r='4' fill='#ffffff' opacity='0.85'/>)}
    <line x1='715' y1='116' x2='715' y2='96' stroke={ink} strokeWidth='2'/>
    <text x='722' y='100' fontSize='11' fill={quiet}>to gas header</text>
    {/* callouts left */}
    <text x='630' y='200' textAnchor='end' fontSize='11.5' fill={ink}>Gas plenum</text>
    <text x='630' y='215' textAnchor='end' fontSize='11.5' fill={quiet}>Ar + Pb vapour, 1.9 bar</text>
    <line x1='634' y1='204' x2='682' y2='204' stroke={quiet}/>
    <text x='630' y='284' textAnchor='end' fontSize='11.5' fill={ink}>Pb layer (boiling cap)</text>
    <text x='630' y='299' textAnchor='end' fontSize='11.5' fill={quiet}>boils at 2,150 K at 1.9 bar</text>
    <line x1='634' y1='287' x2='682' y2='287' stroke={quiet}/>
    <text x='630' y='400' textAnchor='end' fontSize='11.5' fill={ink}>Liquid U–Pu, 1 m column</text>
    <text x='630' y='415' textAnchor='end' fontSize='11.5' fill={quiet}>264 MW/m³, ≤ 1,970 K in operation</text>
    <text x='630' y='430' textAnchor='end' fontSize='11.5' fill={quiet}>convection: 146 K to the wall</text>
    <line x1='634' y1='404' x2='682' y2='404' stroke={quiet}/>
    {/* callouts right */}
    <text x='800' y='330' fontSize='11.5' fill={ink}>W-25Re tube 1.5 mm</text>
    <text x='800' y='345' fontSize='11.5' fill={quiet}>inner face 1,830 K</text>
    <line x1='796' y1='334' x2='752' y2='334' stroke={quiet}/>
    <text x='800' y='380' fontSize='11.5' fill={ink}>TiB2 layer 1 mm</text>
    <text x='800' y='395' fontSize='11.5' fill={quiet}>Al face 1,710 K</text>
    <line x1='796' y1='384' x2='760' y2='384' stroke={quiet}/>
    <text x='800' y='430' fontSize='11.5' fill={ink}>Al 0.4 m/s</text>
    <text x='800' y='445' fontSize='11.5' fill={quiet}>3 MW/m² through the wall</text>
    <line x1='796' y1='434' x2='782' y2='434' stroke={quiet}/>
    {/* how the cap works */}
    <rect x='500' y='556' width='440' height='38' fill={tint} stroke={axis}/>
    <text x='510' y='572' fontSize='11.5' fill={ink}>Overpower or loss of cooling: fuel reaches 2,150 K, Pb and fuel-side bubbles form,</text>
    <text x='510' y='587' fontSize='11.5' fill={ink}>void worth −175 to −570 pcm per % (OpenMC): the core shuts itself down.</text>
    </g>
  </svg>;
};
