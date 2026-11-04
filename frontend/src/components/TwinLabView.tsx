import React from 'react';
import { useLastlineStore } from '../store/useLastlineStore';
import { Activity } from 'lucide-react';

export const TwinLabView: React.FC = () => {
  const {
    frame,
    selectedSensorId,
    setSelectedSensorId,
  } = useLastlineStore();

  const currentHour = frame.current_hour ?? 8;
  const telemetry = frame.telemetry || {};
  const reconstructed = frame.reconstructed_state || {};
  const uncertainties = frame.uncertainties || {};
  const trust = frame.sensor_trust || {};

  const availableSensors = [
    { id: 'P_J7', label: 'P_J7 (Hospital Junction Pressure)', unit: 'm', type: 'Pressure' },
    { id: 'P_J1', label: 'P_J1 (Highlands Entry Pressure)', unit: 'm', type: 'Pressure' },
    { id: 'P_J5', label: 'P_J5 (Central Zone Inflow Pressure)', unit: 'm', type: 'Pressure' },
    { id: 'P_J6', label: 'P_J6 (Hospital Branch Pressure)', unit: 'm', type: 'Pressure' },
    { id: 'P_J9', label: 'P_J9 (Industrial Entry Pressure)', unit: 'm', type: 'Pressure' },
    { id: 'L_T1', label: 'L_T1 (Highlands Tank Level)', unit: 'm', type: 'Level' },
    { id: 'L_T2', label: 'L_T2 (Eastside Tank Level)', unit: 'm', type: 'Level' },
    { id: 'F_PRV', label: 'F_PRV (Central PRV Flow Rate)', unit: 'L/s', type: 'Flow' },
  ];

  const activeSensor = availableSensors.find((s) => s.id === selectedSensorId) || availableSensors[0];
  const curRaw = telemetry[activeSensor.id] ?? 22.0;
  const curRecon = reconstructed[activeSensor.id] ?? 22.0;
  const curSigma = uncertainties[activeSensor.id] ?? 0.35;
  const curTrust = trust[activeSensor.id] !== undefined ? trust[activeSensor.id] : 1.0;
  const residual = Math.abs(curRaw - curRecon);
  const isSpoofed = curTrust < 0.5;

  // Generate 24-hour synthetic curve for visualization matching the scenario
  const chartPoints = Array.from({ length: 25 }, (_, h) => {
    const diurnal = 22.0 + 3.0 * Math.sin((h / 24) * 2 * Math.PI - Math.PI / 2);
    let raw = diurnal + 0.3 * Math.sin(h * 1.5);
    const recon = diurnal + 0.1 * Math.sin(h * 1.5);

    if (activeSensor.id === 'P_J7' && h >= 8 && h <= 14) {
      raw += 18.2;
    } else if (activeSensor.id === 'L_T1' && h >= 4 && h <= 12) {
      raw += (h - 4) * 0.8;
    }

    return {
      hour: h,
      raw: Number(raw.toFixed(2)),
      recon: Number(recon.toFixed(2)),
      upper: Number((recon + 1.96 * curSigma).toFixed(2)),
      lower: Number((recon - 1.96 * curSigma).toFixed(2)),
    };
  });

  // SVG Chart Dimensions
  const svgWidth = 720;
  const svgHeight = 260;
  const padLeft = 45;
  const padRight = 20;
  const padTop = 25;
  const padBottom = 35;
  const plotWidth = svgWidth - padLeft - padRight;
  const plotHeight = svgHeight - padTop - padBottom;

  const minVal = Math.min(...chartPoints.map((p) => Math.min(p.raw, p.lower))) - 2;
  const maxVal = Math.max(...chartPoints.map((p) => Math.max(p.raw, p.upper))) + 2;

  const scaleX = (h: number) => padLeft + (h / 24) * plotWidth;
  const scaleY = (v: number) => padTop + plotHeight - ((v - minVal) / (maxVal - minVal)) * plotHeight;

  // Construct SVG paths
  const rawPath = chartPoints.reduce(
    (acc, p, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${scaleX(p.hour)} ${scaleY(p.raw)}`,
    ''
  );

  const reconPath = chartPoints.reduce(
    (acc, p, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${scaleX(p.hour)} ${scaleY(p.recon)}`,
    ''
  );

  const upperPoints = chartPoints.map((p) => `${scaleX(p.hour)},${scaleY(p.upper)}`).join(' ');
  const lowerPoints = [...chartPoints].reverse().map((p) => `${scaleX(p.hour)},${scaleY(p.lower)}`).join(' ');
  const ribbonPolygon = `${upperPoints} ${lowerPoints}`;

  const curHourX = scaleX(currentHour);

  return (
    <div className="space-y-4">
      {/* Sensor Selection Bar */}
      <div className="p-4 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt flex flex-wrap items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-sage" />
          <h3 className="font-semibold text-sm text-ink dark:text-bone">
            Telemetry Inspector & Digital Twin State Reconstruction
          </h3>
        </div>

        <div className="flex items-center space-x-2">
          <label htmlFor="sensor-picker" className="text-xs font-mono text-text-muted">
            SELECT INSTRUMENT:
          </label>
          <select
            id="sensor-picker"
            value={activeSensor.id}
            onChange={(e) => setSelectedSensorId(e.target.value)}
            className="bg-bone dark:bg-ink-muted border border-stone dark:border-basalt-subtle px-3 py-1 rounded text-ink dark:text-bone text-xs font-mono focus:outline-hidden focus:ring-1 focus:ring-sage"
          >
            {availableSensors.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Dual-Series SVG Chart */}
      <div className="p-4 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt space-y-3 shadow-xs">
        <div className="flex flex-wrap items-center justify-between text-xs font-mono gap-2 border-b border-stone/30 dark:border-basalt-subtle pb-2">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-0.5 bg-brick inline-block" />
              <span className="text-text-muted">Raw Measured SCADA</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-1 bg-sage inline-block" />
              <span className="font-semibold text-ink dark:text-bone">Reconstructed Physics State</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-2 bg-sage/20 border border-sage/40 inline-block rounded-xs" />
              <span className="text-text-muted">±1.96σ Bayesian Uncertainty Band</span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-text-muted">STATUS:</span>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                isSpoofed ? 'bg-brick text-white' : 'bg-moss text-white'
              }`}
            >
              {isSpoofed ? 'CYBER SPOOFING DETECTED' : 'PHYSICALLY VALIDATED'}
            </span>
          </div>
        </div>

        {/* Chart Viewbox */}
        <div className="w-full overflow-x-auto">
          <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto min-w-[620px] select-none">
            {/* Grid lines */}
            {[0, 6, 12, 18, 24].map((h) => (
              <g key={h}>
                <line
                  x1={scaleX(h)}
                  y1={padTop}
                  x2={scaleX(h)}
                  y2={padTop + plotHeight}
                  stroke="#D9D4C7"
                  className="dark:stroke-basalt-subtle"
                  strokeDasharray="2 2"
                />
                <text
                  x={scaleX(h)}
                  y={padTop + plotHeight + 16}
                  textAnchor="middle"
                  className="fill-text-muted text-[10px] font-mono"
                >
                  T+{h.toString().padStart(2, '0')}h
                </text>
              </g>
            ))}

            {/* Y axis labels */}
            {[minVal, (minVal + maxVal) / 2, maxVal].map((v, i) => (
              <g key={i}>
                <line
                  x1={padLeft}
                  y1={scaleY(v)}
                  x2={padLeft + plotWidth}
                  y2={scaleY(v)}
                  stroke="#D9D4C7"
                  className="dark:stroke-basalt-subtle"
                  strokeDasharray="2 2"
                />
                <text
                  x={padLeft - 8}
                  y={scaleY(v) + 3}
                  textAnchor="end"
                  className="fill-text-muted text-[10px] font-mono"
                >
                  {v.toFixed(0)}m
                </text>
              </g>
            ))}

            {/* Shaded Uncertainty Ribbon */}
            <polygon points={ribbonPolygon} fill="#6F8F7B" opacity="0.18" />

            {/* Reconstructed State Line */}
            <path d={reconPath} fill="none" stroke="#6F8F7B" strokeWidth="2.5" />

            {/* Raw Telemetry Line */}
            <path
              d={rawPath}
              fill="none"
              stroke="#A8403A"
              strokeWidth="2"
              strokeDasharray={isSpoofed ? '4 2' : 'none'}
            />

            {/* Current Simulation Hour Vertical Indicator */}
            <line
              x1={curHourX}
              y1={padTop}
              x2={curHourX}
              y2={padTop + plotHeight}
              stroke="#14181B"
              className="dark:stroke-bone stroke-[2px]"
            />
            <circle
              cx={curHourX}
              cy={scaleY(curRecon)}
              r="4"
              fill="#6F8F7B"
              stroke="#FFFFFF"
              strokeWidth="1.5"
            />
            <circle
              cx={curHourX}
              cy={scaleY(curRaw)}
              r="4"
              fill="#A8403A"
              stroke="#FFFFFF"
              strokeWidth="1.5"
            />
          </svg>
        </div>
      </div>

      {/* Numerical Evidence & Statistical Residuals Table */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="p-3 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt">
          <span className="text-[10px] text-text-muted font-mono block">RAW SCADA READING</span>
          <div className="text-xl font-bold font-telemetry text-brick">
            {curRaw.toFixed(2)} {activeSensor.unit}
          </div>
          <span className="text-[10px] text-text-muted font-mono">
            {isSpoofed ? '+18.2m spoofed bias' : 'Diurnal envelope normal'}
          </span>
        </div>

        <div className="p-3 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt">
          <span className="text-[10px] text-text-muted font-mono block">RECONSTRUCTED (WLS)</span>
          <div className="text-xl font-bold font-telemetry text-sage">
            {curRecon.toFixed(2)} {activeSensor.unit}
          </div>
          <span className="text-[10px] text-text-muted font-mono">
            ± {(curSigma * 1.96).toFixed(2)} {activeSensor.unit} (95% CI)
          </span>
        </div>

        <div className="p-3 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt">
          <span className="text-[10px] text-text-muted font-mono block">PHYSICAL RESIDUAL |Δ|</span>
          <div className="text-xl font-bold font-telemetry text-ink dark:text-bone">
            {residual.toFixed(2)} {activeSensor.unit}
          </div>
          <span className="text-[10px] text-text-muted font-mono">
            Threshold: 3.50 {activeSensor.unit}
          </span>
        </div>

        <div className="p-3 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt">
          <span className="text-[10px] text-text-muted font-mono block">SENSOR TRUST WEIGHT</span>
          <div className={`text-xl font-bold font-telemetry ${curTrust < 0.5 ? 'text-brick' : 'text-moss'}`}>
            {(curTrust * 100).toFixed(1)}%
          </div>
          <span className="text-[10px] text-text-muted font-mono">
            {curTrust < 0.5 ? 'Weight discounted to 0.0' : 'Full observation fidelity'}
          </span>
        </div>
      </div>
    </div>
  );
};
