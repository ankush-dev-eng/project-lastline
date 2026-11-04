import React from 'react';
import { useLastlineStore } from '../store/useLastlineStore';
import { X, ArrowRight } from 'lucide-react';

export const NodeInspectorDrawer: React.FC = () => {
  const {
    selectedElementId,
    setSelectedElementId,
    topology,
    frame,
    setActiveView,
    setSelectedSensorId,
  } = useLastlineStore();

  if (!selectedElementId) return null;

  const node = topology.nodes.find((n) => n.id === selectedElementId);
  const sensorId = `P_${selectedElementId}`;
  const rawValue = frame.telemetry?.[sensorId];
  const reconValue = frame.reconstructed_state?.[sensorId];
  const uncertainty = frame.uncertainties?.[sensorId] ?? 0.35;
  const trustScore = frame.sensor_trust?.[sensorId] !== undefined ? frame.sensor_trust[sensorId] : 1.0;
  const isCompromised = trustScore < 0.5;

  // Find Zone for this node
  const zone = topology.zones.find((z) => z.nodes.includes(selectedElementId));

  // Determine connected PLC based on node location
  const getPlcId = (id: string) => {
    if (['J1', 'J2', 'J3', 'J4', 'T1_Highlands'].includes(id)) return 'PLC_1 (North Highlands)';
    if (['J_PRV_Inlet', 'J5', 'J6', 'J7', 'J8'].includes(id)) return 'PLC_2 (Central Commercial)';
    if (['J9', 'J10', 'J11', 'J12', 'T2_Eastside'].includes(id)) return 'PLC_3 (Eastside Industrial)';
    return 'PLC_4 (Clearwell & Main Station)';
  };

  const plcName = getPlcId(selectedElementId);

  const handleOpenInLab = () => {
    setSelectedSensorId(sensorId);
    setActiveView('TWIN_LAB');
  };

  return (
    <div className="p-4 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt space-y-4 shadow-sm animate-in fade-in duration-200">
      <div className="flex items-center justify-between border-b border-stone/50 dark:border-basalt-subtle pb-2.5">
        <div className="flex items-center space-x-2">
          <span className="font-bold text-sm text-ink dark:text-bone font-mono">
            ELEMENT INSPECTOR: {selectedElementId}
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-stone/40 dark:bg-basalt-subtle text-ink dark:text-bone">
            {node?.type ?? 'Node'}
          </span>
        </div>
        <button
          onClick={() => setSelectedElementId(null)}
          className="p-1 rounded hover:bg-stone/30 dark:hover:bg-basalt-subtle text-text-muted hover:text-ink dark:hover:text-bone"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Basic Metadata */}
      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="bg-bone dark:bg-ink-muted/50 p-2 rounded border border-stone/40 dark:border-basalt-subtle">
          <span className="text-text-muted block text-[10px]">ELEVATION</span>
          <span className="font-bold font-telemetry">{node?.elevation_m ?? 0.0} m</span>
        </div>
        <div className="bg-bone dark:bg-ink-muted/50 p-2 rounded border border-stone/40 dark:border-basalt-subtle">
          <span className="text-text-muted block text-[10px]">ZONE</span>
          <span className="font-bold truncate block">{zone?.name ?? 'Verdant Core'}</span>
        </div>
        <div className="col-span-2 bg-bone dark:bg-ink-muted/50 p-2 rounded border border-stone/40 dark:border-basalt-subtle">
          <span className="text-text-muted block text-[10px]">CONTROLLING PLC</span>
          <span className="font-bold">{plcName}</span>
        </div>
      </div>

      {/* Telemetry vs Physics Reconstruction Comparison */}
      <div className="p-3 rounded border border-stone dark:border-basalt-subtle bg-bone/30 dark:bg-ink/40 space-y-2.5">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-text-muted">STATE ESTIMATION (HEAD)</span>
          <span
            className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
              isCompromised ? 'bg-brick text-white' : 'bg-moss text-white'
            }`}
          >
            {isCompromised ? 'SPOOFING DETECTED' : 'TRUSTED'}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="p-2 rounded bg-white dark:bg-basalt border border-stone dark:border-basalt-subtle">
            <span className="text-[10px] text-text-muted block font-mono">RAW SCADA</span>
            <div className={`text-lg font-bold font-telemetry ${isCompromised ? 'text-brick' : 'text-ink dark:text-bone'}`}>
              {rawValue !== undefined ? `${rawValue.toFixed(2)}m` : 'N/A'}
            </div>
            {isCompromised && (
              <span className="text-[10px] text-brick font-mono font-semibold">ATTACK INJECTED</span>
            )}
          </div>

          <div className="p-2 rounded bg-white dark:bg-basalt border border-stone dark:border-basalt-subtle">
            <span className="text-[10px] text-text-muted block font-mono">RECONSTRUCTED (WLS)</span>
            <div className="text-lg font-bold font-telemetry text-sage">
              {reconValue !== undefined ? `${reconValue.toFixed(2)}m` : 'N/A'}
            </div>
            <span className="text-[10px] text-text-muted font-mono">
              ± {(uncertainty * 1.96).toFixed(2)}m (95% CI)
            </span>
          </div>
        </div>

        {/* Trust Gauge */}
        <div className="space-y-1">
          <div className="flex justify-between text-[11px] font-mono">
            <span className="text-text-muted">Sensor Telemetry Trust:</span>
            <span className={`font-bold ${trustScore < 0.5 ? 'text-brick' : 'text-moss'}`}>
              {(trustScore * 100).toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-stone dark:bg-basalt-subtle rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                trustScore < 0.5 ? 'bg-brick' : 'bg-moss'
              }`}
              style={{ width: `${Math.max(5, trustScore * 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Action to View in Twin Lab */}
      <button
        onClick={handleOpenInLab}
        className="w-full py-1.5 px-3 rounded text-xs font-semibold bg-stone/40 dark:bg-basalt-subtle hover:bg-stone dark:hover:bg-basalt text-ink dark:text-bone flex items-center justify-center space-x-1.5 transition-colors"
      >
        <span>Inspect Dual-Series Curve in Digital Twin Lab</span>
        <ArrowRight className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
