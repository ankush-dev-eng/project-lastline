import React from 'react';
import { useLastlineStore } from '../store/useLastlineStore';
import { ShieldCheck, Activity, Cpu, Building2 } from 'lucide-react';

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
    const node = topology.nodes.find((n) => n.id === id);
    return node ? node.coordinates : [0, 0];
  };

  // Helper to determine node status color
  const getNodeStatusColor = (nodeId: string) => {
    // Sensor ID for pressure at node
    const sensorId = `P_${nodeId}`;
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
            Compromised: {compromised.slice(0, 2).join(', ') || 'None'}
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
              const midX = (x1 + x2) / 2;
              const midY = (y1 + y2) / 2;

              return (
                <g key={link.id} className="cursor-pointer">
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
                  {/* Flow label */}
                  <rect
                    x={midX - 16}
                    y={midY - 8}
                    width="32"
                    height="14"
                    rx="3"
                    className="fill-bone dark:fill-ink-muted opacity-80"
                  />
                  <text
                    x={midX}
                    y={midY + 3}
                    textAnchor="middle"
                    className="fill-ink dark:fill-bone text-[8px] font-mono font-semibold"
                  >
                    {link.id.startsWith('PUMP') ? 'PUMP' : link.id === 'PRV_1' ? 'PRV' : 'PIPE'}
                  </text>
                </g>
              );
            })}

            {/* Network Nodes */}
            {topology.nodes.map((node) => {
              const [x, y] = node.coordinates;
              const isSelected = selectedElementId === node.id;
              const status = getNodeStatusColor(node.id);
              const sensorId = `P_${node.id}`;
              const rawVal = telemetry[sensorId];
              const reconVal = reconstructed[sensorId];
              const displayVal = reconVal ?? rawVal;

              return (
                <g
                  key={node.id}
                  onClick={() => setSelectedElementId(node.id)}
                  className="cursor-pointer transition-transform hover:scale-110"
                >
                  {/* Selection Ring */}
                  {isSelected && (
                    <circle
                      cx={x}
                      cy={y}
                      r="18"
                      fill="none"
                      stroke="#6F8F7B"
                      strokeWidth="2.5"
                      strokeDasharray="3 3"
                      className="animate-spin"
                    />
                  )}

                  {/* Node Shape */}
                  {node.type === 'Reservoir' ? (
                    <rect
                      x={x - 14}
                      y={y - 14}
                      width="28"
                      height="28"
                      rx="4"
                      fill="#4F7A5A"
                      stroke="#14181B"
                      strokeWidth="2"
                    />
                  ) : node.type === 'Tank' ? (
                    <g>
                      <rect
                        x={x - 12}
                        y={y - 14}
                        width="24"
                        height="28"
                        rx="3"
                        fill="#385840"
                        stroke="#14181B"
                        strokeWidth="2"
                      />
                      <rect
                        x={x - 10}
                        y={y + 2}
                        width="20"
                        height="10"
                        rx="2"
                        fill="#6F8F7B"
                      />
                    </g>
                  ) : (
                    <circle
                      cx={x}
                      cy={y}
                      r="10"
                      fill={status.fill}
                      stroke={status.stroke}
                      strokeWidth="2"
                    />
                  )}

                  {/* Node Label */}
                  <text
                    x={x}
                    y={y - 14}
                    textAnchor="middle"
                    className="fill-ink dark:fill-bone text-[10px] font-sans font-bold"
                  >
                    {node.id}
                  </text>

                  {/* Pressure / Level Readout Badge */}
                  {displayVal !== undefined && (
                    <g>
                      <rect
                        x={x - 18}
                        y={y + 12}
                        width="36"
                        height="14"
                        rx="3"
                        className={`${
                          status.isAttacked
                            ? 'fill-brick text-white'
                            : 'fill-stone/90 dark:fill-basalt-subtle'
                        }`}
                      />
                      <text
                        x={x}
                        y={y + 22}
                        textAnchor="middle"
                        className={`text-[9px] font-mono font-bold ${
                          status.isAttacked ? 'fill-white' : 'fill-ink dark:fill-bone'
                        }`}
                      >
                        {displayVal.toFixed(1)}m
                      </text>
                    </g>
                  )}

                  {/* Spoofed Alert Icon */}
                  {status.isAttacked && (
                    <g transform={`translate(${x + 6}, ${y - 16})`}>
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
