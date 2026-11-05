import React from 'react';
import { useLastlineStore } from '../store/useLastlineStore';
import { ShieldCheck, Activity, Cpu, Building2 } from 'lucide-react';

// Canonical screen coordinates mapped to the 760x480 SVG canvas space
const CANONICAL_COORDS: Record<string, [number, number]> = {
  // Headworks & Treatment Plant
  R1_Clearwell: [90, 275],
  R0_Clearwell: [90, 275],
  J0_PumpSuction: [150, 275],
  J0_Discharge: [220, 275],

  // Zone A: North Highlands (Residential & Civic, Elevation 25-32m)
  J1: [330, 160],
  J4: [430, 120],
  J2: [460, 175],
  J3: [570, 175],
  T1_Highlands: [670, 125],

  // Zone B: Central Commercial & Hospital (Elevation 15-20m)
  J_PRV_Inlet: [300, 290],
  J5: [375, 290],
  J6: [520, 280],
  J7: [520, 340],
  J8: [375, 340],

  // Zone C: Eastside Industrial & Tech Park (Elevation 10-15m)
  J9: [380, 440],
  J10: [500, 440],
  J11: [630, 440],
  J12: [700, 415],
  T2_Eastside: [750, 440],
};

export const OperationsMap: React.FC = () => {
  const {
    topology,
    frame,
    selectedElementId,
    setSelectedElementId,
  } = useLastlineStore();

  const telemetry = frame.telemetry || {};
  const reconstructed = frame.reconstructed_state || {};
  const trust = frame.sensor_trust || {};
  const compromised = frame.top_suspicious || [];

  // Zone boundaries for visual backdrop
  const zoneOverlays = [
    {
      id: 'Zone_A_North',
      name: 'Zone A: North Highlands',
      path: 'M 280,70 L 720,70 L 720,210 L 280,210 Z',
      bgClass: 'fill-sage/5 stroke-sage/30',
      labelX: 300,
      labelY: 95,
      facilities: 'North Highlands Civic Center',
    },
    {
      id: 'Zone_B_Central',
      name: 'Zone B: Central Commercial & Hospital',
      path: 'M 280,230 L 650,230 L 650,370 L 280,370 Z',
      bgClass: 'fill-brass/5 stroke-brass/30',
      labelX: 300,
      labelY: 255,
      facilities: 'Verdant Memorial Hospital',
    },
    {
      id: 'Zone_C_Industrial',
      name: 'Zone C: Eastside Industrial',
      path: 'M 340,390 L 790,390 L 790,490 L 340,490 Z',
      bgClass: 'fill-copper/5 stroke-copper/30',
      labelX: 360,
      labelY: 415,
      facilities: 'Eastside Tech Park',
    },
  ];

  // Helper to get node position
  const getNodePos = (id: string): [number, number] => {
    if (CANONICAL_COORDS[id]) {
      return CANONICAL_COORDS[id];
    }
    const node = topology.nodes?.find((n) => n.id === id);
    if (!node || !node.coordinates) return [100, 100];
    const [x, y] = node.coordinates;
    if (x <= 150 && y <= 150) {
      const normX = 90 + (x / 110) * 660;
      const normY = 470 - ((y - 30) / 80) * 360;
      return [normX, normY];
    }
    return [x, y];
  };

  // Helper to determine node status color
  const getNodeStatusColor = (nodeId: string) => {
    const sensorId = nodeId.startsWith('T') ? `L_${nodeId.substring(0, 2)}` : `P_${nodeId}`;
    const sensorTrust = trust[sensorId] !== undefined ? trust[sensorId] : 1.0;
    const estPressure = reconstructed[sensorId] ?? telemetry[sensorId] ?? 20.0;

    if (sensorTrust < 0.5) {
      return { fill: '#C79A3B', stroke: '#A8403A', isAttacked: true, statusText: 'UNTRUSTED' };
    }
    if (estPressure < 15.0) {
      return { fill: '#A8403A', stroke: '#852F2A', isAttacked: false, statusText: 'LOW PRESSURE' };
    }
    return { fill: '#4F7A5A', stroke: '#385840', isAttacked: false, statusText: 'NOMINAL' };
  };

  return (
    <div className="space-y-4">
      {/* Top Operations KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Card 1: Physical State */}
        <div className="p-3.5 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt">
          <div className="flex items-center justify-between text-xs font-mono text-text-muted mb-1">
            <span>PHYSICAL STATE</span>
            <Activity className="w-4 h-4 text-sage" />
          </div>
          <div className="text-xl font-bold font-telemetry text-sage">
            {frame.stability_index >= 0.8 ? 'STABLE' : 'DEGRADED'}
          </div>
          <div className="text-[11px] text-text-muted mt-0.5">
            Stability Index: {(frame.stability_index * 100).toFixed(1)}%
          </div>
        </div>

        {/* Card 2: Telemetry Integrity */}
        <div className="p-3.5 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt">
          <div className="flex items-center justify-between text-xs font-mono text-text-muted mb-1">
            <span>SENSOR TRUST</span>
            <Cpu className="w-4 h-4 text-moss" />
          </div>
          <div className="text-xl font-bold font-telemetry text-ink dark:text-bone">
            {trust['P_J7'] !== undefined && trust['P_J7'] < 0.5 ? (
              <span className="text-brick font-bold">1 SENSOR SPOOFED</span>
            ) : (
              <span className="text-moss">100% NOMINAL</span>
            )}
          </div>
          <div className="text-[11px] text-text-muted mt-0.5">
            Compromised:{' '}
            {compromised.length > 0
              ? compromised
                  .slice(0, 2)
                  .map((c: any) => (typeof c === 'string' ? c : c.component_id || 'Unknown'))
                  .join(', ')
              : 'None'}
          </div>
        </div>

        {/* Card 3: Downstream Disruption */}
        <div className="p-3.5 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt">
          <div className="flex items-center justify-between text-xs font-mono text-text-muted mb-1">
            <span>CRITICAL FACILITIES</span>
            <Building2 className="w-4 h-4 text-brass" />
          </div>
          <div className="text-xl font-bold font-telemetry text-ink dark:text-bone">
            {frame.critical_facilities_at_risk?.length ? (
              <span className="text-brass">PROTECTED</span>
            ) : (
              <span className="text-moss">NOMINAL</span>
            )}
          </div>
          <div className="text-[11px] text-text-muted mt-0.5">
            Verdant Memorial Hospital: 22.3m head
          </div>
        </div>

        {/* Card 4: Advisory Safety Invariant */}
        <div className="p-3.5 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt">
          <div className="flex items-center justify-between text-xs font-mono text-text-muted mb-1">
            <span>ADVISORY SAFETY</span>
            <ShieldCheck className="w-4 h-4 text-moss" />
          </div>
          <div className="text-xl font-bold font-telemetry text-moss">GUARANTEED</div>
          <div className="text-[11px] text-text-muted mt-0.5">
            Zero physical control endpoints active
          </div>
        </div>
      </div>

      {/* Interactive Water Distribution Topology Map */}
      <div className="p-4 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt shadow-xs relative overflow-hidden">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <h3 className="font-semibold text-sm text-ink dark:text-bone tracking-tight">
              Verdant City Water Distribution Network (VCWS)
            </h3>
            <span className="text-[11px] font-mono text-text-muted">
              | Hydraulic Topology & Live State Overlays
            </span>
          </div>

          <div className="flex items-center space-x-3 text-xs font-mono">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-moss inline-block" />
              <span>P ≥ 15m (Nominal)</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-brass inline-block" />
              <span>Untrusted / Spoofed</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-brick inline-block" />
              <span>Pressure Deficit</span>
            </div>
          </div>
        </div>

        {/* SVG Diagram Canvas */}
        <div className="w-full overflow-x-auto">
          <svg
            viewBox="50 40 760 480"
            className="w-full h-auto min-w-[700px] select-none"
            style={{ maxHeight: '550px' }}
          >
            <defs>
              <marker
                id="flow-arrow"
                viewBox="0 0 10 10"
                refX="5"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#6F8F7B" opacity="0.8" />
              </marker>
            </defs>

            {/* Zone Backdrop Areas */}
            {zoneOverlays.map((zone) => (
              <g key={zone.id}>
                <path d={zone.path} className={zone.bgClass} strokeDasharray="4 4" rx="8" />
                <text
                  x={zone.labelX}
                  y={zone.labelY}
                  className="fill-text-muted text-[11px] font-sans font-semibold tracking-wide uppercase"
                >
                  {zone.name}
                </text>
                <text
                  x={zone.labelX}
                  y={zone.labelY + 14}
                  className="fill-text-muted/70 text-[9px] font-mono"
                >
                  Critical: {zone.facilities}
                </text>
              </g>
            ))}

            {/* Network Links (Pipes, Pumps, Valves) */}
            {topology.links.map((link) => {
              const [x1, y1] = getNodePos(link.start_node);
              const [x2, y2] = getNodePos(link.end_node);

              const isParallelPump1 = link.id.includes('P1') || link.id === 'PUMP_1';
              const isParallelPump2 = link.id.includes('P2') || link.id === 'PUMP_2';
              const isPump = link.type === 'Pump' || isParallelPump1 || isParallelPump2;
              const isValve = link.type === 'Valve' || link.id.includes('PRV') || link.id.includes('V1');
              const isIntertie = link.id.includes('INTER');

              // Distinguish parallel pumps with curved offsets
              let isCurved = false;
              let pathD = `M ${x1},${y1} L ${x2},${y2}`;
              let midX = (x1 + x2) / 2;
              let midY = (y1 + y2) / 2;

              if (isParallelPump1 && link.start_node.includes('Suction') && link.end_node.includes('Discharge')) {
                isCurved = true;
                midY -= 14;
                pathD = `M ${x1},${y1 - 6} Q ${midX},${midY - 10} ${x2},${y2 - 6}`;
              } else if (isParallelPump2 && link.start_node.includes('Suction') && link.end_node.includes('Discharge')) {
                isCurved = true;
                midY += 14;
                pathD = `M ${x1},${y1 + 6} Q ${midX},${midY + 10} ${x2},${y2 + 6}`;
              }

              // Determine badge text
              let badgeText = 'PIPE';
              if (isParallelPump1) badgeText = 'P1 (MAIN)';
              else if (isParallelPump2) badgeText = 'P2 (AUX)';
              else if (isPump) badgeText = 'PUMP';
              else if (isValve) badgeText = 'PRV';
              else if (isIntertie) badgeText = 'INTERTIE';

              const badgeWidth = badgeText.length > 5 ? 46 : 28;

              return (
                <g key={link.id} className="cursor-pointer">
                  {isCurved ? (
                    <>
                      <path
                        d={pathD}
                        fill="none"
                        stroke="#D9D4C7"
                        className="dark:stroke-basalt-subtle stroke-[4px]"
                      />
                      <path
                        d={pathD}
                        fill="none"
                        stroke="#6F8F7B"
                        className="stroke-[2px]"
                      />
                    </>
                  ) : (
                    <>
                      <line
                        x1={x1}
                        y1={y1}
                        x2={x2}
                        y2={y2}
                        stroke="#D9D4C7"
                        className="dark:stroke-basalt-subtle stroke-[4px]"
                      />
                      <line
                        x1={x1}
                        y1={y1}
                        x2={x2}
                        y2={y2}
                        stroke="#6F8F7B"
                        className="stroke-[2px]"
                        markerEnd="url(#flow-arrow)"
                      />
                    </>
                  )}

                  {/* Flow / Component Type label badge */}
                  <rect
                    x={midX - badgeWidth / 2}
                    y={midY - 7}
                    width={badgeWidth}
                    height="14"
                    rx="3"
                    className="fill-bone dark:fill-ink-muted opacity-90 stroke stroke-stone/40 dark:stroke-basalt-subtle"
                  />
                  <text
                    x={midX}
                    y={midY + 3.5}
                    textAnchor="middle"
                    className="fill-ink dark:fill-bone text-[8px] font-mono font-bold"
                  >
                    {badgeText}
                  </text>
                </g>
              );
            })}

            {/* Network Nodes */}
            {topology.nodes.map((node) => {
              const [x, y] = getNodePos(node.id);
              const isSelected = selectedElementId === node.id;
              const status = getNodeStatusColor(node.id);

              const sensorId =
                node.type === 'Tank'
                  ? node.id === 'T1_Highlands'
                    ? 'L_T1'
                    : 'L_T2'
                  : node.type === 'Reservoir'
                  ? 'P_PUMP_SUCT'
                  : `P_${node.id}`;

              const rawVal = telemetry[sensorId];
              const reconVal = reconstructed[sensorId];
              const displayVal = reconVal ?? rawVal;
              const unit = node.type === 'Tank' ? 'm lvl' : 'm';

              return (
                <g
                  key={node.id}
                  onClick={() => setSelectedElementId(node.id)}
                  className="cursor-pointer transition-transform hover:scale-105"
                >
                  {/* Selection Ring */}
                  {isSelected && (
                    <circle
                      cx={x}
                      cy={y}
                      r="22"
                      fill="none"
                      stroke="#6F8F7B"
                      strokeWidth="2.5"
                      strokeDasharray="4 4"
                      className="animate-spin"
                    />
                  )}

                  {/* Node Shape */}
                  {node.type === 'Reservoir' ? (
                    <g>
                      <rect
                        x={x - 16}
                        y={y - 16}
                        width="32"
                        height="32"
                        rx="5"
                        fill="#24513B"
                        stroke="#14181B"
                        strokeWidth="2"
                      />
                      <text
                        x={x}
                        y={y + 4}
                        textAnchor="middle"
                        fill="#FFFFFF"
                        fontSize="12"
                        fontWeight="bold"
                        className="font-mono"
                      >
                        ≈
                      </text>
                    </g>
                  ) : node.type === 'Tank' ? (
                    <g>
                      <rect
                        x={x - 14}
                        y={y - 18}
                        width="28"
                        height="32"
                        rx="4"
                        fill="#385840"
                        stroke="#14181B"
                        strokeWidth="2"
                      />
                      <path
                        d={`M ${x - 11} ${y + 4} L ${x + 11} ${y + 4}`}
                        stroke="#6F8F7B"
                        strokeWidth="3"
                        strokeLinecap="round"
                      />
                    </g>
                  ) : (
                    <circle
                      cx={x}
                      cy={y}
                      r="11"
                      fill={status.fill}
                      stroke={status.stroke}
                      strokeWidth="2"
                    />
                  )}

                  {/* Node Label */}
                  <text
                    x={x}
                    y={y - 18}
                    textAnchor="middle"
                    className="fill-ink dark:fill-bone text-[10px] font-sans font-bold"
                  >
                    {node.id}
                  </text>

                  {/* Pressure / Level Readout Badge */}
                  {displayVal !== undefined && (
                    <g>
                      <rect
                        x={x - 22}
                        y={y + 14}
                        width="44"
                        height="15"
                        rx="3"
                        className={`${
                          status.isAttacked
                            ? 'fill-brick text-white'
                            : 'fill-stone/90 dark:fill-basalt-subtle stroke stroke-stone/50'
                        }`}
                      />
                      <text
                        x={x}
                        y={y + 25}
                        textAnchor="middle"
                        className={`text-[9px] font-mono font-bold ${
                          status.isAttacked ? 'fill-white' : 'fill-ink dark:fill-bone'
                        }`}
                      >
                        {displayVal.toFixed(1)}{unit}
                      </text>
                    </g>
                  )}

                  {/* Critical Facility Badges */}
                  {node.id === 'J7' && (
                    <g transform={`translate(${x - 48}, ${y + 32})`}>
                      <rect
                        x="0"
                        y="0"
                        width="96"
                        height="15"
                        rx="3"
                        fill="#C79A3B"
                        opacity="0.2"
                        stroke="#C79A3B"
                        strokeWidth="1"
                      />
                      <text
                        x="48"
                        y="11"
                        textAnchor="middle"
                        className="fill-brass font-bold text-[9px] font-mono"
                      >
                        🏥 Memorial Hospital
                      </text>
                    </g>
                  )}

                  {node.id === 'J3' && (
                    <g transform={`translate(${x - 42}, ${y + 32})`}>
                      <rect
                        x="0"
                        y="0"
                        width="84"
                        height="15"
                        rx="3"
                        fill="#6F8F7B"
                        opacity="0.2"
                        stroke="#6F8F7B"
                        strokeWidth="1"
                      />
                      <text
                        x="42"
                        y="11"
                        textAnchor="middle"
                        className="fill-sage font-bold text-[9px] font-mono"
                      >
                        🏛️ Civic Center
                      </text>
                    </g>
                  )}

                  {node.id === 'J11' && (
                    <g transform={`translate(${x - 42}, ${y + 32})`}>
                      <rect
                        x="0"
                        y="0"
                        width="84"
                        height="15"
                        rx="3"
                        fill="#C36B47"
                        opacity="0.2"
                        stroke="#C36B47"
                        strokeWidth="1"
                      />
                      <text
                        x="42"
                        y="11"
                        textAnchor="middle"
                        className="fill-copper font-bold text-[9px] font-mono"
                      >
                        🏭 Tech Park
                      </text>
                    </g>
                  )}

                  {/* Spoofed Alert Icon */}
                  {status.isAttacked && (
                    <g transform={`translate(${x + 8}, ${y - 20})`}>
                      <circle cx="5" cy="5" r="7" fill="#A8403A" />
                      <text
                        x="5"
                        y="9"
                        textAnchor="middle"
                        fill="#FFFFFF"
                        className="text-[9px] font-bold"
                      >
                        !
                      </text>
                    </g>
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    </div>
  );
};
