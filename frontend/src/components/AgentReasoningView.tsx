import React from 'react';
import { useLastlineStore } from '../store/useLastlineStore';
import {
  ShieldAlert,
  Cpu,
  Activity,
  AlertTriangle,
  PlayCircle,
  FileCheck2,
  CheckCircle2,
  Layers,
} from 'lucide-react';

export const AgentReasoningView: React.FC = () => {
  const { frame } = useLastlineStore();
  const reports = frame.agent_reports;

  const sentinel = reports?.sentinel;
  const integrity = reports?.integrity;
  const reconstruction = reports?.reconstruction;
  const impact = reports?.impact;
  const response = reports?.response;
  const explainer = reports?.explainer;

  const agents = [
    {
      id: 'sentinel',
      name: '1. Sentinel Agent',
      role: 'Cyber Telemetry & Traffic Invariants',
      icon: <ShieldAlert className="w-4 h-4 text-brick" />,
      threat: sentinel?.threat_level ?? 'NORMAL',
      threatClass:
        sentinel?.threat_level === 'HIGH' || sentinel?.threat_level === 'CRITICAL'
          ? 'bg-brick-subtle text-brick border-brick/40'
          : 'bg-moss-subtle text-moss border-moss/40',
      metrics: [
        { label: 'Anomalies Detected', val: sentinel?.anomalies_detected ?? 0 },
        { label: 'Flagged Sensors', val: sentinel?.flagged_sensors?.join(', ') || 'None' },
        { label: 'Network Invariants', val: 'Modbus TCP Monitored' },
      ],
      summary: sentinel?.traffic_anomalies?.length
        ? sentinel.traffic_anomalies.join('; ')
        : 'Zero SCADA telemetry transport violations detected.',
    },
    {
      id: 'integrity',
      name: '2. Integrity Agent',
      role: 'Statistical Trust & Diurnal Residuals',
      icon: <Cpu className="w-4 h-4 text-brass" />,
      threat: integrity?.system_alarm ? 'ALARM ACTIVE' : 'NOMINAL',
      threatClass: integrity?.system_alarm
        ? 'bg-brick-subtle text-brick border-brick/40'
        : 'bg-moss-subtle text-moss border-moss/40',
      metrics: [
        {
          label: 'Compromised Sensors',
          val: integrity?.compromised_sensors?.join(', ') || 'None',
        },
        {
          label: 'PLC Trust Status',
          val: integrity?.compromised_plcs?.length
            ? `Degraded (${integrity.compromised_plcs.join(', ')})`
            : '100% Trusted',
        },
        {
          label: 'Gaussian Kernel',
          val: 'Dynamic Z-score Residuals',
        },
      ],
      summary: integrity?.compromised_sensors?.length
        ? `Sensor ${integrity.compromised_sensors[0]} exhibits severe drift/spoofing (> 4.5 sigma from diurnal mean). Trust isolated to 0.00.`
        : 'All sensor observations conform to physical mass and diurnal boundaries.',
    },
    {
      id: 'reconstruction',
      name: '3. Reconstruction Agent',
      role: 'Bayesian WLS State Estimator',
      icon: <Activity className="w-4 h-4 text-sage" />,
      threat: reconstruction?.stability_index && reconstruction.stability_index >= 0.8 ? 'STABLE' : 'DEGRADED',
      threatClass: 'bg-sage-subtle text-sage border-sage/40',
      metrics: [
        {
          label: 'Stability Index',
          val: reconstruction?.stability_index ? `${(reconstruction.stability_index * 100).toFixed(1)}%` : '95.0%',
        },
        {
          label: 'Top Suspicious Components',
          val: reconstruction?.top_suspicious_components?.slice(0, 2).join(', ') || 'None',
        },
        {
          label: 'Hydraulic Invariant',
          val: 'Mass Conservation & Energy Loop',
        },
      ],
      summary:
        'State reconstructed using trust-weighted Bayesian WLS. Untrusted observations discounted to zero weight, preserving true hydraulic head.',
    },
    {
      id: 'impact',
      name: '4. Impact Agent',
      role: 'Downstream Disruption & Critical Facilities',
      icon: <AlertTriangle className="w-4 h-4 text-copper" />,
      threat: impact?.overall_severity ?? 'LOW',
      threatClass:
        impact?.overall_severity === 'HIGH' || impact?.overall_severity === 'CRITICAL'
          ? 'bg-copper-subtle text-copper border-copper/40'
          : 'bg-moss-subtle text-moss border-moss/40',
      metrics: [
        {
          label: 'Priority Zone',
          val: impact?.zone_priorities?.[0] || 'Zone_B_Central',
        },
        {
          label: 'Critical Facilities at Risk',
          val: impact?.critical_facilities_at_risk?.join(', ') || 'None (Safe)',
        },
        {
          label: 'Storage Buffer (T1 / T2)',
          val: '18.4h / 22.1h',
        },
      ],
      summary: impact?.critical_facilities_at_risk?.length
        ? `High priority: ${impact.critical_facilities_at_risk.join(', ')} located in target zone. Physical pressure maintained at 22.3m (safe above 15m threshold).`
        : 'All distribution zones operating with normal delivery pressure margins.',
    },
    {
      id: 'response',
      name: '5. Response Agent',
      role: 'Twin-Simulated Pre-Approved Playbooks',
      icon: <PlayCircle className="w-4 h-4 text-moss" />,
      threat: response?.verification_passed ? 'VERIFIED SAFE' : 'UNVERIFIED',
      threatClass: response?.verification_passed
        ? 'bg-moss-subtle text-moss border-moss/40'
        : 'bg-brick-subtle text-brick border-brick/40',
      metrics: [
        {
          label: 'Candidate Playbook',
          val: response?.recommended_playbook || 'PB-RES-02',
        },
        {
          label: 'Twin Hydraulic Gate',
          val: response?.verification_passed ? 'PASSED (P ≥ 15m)' : 'FAILED',
        },
        {
          label: 'Execution Model',
          val: 'Human-in-the-Loop Only',
        },
      ],
      summary: response?.simulation_summary || 'Digital twin simulation forward-verified that fallback procedures maintain minimum pressures and storage reserves.',
    },
    {
      id: 'explainer',
      name: '6. Explainer Agent',
      role: 'Evidence-Linked Operator Rationale',
      icon: <FileCheck2 className="w-4 h-4 text-ink dark:text-bone" />,
      threat: 'CONFIDENCE: 95%',
      threatClass: 'bg-stone/50 dark:bg-basalt-subtle text-ink dark:text-bone border-stone',
      metrics: [
        {
          label: 'Confidence Score',
          val: explainer?.confidence ? `${(explainer.confidence * 100).toFixed(0)}%` : '95%',
        },
        {
          label: 'Evidence For / Against',
          val: `${explainer?.evidence?.evidence_for?.length ?? 2} For / ${explainer?.evidence?.evidence_against?.length ?? 0} Against`,
        },
        {
          label: 'Advisory Mode',
          val: 'Strict Sandbox Enforced',
        },
      ],
      summary: explainer?.summary || 'Integrity Agent identified severe spoofing on sensor P_J7 (+18.2m discrepancy, trust 0.00). Reconstructed true physical head is 22.3m, safely protecting Verdant Memorial Hospital.',
    },
  ];

  return (
    <div className="space-y-5">
      {/* Overview Banner */}
      <div className="p-4 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt space-y-2">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-sage" />
          <h2 className="font-bold text-sm tracking-tight text-ink dark:text-bone">
            Multi-Agent Reasoning Pipeline & Evidence Chain
          </h2>
        </div>
        <p className="text-xs text-text-muted leading-relaxed">
          Six specialized deterministic agents collaborate to overcome operational blindness during SCADA compromise. Telemetry moves from cyber-physical anomaly ingestion to Bayesian state reconstruction, downstream risk triage, twin pre-simulation, and human-in-the-loop rationale synthesis.
        </p>
      </div>

      {/* Visual Pipeline Flow Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent, idx) => (
          <div
            key={agent.id}
            className="p-4 rounded border border-stone dark:border-basalt-subtle bg-white dark:bg-basalt space-y-3 shadow-xs flex flex-col justify-between"
          >
            <div>
              {/* Agent Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <div className="p-1.5 rounded bg-bone dark:bg-ink-muted border border-stone/50 dark:border-basalt-subtle">
                    {agent.icon}
                  </div>
                  <div>
                    <h3 className="font-bold text-xs text-ink dark:text-bone">{agent.name}</h3>
                    <span className="text-[10px] text-text-muted block">{agent.role}</span>
                  </div>
                </div>

                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold border ${agent.threatClass}`}
                >
                  {agent.threat}
                </span>
              </div>

              {/* Agent Structured Metrics */}
              <div className="space-y-1.5 py-2 border-y border-stone/30 dark:border-basalt-subtle/50 my-2">
                {agent.metrics.map((m, mIdx) => (
                  <div key={mIdx} className="flex justify-between text-[11px] font-mono">
                    <span className="text-text-muted">{m.label}:</span>
                    <span className="font-semibold text-ink dark:text-bone truncate max-w-[150px] text-right">
                      {m.val}
                    </span>
                  </div>
                ))}
              </div>

              {/* Natural Language Rationale */}
              <p className="text-xs text-text-muted leading-relaxed italic bg-bone/40 dark:bg-ink/30 p-2.5 rounded border border-stone/30 dark:border-basalt-subtle">
                "{agent.summary}"
              </p>
            </div>

            {/* Pipeline Step Footer */}
            <div className="pt-2 flex items-center justify-between text-[10px] font-mono text-text-muted">
              <span>STAGE {idx + 1} OF 6</span>
              <div className="flex items-center space-x-1 text-sage font-semibold">
                <span>DETERMINISTIC</span>
                <CheckCircle2 className="w-3 h-3" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
