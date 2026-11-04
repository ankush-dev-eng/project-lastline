/**
 * PROJECT LASTLINE: Frontend Domain Types & API Contracts.
 * 
 * Defines all data models matching FastAPI backend schemas for
 * digital twin simulation, multi-agent reasoning, telemetry trust,
 * state reconstruction, advisory recommendations, and audit logs.
 */

export type ViewMode = 'OPERATIONS_MAP' | 'AGENT_REASONING' | 'TWIN_LAB' | 'AUDIT_LOG';

export interface HealthResponse {
  status: string;
  version: string;
  mode: string;
  advisory_only: boolean;
  physical_control_prohibited: boolean;
  system_name: string;
}

export interface NetworkNode {
  id: string;
  type: 'Junction' | 'Tank' | 'Reservoir';
  elevation_m: number;
  coordinates: [number, number];
}

export interface NetworkLink {
  id: string;
  type: 'Pipe' | 'Pump' | 'Valve';
  start_node: string;
  end_node: string;
  length_m: number;
  diameter_m: number;
}

export interface ZoneInfo {
  zone_id: string;
  name: string;
  elevation_range: string;
  nodes: string[];
  critical_facilities: string[];
}

export interface NetworkTopology {
  network_name: string;
  nodes: NetworkNode[];
  links: NetworkLink[];
  zones: ZoneInfo[];
}

export interface SensorMeta {
  sensor_id: string;
  sensor_type: 'PRESSURE' | 'TANK_LEVEL' | 'FLOW_RATE' | 'STATUS';
  element_id: string;
  plc_id: string;
  unit: string;
  min_normal: number;
  max_normal: number;
  criticality: number;
  zone_id: string;
}

export interface ScenarioMeta {
  scenario_id: string;
  name: string;
  description: string;
  attack_type: string;
  target_components: string[];
  target_plc: string;
  start_hour: number;
  duration_hours: number;
}

export interface EvidenceBalanceSheet {
  evidence_for: string[];
  evidence_against: string[];
  assumptions: string[];
}

export interface SimulationResult {
  simulation_id: string;
  playbook_id: string;
  duration_hours: number;
  is_hydraulically_safe: boolean;
  minimum_pressure_m: number;
  critical_nodes_failing: string[];
  minimum_tank_levels: Record<string, number>;
  tanks_overflowing: string[];
  tanks_depleted: string[];
  simulation_duration_ms: number;
}

export interface VerifiedRecommendation {
  recommendation_id: string;
  playbook_id: string;
  title: string;
  description: string;
  target_zone: string;
  target_components: string[];
  recommended_actions: string[];
  evidence: EvidenceBalanceSheet;
  confidence_score: number;
  simulation_proof: SimulationResult;
  advisory_notice: string;
  requires_human_approval: boolean;
  approval_status?: 'PENDING' | 'APPROVED' | 'REJECTED';
}

export interface SentinelReport {
  agent: string;
  timestamp: number;
  anomalies_detected: number;
  flagged_sensors: string[];
  traffic_anomalies: string[];
  threat_level: 'NORMAL' | 'ELEVATED' | 'HIGH' | 'CRITICAL';
}

export interface IntegrityReport {
  agent: string;
  timestamp: number;
  sensor_trust: Record<string, number>;
  plc_trust: Record<string, number>;
  compromised_sensors: string[];
  compromised_plcs: string[];
  system_alarm: boolean;
}

export interface ReconstructionReport {
  agent: string;
  timestamp: number;
  state_estimates: Record<string, number>;
  uncertainties: Record<string, number>;
  stability_index: number;
  top_suspicious_components: string[];
}

export interface ImpactReport {
  agent: string;
  timestamp: number;
  overall_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  zone_priorities: string[];
  critical_facilities_at_risk: string[];
  pressure_deficits_m: Record<string, number>;
  tanks_time_to_empty_hours: Record<string, number>;
}

export interface ResponseReport {
  agent: string;
  timestamp: number;
  recommended_playbook: string;
  actions: string[];
  verification_passed: boolean;
  simulation_summary: string;
}

export interface ExplainerReport {
  agent: string;
  timestamp: number;
  summary: string;
  evidence: EvidenceBalanceSheet;
  confidence: number;
}

export interface AgentReports {
  sentinel: SentinelReport;
  integrity: IntegrityReport;
  reconstruction: ReconstructionReport;
  impact: ImpactReport;
  response: ResponseReport;
  explainer: ExplainerReport;
}

export interface SystemStateFrame {
  timestamp: number;
  current_hour: number;
  max_hours: number;
  scenario_id: string;
  is_playing: boolean;
  speed: number;
  telemetry: Record<string, number>;
  reconstructed_state: Record<string, number>;
  uncertainties: Record<string, number>;
  sensor_trust: Record<string, number>;
  plc_trust: Record<string, number>;
  system_alarm: boolean;
  stability_index: number;
  top_suspicious: string[];
  zone_priorities: string[];
  critical_facilities_at_risk: string[];
  pressure_deficits_m: Record<string, number>;
  tanks_time_to_empty_hours: Record<string, number>;
  recommendations: VerifiedRecommendation[];
  explainer_summary: string;
  evidence: EvidenceBalanceSheet;
  confidence: number;
  agent_reports: AgentReports;
}

export interface AuditEntry {
  entry_id: string;
  timestamp: number;
  agent: string;
  action: string;
  payload: Record<string, any>;
  previous_hash: string;
  entry_hash: string;
}

export interface AuditLogResponse {
  entries: AuditEntry[];
  total_entries: number;
  is_chain_valid: boolean;
}

export interface ReplayStatus {
  current_hour: number;
  max_hours: number;
  scenario_id: string;
  is_playing: boolean;
  speed: number;
  loop: boolean;
}

export interface ActionApprovalRequest {
  recommendation_id: string;
  action: 'APPROVE' | 'REJECT';
  operator_id: string;
  notes?: string;
}

