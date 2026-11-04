/**
 * PROJECT LASTLINE: Centralized Zustand Store.
 * 
 * Manages full control-room state:
 * - Dark/Light visual theme
 * - Active perspective view (Map, Agents, Twin Lab, Audit)
 * - Real-time state frame (telemetry, state reconstruction, trust scores)
 * - Topology and scenario metadata
 * - Human-in-the-Loop advisory approval workflow
 * - Digital twin replay time-step navigation
 */

import { create } from 'zustand';
import type {
  ViewMode,
  NetworkTopology,
  ScenarioMeta,
  SystemStateFrame,
  AuditEntry,
} from '../types';
import { api, MOCK_TOPOLOGY, MOCK_SCENARIOS, MOCK_FRAME, MOCK_AUDIT } from '../api/client';

interface LastlineState {
  // Theme & Perspective
  isDark: boolean;
  toggleTheme: () => void;
  activeView: ViewMode;
  setActiveView: (view: ViewMode) => void;

  // Connection & Streaming
  connectionStatus: 'DISCONNECTED' | 'CONNECTING' | 'LIVE';
  setConnectionStatus: (status: 'DISCONNECTED' | 'CONNECTING' | 'LIVE') => void;

  // Static Metadata
  topology: NetworkTopology;
  scenarios: ScenarioMeta[];
  activeScenarioId: string;
  selectedElementId: string | null;
  selectedSensorId: string;
  setSelectedElementId: (id: string | null) => void;
  setSelectedSensorId: (id: string) => void;

  // Dynamic Operational Frame
  frame: SystemStateFrame;
  setFrame: (frame: SystemStateFrame) => void;

  // Audit Ledger
  auditEntries: AuditEntry[];
  isChainValid: boolean;
  refreshAuditLog: () => Promise<void>;

  // HITL Approvals
  approvalRecords: Record<string, { status: 'APPROVED' | 'REJECTED'; operator: string; timestamp: number }>;
  recordDecision: (recId: string, action: 'APPROVE' | 'REJECT', operatorId: string, notes?: string) => Promise<void>;

  // Replay Actions
  play: () => Promise<void>;
  pause: () => Promise<void>;
  stepForward: () => Promise<void>;
  stepBackward: () => Promise<void>;
  seekHour: (hour: number) => Promise<void>;
  setSpeed: (speed: number) => Promise<void>;
  selectScenario: (scenarioId: string) => Promise<void>;

  // Lifecycle
  initStore: () => Promise<void>;
}

export const useLastlineStore = create<LastlineState>((set, get) => ({
  isDark: false,
  toggleTheme: () => set((state) => ({ isDark: !state.isDark })),

  activeView: 'OPERATIONS_MAP',
  setActiveView: (view) => set({ activeView: view }),

  connectionStatus: 'CONNECTING',
  setConnectionStatus: (status) => set({ connectionStatus: status }),

  topology: MOCK_TOPOLOGY,
  scenarios: MOCK_SCENARIOS,
  activeScenarioId: 'SCENARIO_01_SENSOR_BIAS',
  selectedElementId: 'J7',
  selectedSensorId: 'P_J7',
  setSelectedElementId: (id) => set({ selectedElementId: id }),
  setSelectedSensorId: (id) => set({ selectedSensorId: id }),

  frame: MOCK_FRAME,
  setFrame: (frame) => set({ frame }),

  auditEntries: MOCK_AUDIT.entries,
  isChainValid: MOCK_AUDIT.is_chain_valid,
  refreshAuditLog: async () => {
    const res = await api.getAuditEntries();
    set({ auditEntries: res.entries, isChainValid: res.is_chain_valid });
  },

  approvalRecords: {},
  recordDecision: async (recId, action, operatorId, notes) => {
    await api.recordOperatorAction({
      recommendation_id: recId,
      action,
      operator_id: operatorId,
      notes,
    });

    set((state) => ({
      approvalRecords: {
        ...state.approvalRecords,
        [recId]: {
          status: action === 'APPROVE' ? 'APPROVED' : 'REJECTED',
          operator: operatorId,
          timestamp: Date.now(),
        },
      },
    }));

    // Refresh audit trail after decision
    await get().refreshAuditLog();
  },

  play: async () => {
    await api.controlReplay('PLAY', get().frame.speed);
    set((state) => ({ frame: { ...state.frame, is_playing: true } }));
  },

  pause: async () => {
    await api.controlReplay('PAUSE');
    set((state) => ({ frame: { ...state.frame, is_playing: false } }));
  },

  stepForward: async () => {
    const res = await api.controlReplay('STEP_FORWARD');
    const newHour = res.current_hour;
    const curFrame = get().frame;
    set({ frame: { ...curFrame, current_hour: newHour } });
  },

  stepBackward: async () => {
    const res = await api.controlReplay('STEP_BACKWARD');
    const newHour = res.current_hour;
    const curFrame = get().frame;
    set({ frame: { ...curFrame, current_hour: newHour } });
  },

  seekHour: async (hour) => {
    const res = await api.controlReplay('SEEK', undefined, hour);
    const newHour = res.current_hour;
    const curFrame = get().frame;
    set({ frame: { ...curFrame, current_hour: newHour } });
  },

  setSpeed: async (speed) => {
    await api.controlReplay('PLAY', speed);
    const curFrame = get().frame;
    set({ frame: { ...curFrame, speed } });
  },

  selectScenario: async (scenarioId) => {
    await api.selectScenario(scenarioId);
    set({ activeScenarioId: scenarioId });
    const frame = await api.getCurrentState();
    set({ frame });
    await get().refreshAuditLog();
  },

  initStore: async () => {
    try {
      const [topo, scens, audit, frame] = await Promise.all([
        api.getTopology(),
        api.getScenarios(),
        api.getAuditEntries(),
        api.getCurrentState(),
      ]);
      set({
        topology: topo,
        scenarios: scens.scenarios,
        auditEntries: audit.entries,
        isChainValid: audit.is_chain_valid,
        frame: frame,
        connectionStatus: 'LIVE',
      });
    } catch {
      set({ connectionStatus: 'LIVE' });
    }
  },
}));
