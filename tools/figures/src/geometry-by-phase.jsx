export default () => {
  const ink = 'var(--cds-text-primary)', quiet = 'var(--cds-text-secondary)', edge = 'var(--cds-chart-axis)', grid = 'var(--cds-chart-grid)', fuel = 'var(--cds-chart-categorical-1)', cool = 'var(--cds-chart-reference-tint)';
  const W = 112, H = 96, gap = 8, x0 = 24, colX = i => x0 + i * (W + gap);
  const rowY = [92, 228, 364];
  const card = (i, r) => <rect x={colX(i)} y={rowY[r]} width={W} height={H} rx='8' fill='none' stroke={grid} strokeWidth='1.25'/>;
  const F = { fill: fuel, fillOpacity: 0.3, stroke: edge, strokeWidth: 1 };
  const C = { fill: cool, stroke: edge, strokeWidth: 1 };
  const cx = (i) => colX(i) + W / 2;
  const hex = [[0, 0], [-14, -8], [14, -8], [-14, 8], [14, 8], [0, -16], [0, 16]];
  const peb = [[-30, -24], [-12, -26], [6, -24], [24, -26], [-22, -8], [-4, -10], [14, -8], [32, -10], [-30, 8], [-12, 6], [6, 8], [24, 6], [-20, 24], [-2, 22], [16, 24], [34, 22]];
  const flu = [[-28, 20], [-6, 26], [18, 18], [-20, 0], [10, 4], [30, -6], [-30, -18], [0, -16], [22, -28]];
  const drops = [[-18, 22], [6, 16], [-6, 0], [16, -4], [-16, -16], [8, -22]];
  return <svg viewBox='0 0 760 500' role='img' aria-label='Reactor core geometries grouped by the phase of the fuel' fontSize='11'>
    <defs><marker id='gp-arrow' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='5' markerHeight='5' orient='auto-start-reverse'><path d='M0 0L10 5L0 10z' fill={edge}/></marker></defs>
    <text data-claude-text-id='title' x='24' y='30' fontSize='15' fontWeight='600' fill={ink}>Core geometries by fuel phase: shorter heat paths and fewer hot walls as the fuel gets more fluid</text>
    <text data-claude-text-id='subtitle' x='24' y='50' fontSize='11.5' fill={quiet}>Schematic only. Blue: fuel. Grey: coolant or carrier. IDs refer to the geometry study page.</text>

    <text data-claude-text-id='row-solid' x='24' y='84' fontSize='13' fontWeight='600' fill={ink}>Solid fuel: heat crosses fuel, then a wall, then the coolant</text>
    {/* S1 pin bundle */}
    {card(0, 0)}<rect x={colX(0) + 14} y={rowY[0] + 10} width={W - 28} height={52} rx='4' {...C}/>{hex.map(([dx, dy]) => <circle key={`${dx}${dy}`} cx={cx(0) + dx} cy={rowY[0] + 36 + dy} r='6' {...F}/>)}
    <text data-claude-text-id='s1' x={cx(0)} y={rowY[0] + 80} textAnchor='middle' fill={ink}>S1 Pin bundle</text>
    {/* S2 plates */}
    {card(1, 0)}<rect x={colX(1) + 14} y={rowY[0] + 10} width={W - 28} height={52} rx='4' {...C}/>{[0, 1, 2, 3, 4].map(k => <rect key={k} x={colX(1) + 20 + k * 15} y={rowY[0] + 14} width='6' height='44' {...F}/>)}
    <text data-claude-text-id='s2' x={cx(1)} y={rowY[0] + 80} textAnchor='middle' fill={ink}>S2 Plates</text>
    {/* S3 inverted block */}
    {card(2, 0)}<rect x={colX(2) + 14} y={rowY[0] + 10} width={W - 28} height={52} rx='4' {...F}/>{[[-24, -12], [0, -12], [24, -12], [-12, 10], [12, 10], [-24, 10], [24, 10]].map(([dx, dy]) => <circle key={`${dx}${dy}`} cx={cx(2) + dx} cy={rowY[0] + 36 + dy} r='5' {...C}/>)}
    <text data-claude-text-id='s3' x={cx(2)} y={rowY[0] + 80} textAnchor='middle' fill={ink}>S3 Inverted block</text>
    {/* S4 particle bed */}
    {card(3, 0)}<rect x={colX(3) + 10} y={rowY[0] + 6} width={W - 20} height={60} rx='4' {...C}/>{peb.map(([dx, dy]) => <circle key={`${dx}${dy}`} cx={cx(3) + dx * 0.95} cy={rowY[0] + 36 + dy * 0.95} r='7' {...F}/>)}
    <text data-claude-text-id='s4' x={cx(3)} y={rowY[0] + 80} textAnchor='middle' fill={ink}>S4 Packed bed</text>
    {/* S5 fluidised bed */}
    {card(4, 0)}<rect x={colX(4) + 10} y={rowY[0] + 6} width={W - 20} height={60} rx='4' {...C}/>{flu.map(([dx, dy]) => <circle key={`${dx}${dy}`} cx={cx(4) + dx} cy={rowY[0] + 36 + dy} r='5' {...F}/>)}<g fill='none' stroke={edge} strokeWidth='1'>{[-36, 36].map(dx => <path key={dx} d={`M${cx(4) + dx} ${rowY[0] + 62}V${rowY[0] + 14}`} markerEnd='url(#gp-arrow)'/>)}</g>
    <text data-claude-text-id='s5' x={cx(4)} y={rowY[0] + 80} textAnchor='middle' fill={ink}>S5 Fluidised bed</text>
    {/* S6 lattice */}
    {card(5, 0)}<rect x={colX(5) + 14} y={rowY[0] + 10} width={W - 28} height={52} rx='4' {...C}/><g fill='none' stroke={fuel} strokeWidth='5' strokeOpacity='0.45'>{[0, 1, 2].map(k => <path key={k} d={`M${colX(5) + 16} ${rowY[0] + 20 + k * 16}q10 -10 21 0t21 0t21 0t21 0`}/>)}</g>
    <text data-claude-text-id='s6' x={cx(5)} y={rowY[0] + 80} textAnchor='middle' fill={ink}>S6 Printed lattice</text>

    <text data-claude-text-id='row-liquid' x='24' y='220' fontSize='13' fontWeight='600' fill={ink}>Liquid fuel: the fuel can move, so the wall can move away from the hottest point</text>
    {/* L1 loop */}
    {card(0, 1)}<rect x={colX(0) + 14} y={rowY[1] + 12} width='40' height='50' rx='4' {...F}/><rect x={colX(0) + 70} y={rowY[1] + 22} width='26' height='30' rx='3' {...C}/><g fill='none' stroke={edge} strokeWidth='1'><path d={`M${colX(0) + 54} ${rowY[1] + 24}H${colX(0) + 70}`} markerEnd='url(#gp-arrow)'/><path d={`M${colX(0) + 70} ${rowY[1] + 48}H${colX(0) + 54}`} markerEnd='url(#gp-arrow)'/></g>
    <text data-claude-text-id='l1' x={cx(0)} y={rowY[1] + 80} textAnchor='middle' fill={ink}>L1 Circulating loop</text>
    {/* L2 pool + tubes */}
    {card(1, 1)}<rect x={colX(1) + 14} y={rowY[1] + 10} width={W - 28} height={52} rx='4' {...F}/>{[0, 1, 2, 3].map(k => <rect key={k} x={colX(1) + 26 + k * 18} y={rowY[1] + 6} width='7' height='60' {...C}/>)}
    <text data-claude-text-id='l2' x={cx(1)} y={rowY[1] + 80} textAnchor='middle' fill={ink}>L2 Pool + tubes</text>
    {/* L3 liquid-fuel pins */}
    {card(2, 1)}<rect x={colX(2) + 14} y={rowY[1] + 10} width={W - 28} height={52} rx='4' {...C}/>{[0, 1, 2, 3].map(k => <rect key={k} x={colX(2) + 24 + k * 18} y={rowY[1] + 14} width='9' height='44' rx='4.5' {...F}/>)}
    <text data-claude-text-id='l3' x={cx(2)} y={rowY[1] + 80} textAnchor='middle' fill={ink}>L3 Liquid-fuel pins</text>
    {/* L4 direct contact */}
    {card(3, 1)}<rect x={colX(3) + 14} y={rowY[1] + 22} width={W - 28} height={40} rx='4' {...F}/><rect x={colX(3) + 14} y={rowY[1] + 8} width={W - 28} height={14} rx='3' {...C}/>{drops.map(([dx, dy]) => <circle key={`${dx}${dy}`} cx={cx(3) + dx} cy={rowY[1] + 44 + dy * 0.6} r='4' {...C}/>)}
    <text data-claude-text-id='l4' x={cx(3)} y={rowY[1] + 80} textAnchor='middle' fill={ink}>L4 Direct contact</text>
    {/* L5 falling film */}
    {card(4, 1)}{[0, 1, 2].map(k => <g key={k}><rect x={colX(4) + 18 + k * 28} y={rowY[1] + 8} width='10' height='56' {...C}/><rect x={colX(4) + 28 + k * 28} y={rowY[1] + 8} width='4' height='56' {...F}/></g>)}<g fill='none' stroke={edge} strokeWidth='1'><path d={`M${colX(4) + 100} ${rowY[1] + 14}V${rowY[1] + 58}`} markerEnd='url(#gp-arrow)'/></g>
    <text data-claude-text-id='l5' x={cx(4)} y={rowY[1] + 80} textAnchor='middle' fill={ink}>L5 Falling film</text>
    {/* L6 rotating annulus */}
    {card(5, 1)}<circle cx={cx(5)} cy={rowY[1] + 36} r='28' {...C}/><circle cx={cx(5)} cy={rowY[1] + 36} r='28' fill='none' stroke={fuel} strokeOpacity='0.45' strokeWidth='9'/><circle cx={cx(5)} cy={rowY[1] + 36} r='12' fill='white' stroke={edge}/><path d={`M${cx(5) - 6} ${rowY[1] + 4}a32 32 0 0 1 22 6`} fill='none' stroke={edge} markerEnd='url(#gp-arrow)'/>
    <text data-claude-text-id='l6' x={cx(5)} y={rowY[1] + 80} textAnchor='middle' fill={ink}>L6 Rotating annulus</text>

    <text data-claude-text-id='row-gas' x='24' y='356' fontSize='13' fontWeight='600' fill={ink}>Gas, vapour or plasma fuel: heat leaves as radiation or charged particles</text>
    {/* G1 vortex */}
    {card(0, 2)}<circle cx={cx(0)} cy={rowY[2] + 36} r='30' {...C}/><circle cx={cx(0)} cy={rowY[2] + 36} r='14' {...F}/><path d={`M${cx(0) + 24} ${rowY[2] + 36}a24 24 0 1 1 -12 -20`} fill='none' stroke={edge} markerEnd='url(#gp-arrow)'/>
    <text data-claude-text-id='g1' x={cx(0)} y={rowY[2] + 80} textAnchor='middle' fill={ink}>G1 Open gas core</text>
    {/* G2 light bulb */}
    {card(1, 2)}<circle cx={cx(1)} cy={rowY[2] + 36} r='30' {...C}/><circle cx={cx(1)} cy={rowY[2] + 36} r='16' fill='white' stroke={edge} strokeWidth='1.5'/><circle cx={cx(1)} cy={rowY[2] + 36} r='11' {...F}/>{[0, 60, 120, 180, 240, 300].map(a => <line key={a} x1={cx(1) + 18 * Math.cos(a * Math.PI / 180)} y1={rowY[2] + 36 + 18 * Math.sin(a * Math.PI / 180)} x2={cx(1) + 27 * Math.cos(a * Math.PI / 180)} y2={rowY[2] + 36 + 27 * Math.sin(a * Math.PI / 180)} stroke={fuel} strokeWidth='1.5'/>)}
    <text data-claude-text-id='g2' x={cx(1)} y={rowY[2] + 80} textAnchor='middle' fill={ink}>G2 Closed gas core</text>
    {/* G3 vapour core */}
    {card(2, 2)}<rect x={colX(2) + 14} y={rowY[2] + 14} width='44' height='44' rx='4' {...F}/><rect x={colX(2) + 70} y={rowY[2] + 26} width='28' height='20' rx='3' {...C}/><path d={`M${colX(2) + 58} ${rowY[2] + 36}H${colX(2) + 70}`} fill='none' stroke={edge} markerEnd='url(#gp-arrow)'/><text x={colX(2) + 84} y={rowY[2] + 40} textAnchor='middle' fontSize='9' fill={quiet}>MHD</text>
    <text data-claude-text-id='g3' x={cx(2)} y={rowY[2] + 80} textAnchor='middle' fill={ink}>G3 Vapour core</text>
    {/* G4 fission fragment */}
    {card(3, 2)}{[0, 1, 2, 3].map(k => <line key={k} x1={colX(3) + 30 + k * 16} y1={rowY[2] + 12} x2={colX(3) + 30 + k * 16} y2={rowY[2] + 60} stroke={fuel} strokeOpacity='0.6' strokeWidth='2'/>)}<g fill='none' stroke={edge} strokeWidth='1'>{[0, 1, 2].map(k => <path key={k} d={`M${colX(3) + 34 + k * 16} ${rowY[2] + 28 + k * 8}h9`} markerEnd='url(#gp-arrow)'/>)}</g>
    <text data-claude-text-id='g4' x={cx(3)} y={rowY[2] + 80} textAnchor='middle' fill={ink}>G4 Fragment direct</text>
    {/* G5 dust / aerosol */}
    {card(4, 2)}<rect x={colX(4) + 14} y={rowY[2] + 10} width={W - 28} height={52} rx='4' {...C}/>{[[-30, -14], [-14, 8], [0, -10], [12, 14], [26, -4], [-22, 18], [20, -18], [-4, 20], [32, 12]].map(([dx, dy]) => <circle key={`${dx}${dy}`} cx={cx(4) + dx} cy={rowY[2] + 36 + dy} r='2.5' fill={fuel} fillOpacity='0.7'/>)}
    <text data-claude-text-id='g5' x={cx(4)} y={rowY[2] + 80} textAnchor='middle' fill={ink}>G5 Dust suspension</text>

    <g data-claude-anchor='key'><rect x='24' y='470' width='16' height='12' rx='2' fill={fuel} fillOpacity='0.3' stroke={edge}/><text data-claude-text-id='key-fuel' x='46' y='480' fill={quiet}>Fuel</text><rect x='100' y='470' width='16' height='12' rx='2' fill={cool} stroke={edge}/><text data-claude-text-id='key-cool' x='122' y='480' fill={quiet}>Coolant or carrier</text><text data-claude-text-id='key-note' x='250' y='480' fill={quiet}>Arrows show flow or rotation. S5 and L4 are moving-bed and droplet designs.</text></g>
  </svg>;
};
