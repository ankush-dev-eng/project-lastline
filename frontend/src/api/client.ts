/**
 * PROJECT LASTLINE: API Client & Resilient Fallback Data Provider.
 * 
 * Provides typed HTTP communication with the LASTLINE FastAPI backend.
 * Falls back to high-fidelity municipal water digital twin simulation frames
 * when running offline or in unit-test environments.
 */

import type {
  HealthResponse,
  NetworkTopology,
  SensorMeta,
  ScenarioMeta,
  SystemStateFrame,
  AgentReports,
  VerifiedRecommendation,
  ActionApprovalRequest,
  AuditLogResponse,
  ReplayStatus,
} from '../types';

const BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) || (import.meta.env?.MODE === 'test' ? 'http://localhost:59999/api' : 'http://localhost:8899/api');

// Realistic Fallback Topology matching Verdant City Water System
export const MOCK_TOPOLOGY: NetworkTopology = {
  network_name: 'Verdant City Municipal Water System',
  nodes: [
    { id: 'R0_Clearwell', type: 'Reservoir', elevation_m: 15.0, coordinates: [100, 300] },
    { id: 'J0_PumpSuction', type: 'Junction', elevation_m: 14.5, coordinates: [200, 300] },
    { id: 'J1', type: 'Junction', elevation_m: 26.0, coordinates: [320, 160] },
    { id: 'J2', type: 'Junction', elevation_m: 28.0, coordinates: [420, 140] },
    { id: 'J3', type: 'Junction', elevation_m: 30.0, coordinates: [520, 120] },
    { id: 'J4', type: 'Junction', elevation_m: 27.0, coordinates: [600, 160] },
    { id: 'T1_Highlands', type: 'Tank', elevation_m: 35.0, coordinates: [680, 140] },
    { id: 'J_PRV_Inlet', type: 'Junction', elevation_m: 20.0, coordinates: [320, 300] },
    { id: 'J5', type: 'Junction', elevation_m: 18.0, coordinates: [420, 300] },
    { id: 'J6', type: 'Junction', elevation_m: 17.5, coordinates: [520, 290] },
    { id: 'J7', type: 'Junction', elevation_m: 16.0, coordinates: [520, 340] },
    { id: 'J8', type: 'Junction', elevation_m: 17.0, coordinates: [600, 300] },
    { id: 'J9', type: 'Junction', elevation_m: 14.0, coordinates: [380, 440] },
    { id: 'J10', type: 'Junction', elevation_m: 12.0, coordinates: [480, 440] },
    { id: 'J11', type: 'Junction', elevation_m: 11.0, coordinates: [580, 440] },
    { id: 'J12', type: 'Junction', elevation_m: 10.5, coordinates: [680, 440] },
    { id: 'T2_Eastside', type: 'Tank', elevation_m: 22.0, coordinates: [750, 440] },
  ],
  links: [
    { id: 'PIPE_SUCTION', type: 'Pipe', start_node: 'R0_Clearwell', end_node: 'J0_PumpSuction', length_m: 100, diameter_m: 0.6 },
    { id: 'PUMP_1', type: 'Pump', start_node: 'J0_PumpSuction', end_node: 'J1', length_m: 10, diameter_m: 0.4 },
    { id: 'PUMP_2', type: 'Pump', start_node: 'J0_PumpSuction', end_node: 'J_PRV_Inlet', length_m: 10, diameter_m: 0.4 },
    { id: 'P_J1_J2', type: 'Pipe', start_node: 'J1', end_node: 'J2', length_m: 600, diameter_m: 0.35 },
    { id: 'P_J2_J3', type: 'Pipe', start_node: 'J2', end_node: 'J3', length_m: 550, diameter_m: 0.3 },
    { id: 'P_J3_J4', type: 'Pipe', start_node: 'J3', end_node: 'J4', length_m: 500, diameter_m: 0.3 },
    { id: 'P_J4_T1', type: 'Pipe', start_node: 'J4', end_node: 'T1_Highlands', length_m: 400, diameter_m: 0.3 },
    { id: 'PRV_1', type: 'Valve', start_node: 'J_PRV_Inlet', end_node: 'J5', length_m: 10, diameter_m: 0.4 },
    { id: 'P_J5_J6', type: 'Pipe', start_node: 'J5', end_node: 'J6', length_m: 500, diameter_m: 0.35 },
    { id: 'P_J6_J7', type: 'Pipe', start_node: 'J6', end_node: 'J7', length_m: 450, diameter_m: 0.3 },
    { id: 'P_J6_J8', type: 'Pipe', start_node: 'J6', end_node: 'J8', length_m: 500, diameter_m: 0.3 },
    { id: 'P_J5_J9', type: 'Pipe', start_node: 'J5', end_node: 'J9', length_m: 700, diameter_m: 0.4 },
    { id: 'P_J9_J10', type: 'Pipe', start_node: 'J9', end_node: 'J10', length_m: 600, diameter_m: 0.35 },
    { id: 'P_J10_J11', type: 'Pipe', start_node: 'J10', end_node: 'J11', length_m: 550, diameter_m: 0.3 },
    { id: 'P_J11_J12', type: 'Pipe', start_node: 'J11', end_node: 'J12', length_m: 500, diameter_m: 0.3 },
    { id: 'P_J12_T2', type: 'Pipe', start_node: 'J12', end_node: 'T2_Eastside', length_m: 400, diameter_m: 0.3 },
  ],
  zones: [
    {
      zone_id: 'Zone_A_North',
      name: 'North Highlands Residential',
      elevation_range: '25 - 32m',
      nodes: ['J1', 'J2', 'J3', 'J4', 'T1_Highlands'],
      critical_facilities: ['North Highlands Civic Center'],
    },
    {
      zone_id: 'Zone_B_Central',
      name: 'Central Commercial & Civic',
      elevation_range: '15 - 20m',
      nodes: ['J_PRV_Inlet', 'J5', 'J6', 'J7', 'J8'],
      critical_facilities: ['Verdant Memorial Hospital'],
    },
    {
      zone_id: 'Zone_C_Industrial',
      name: 'Eastside Industrial & Tech Center',
      elevation_range: '10 - 15m',
      nodes: ['J9', 'J10', 'J11', 'J12', 'T2_Eastside'],
      critical_facilities: ['Eastside High-Tech Industrial Park'],
    },
  ],
};

export const MOCK_SCENARIOS: ScenarioMeta[] = [
  {
    scenario_id: 'SCENARIO_01_SENSOR_BIAS',
    name: 'Attack 01: Severe Sensor Bias Injection (+18m)',
    description: 'Attack injected constant positive pressure bias into Hospital Junction J7 telemetry.',
    attack_type: 'SENSOR_BIAS',
    target_components: ['P_J7'],
    target_plc: 'PLC_2',
    start_hour: 8,
    duration_hours: 6,
  },
  {
    scenario_id: 'SCENARIO_02_SENSOR_DRIFT',
    name: 'Attack 02: Stealthy Sensor Drift (+0.8m/hr)',
    description: 'Ramping pressure spoofing on T1 tank inlet sensor.',
    attack_type: 'SENSOR_DRIFT',
    target_components: ['L_T1'],
    target_plc: 'PLC_1',
    start_hour: 4,
    duration_hours: 8,
  },
  {
    scenario_id: 'SCENARIO_04_REPLAY_ATTACK',
    name: 'Attack 04: Industrial SCADA Telemetry Replay',
    description: 'Stale night-time telemetry replayed during peak morning commercial demand.',
    attack_type: 'REPLAY_ATTACK',
    target_components: ['P_J5', 'P_J6', 'P_J7', 'P_J8'],
    target_plc: 'PLC_2',
    start_hour: 7,
    duration_hours: 5,
  },
  {
    scenario_id: 'SCENARIO_05_PLC_TAMPERING',
    name: 'Attack 05: PLC-2 Pressure Setpoint Tampering',
    description: 'Malicious modification of PRV-1 downstream setpoint parameter.',
    attack_type: 'PLC_SETPOINT_TAMPERING',
    target_components: ['PRV_1'],
    target_plc: 'PLC_2',
    start_hour: 10,
    duration_hours: 4,
  },
];

export const MOCK_FRAME: SystemStateFrame = {
  timestamp: 28800.0,
  current_hour: 8,
  max_hours: 24,
  scenario_id: 'SCENARIO_01_SENSOR_BIAS',
  is_playing: false,
  speed: 1.0,
  telemetry: {
    P_J1: 27.4,
    P_J2: 26.8,
    P_J3: 25.1,
    P_J4: 24.3,
    P_J5: 23.2,
    P_J6: 22.5,
    P_J7: 40.5,
    P_J8: 22.1,
    P_J9: 21.0,
    P_J10: 20.4,
    P_J11: 19.8,
    P_J12: 19.2,
    L_T1: 4.8,
    L_T2: 5.2,
    F_P1: 45.0,
    F_P2: 55.0,
    F_PRV: 52.0,
  },
  reconstructed_state: {
    P_J1: 27.2,
    P_J2: 26.7,
    P_J3: 25.0,
    P_J4: 24.2,
    P_J5: 23.1,
    P_J6: 22.4,
    P_J7: 22.3,
    P_J8: 22.0,
    P_J9: 20.9,
    P_J10: 20.3,
    P_J11: 19.7,
    P_J12: 19.1,
    L_T1: 4.82,
    L_T2: 5.18,
  },
  uncertainties: {
    P_J1: 0.35,
    P_J2: 0.38,
    P_J3: 0.40,
    P_J4: 0.42,
    P_J5: 0.36,
    P_J6: 0.39,
    P_J7: 0.44,
    P_J8: 0.38,
    P_J9: 0.41,
    P_J10: 0.42,
    P_J11: 0.45,
    P_J12: 0.46,
    L_T1: 0.12,
    L_T2: 0.14,
  },
  sensor_trust: {
    P_J1: 0.99,
    P_J2: 0.98,
    P_J3: 0.99,
    P_J4: 0.97,
    P_J5: 0.95,
    P_J6: 0.94,
    P_J7: 0.00,
    P_J8: 0.96,
    P_J9: 0.98,
    P_J10: 0.97,
    P_J11: 0.99,
    P_J12: 0.98,
    L_T1: 0.99,
    L_T2: 0.99,
    F_P1: 0.98,
    F_P2: 0.97,
    F_PRV: 0.96,
  },
  plc_trust: {
    PLC_1: 0.98,
    PLC_2: 0.52,
    PLC_3: 0.97,
    PLC_4: 0.98,
  },
  system_alarm: true,
  stability_index: 0.88,
  top_suspicious: ['P_J7', 'PLC_2', 'PRV_1'],
  zone_priorities: ['Zone_B_Central', 'Zone_A_North', 'Zone_C_Industrial'],
  critical_facilities_at_risk: ['Verdant Memorial Hospital'],
  pressure_deficits_m: { J7: 0.0 },
  tanks_time_to_empty_hours: { T1_Highlands: 18.4, T2_Eastside: 22.1 },
  recommendations: [
    {
      recommendation_id: 'REC-PB-RES-02-001',
      playbook_id: 'PB-RES-02',
      title: 'Zone B Telemetry Quarantine & Hospital Pressure Verification',
      description: 'Quarantine telemetry from sensor P_J7 on PLC_2. Rely on Bayesian WLS reconstructed pressure estimates and inspect physical pressure at Verdant Memorial Hospital.',
      target_zone: 'Zone_B_Central',
      target_components: ['P_J7', 'PLC_2'],
      recommended_actions: [
        'Isolate telemetry channel P_J7 at SCADA gateway',
        'Switch control logic to physical state reconstruction feed',
        'Dispatch field team to Verdant Memorial Hospital gauge junction J7',
      ],
      evidence: {
        evidence_for: [
          'Statistical residual on P_J7 exceeds 18.2m head (> 4.5 sigma from diurnal mean)',
          'Physical mass conservation rejects raw reading under current pump discharge',
          'Adjacent sensors P_J5 and P_J6 report nominal 22.4m head',
        ],
        evidence_against: [
          'No upstream pipe burst telemetry alarms registered',
          'PRV-1 inlet pressure steady at 23.1m',
        ],
        assumptions: [
          'PRV-1 mechanical bypass valve remains operable',
          'Hospital emergency header check valve functional',
        ],
      },
      confidence_score: 0.96,
      simulation_proof: {
        simulation_id: 'SIM-PB-RES-02-771',
        playbook_id: 'PB-RES-02',
        duration_hours: 4,
        is_hydraulically_safe: true,
        minimum_pressure_m: 21.8,
        critical_nodes_failing: [],
        minimum_tank_levels: { T1_Highlands: 4.5, T2_Eastside: 4.9 },
        tanks_overflowing: [],
        tanks_depleted: [],
        simulation_duration_ms: 112,
      },
      advisory_notice: 'SANDBOX ADVISORY: Verified safe in EPANET digital twin simulation. Requires human confirmation.',
      requires_human_approval: true,
      approval_status: 'PENDING',
    },
  ],
  explainer_summary: 'Integrity Agent identified severe spoofing on sensor P_J7 (+18.2m discrepancy, trust 0.00). Reconstructed true physical head is 22.3m, safely protecting Verdant Memorial Hospital. Playbook PB-RES-02 is verified safe by twin simulation.',
  evidence: {
    evidence_for: [
      'P_J7 reading 40.5m exceeds max physical boundary',
      'Hydraulic WLS confirms physical state at 22.3m',
    ],
    evidence_against: [],
    assumptions: ['Network boundary elevations are constant'],
  },
  confidence: 0.95,
  agent_reports: {
    sentinel: {
      agent: 'SENTINEL',
      timestamp: 28800.0,
      anomalies_detected: 1,
      flagged_sensors: ['P_J7'],
      traffic_anomalies: ['SCADA Modbus frame deviation on PLC_2'],
      threat_level: 'HIGH',
    },
    integrity: {
      agent: 'INTEGRITY',
      timestamp: 28800.0,
      sensor_trust: { P_J7: 0.0, P_J1: 0.99, P_J5: 0.95 },
      plc_trust: { PLC_1: 0.98, PLC_2: 0.52, PLC_3: 0.97, PLC_4: 0.98 },
      compromised_sensors: ['P_J7'],
      compromised_plcs: ['PLC_2'],
      system_alarm: true,
    },
    reconstruction: {
      agent: 'RECONSTRUCTION',
      timestamp: 28800.0,
      state_estimates: { P_J7: 22.3, P_J1: 27.2 },
      uncertainties: { P_J7: 0.44, P_J1: 0.35 },
      stability_index: 0.88,
      top_suspicious_components: ['P_J7', 'PLC_2', 'PRV_1'],
    },
    impact: {
      agent: 'IMPACT',
      timestamp: 28800.0,
      overall_severity: 'HIGH',
      zone_priorities: ['Zone_B_Central', 'Zone_A_North', 'Zone_C_Industrial'],
      critical_facilities_at_risk: ['Verdant Memorial Hospital'],
      pressure_deficits_m: { J7: 0.0 },
      tanks_time_to_empty_hours: { T1_Highlands: 18.4, T2_Eastside: 22.1 },
    },
    response: {
      agent: 'RESPONSE',
      timestamp: 28800.0,
      recommended_playbook: 'PB-RES-02',
      actions: ['Quarantine P_J7', 'Engage WLS state feedback', 'Verify Hospital Gauge'],
      verification_passed: true,
      simulation_summary: 'Minimum pressure 21.8m >= 15.0m threshold satisfied in digital twin.',
    },
    explainer: {
      agent: 'EXPLAINER',
      timestamp: 28800.0,
      summary: 'Sensor P_J7 falsified by +18.2m. Physical state safely reconstructed at 22.3m.',
      evidence: {
        evidence_for: ['Residual +18.2m', 'WLS consensus', 'Adjacent sensor agreement'],
        evidence_against: [],
        assumptions: ['Stable clearwell supply'],
      },
      confidence: 0.95,
    },
  },
};

export const MOCK_AUDIT: AuditLogResponse = {
  entries: [
    {
      entry_id: 'AUD-0001',
      timestamp: 28800.0,
      agent: 'SENTINEL',
      action: 'CYBER_ANOMALY_DETECTED',
      payload: { sensor: 'P_J7', residual: 18.2, threat: 'HIGH' },
      previous_hash: '0000000000000000000000000000000000000000000000000000000000000000',
      entry_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    },
    {
      entry_id: 'AUD-0002',
      timestamp: 28805.0,
      agent: 'INTEGRITY',
      action: 'SENSOR_TRUST_DEGRADED',
      payload: { sensor: 'P_J7', trust_score: 0.0, plc: 'PLC_2' },
      previous_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      entry_hash: '8792070e56f4d1e0fc4c94f576e331c463fa7db3ae51d14878b1cf31ae8bc71d',
    },
    {
      entry_id: 'AUD-0003',
      timestamp: 28810.0,
      agent: 'RECONSTRUCTION',
      action: 'PHYSICAL_STATE_RECONSTRUCTED',
      payload: { target: 'J7', raw_m: 40.5, reconstructed_m: 22.3, reduction_pct: 97.5 },
      previous_hash: '8792070e56f4d1e0fc4c94f576e331c463fa7db3ae51d14878b1cf31ae8bc71d',
      entry_hash: '6a87c126d41d1df36f54eb75c1a7d655f483fd8bf042a9b6c0757a3e6f98efd9',
    },
    {
      entry_id: 'AUD-0004',
      timestamp: 28815.0,
      agent: 'RESPONSE',
      action: 'PLAYBOOK_SIMULATED_SAFE',
      payload: { playbook: 'PB-RES-02', min_pressure_m: 21.8, safe: true },
      previous_hash: '6a87c126d41d1df36f54eb75c1a7d655f483fd8bf042a9b6c0757a3e6f98efd9',
      entry_hash: '4d805090f4886f4559892c90e6659c2cc0a66d3a01004bbbb55ff825969a9b70',
    },
  ],
  total_entries: 4,
  is_chain_valid: true,
};

// Resilient API Call Helper
async function apiFetch<T>(endpoint: string, fallback: T, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!res.ok) {
      return fallback;
    }
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}

export const api = {
  getHealth: () =>
    apiFetch<HealthResponse>('/health', {
      status: 'healthy',
      version: '0.8.0',
      mode: 'SANDBOX - ADVISORY ONLY',
      advisory_only: true,
      physical_control_prohibited: true,
      system_name: 'PROJECT LASTLINE',
    }),

  getTopology: () => apiFetch<NetworkTopology>('/network/topology', MOCK_TOPOLOGY),

  getSensors: () =>
    apiFetch<{ sensors: Record<string, SensorMeta>; total_sensors: number }>(
      '/network/sensors',
      { sensors: {}, total_sensors: 22 }
    ),

  getScenarios: () =>
    apiFetch<{ scenarios: ScenarioMeta[] }>('/scenarios', {
      scenarios: MOCK_SCENARIOS,
    }),

  selectScenario: (scenario_id: string) =>
    apiFetch<{ status: string; active_scenario_id: string }>(
      '/scenarios/select',
      { status: 'success', active_scenario_id: scenario_id },
      { method: 'POST', body: JSON.stringify({ scenario_id }) }
    ),

  getCurrentState: () => apiFetch<SystemStateFrame>('/state/current', MOCK_FRAME),

  getAgentReports: () => apiFetch<AgentReports>('/agents/reports', MOCK_FRAME.agent_reports),

  getRecommendations: () =>
    apiFetch<{ recommendations: VerifiedRecommendation[]; advisory_mode: boolean; requires_human_approval: boolean }>(
      '/playbooks/recommendations',
      { recommendations: MOCK_FRAME.recommendations, advisory_mode: true, requires_human_approval: true }
    ),

  recordOperatorAction: (req: ActionApprovalRequest) =>
    apiFetch<{
      recommendation_id: string;
      approval_status: string;
      executed_physical_command: boolean;
      notice: string;
    }>(
      '/playbooks/action',
      {
        recommendation_id: req.recommendation_id,
        approval_status: req.action === 'APPROVE' ? 'APPROVED' : 'REJECTED',
        executed_physical_command: false,
        notice: 'SANDBOX ENVIRONMENT - ADVISORY ONLY',
      },
      { method: 'POST', body: JSON.stringify(req) }
    ),

  getAuditEntries: () => apiFetch<AuditLogResponse>('/audit/entries', MOCK_AUDIT),

  getReplayStatus: () =>
    apiFetch<ReplayStatus>('/replay/status', {
      current_hour: 8,
      max_hours: 24,
      scenario_id: 'SCENARIO_01_SENSOR_BIAS',
      is_playing: false,
      speed: 1.0,
      loop: false,
    }),

  controlReplay: (command: string, speed?: number, target_hour?: number) =>
    apiFetch<ReplayStatus>(
      '/replay/control',
      {
        current_hour: target_hour ?? 8,
        max_hours: 24,
        scenario_id: 'SCENARIO_01_SENSOR_BIAS',
        is_playing: command === 'PLAY',
        speed: speed ?? 1.0,
        loop: false,
      },
      {
        method: 'POST',
        body: JSON.stringify({ command, speed, target_hour }),
      }
    ),
};
