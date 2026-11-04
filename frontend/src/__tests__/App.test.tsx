import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import App from '../App';
import { useLastlineStore } from '../store/useLastlineStore';
import { MOCK_FRAME, MOCK_TOPOLOGY, MOCK_SCENARIOS, MOCK_AUDIT } from '../api/client';

describe('PROJECT LASTLINE: Frontend Operations Console', () => {
  beforeEach(() => {
    // Reset store state to initial mock values
    useLastlineStore.setState({
      isDark: false,
      activeView: 'OPERATIONS_MAP',
      connectionStatus: 'LIVE',
      topology: MOCK_TOPOLOGY,
      scenarios: MOCK_SCENARIOS,
      activeScenarioId: 'SCENARIO_01_SENSOR_BIAS',
      selectedElementId: 'J7',
      selectedSensorId: 'P_J7',
      frame: MOCK_FRAME,
      auditEntries: MOCK_AUDIT.entries,
      isChainValid: true,
      approvalRecords: {},
    });
  });

  it('renders persistent advisory safety boundary pill and brand title', () => {
    render(<App />);

    // Brand Title
    expect(screen.getByText('PROJECT LASTLINE')).toBeInTheDocument();
    expect(screen.getByText('v0.8.0')).toBeInTheDocument();

    // Mandatory Advisory Safety Banner
    const advisoryPill = screen.getByTestId('advisory-pill');
    expect(advisoryPill).toBeInTheDocument();
    expect(advisoryPill).toHaveTextContent(/SANDBOX – ADVISORY ONLY/i);
    expect(advisoryPill).toHaveTextContent(/ZERO PHYSICAL ACTUATION/i);
  });

  it('supports theme toggle between light and dark modes', () => {
    render(<App />);

    const themeToggle = screen.getByLabelText(/switch to dark mode/i);
    expect(themeToggle).toBeInTheDocument();

    fireEvent.click(themeToggle);
    expect(useLastlineStore.getState().isDark).toBe(true);

    const lightToggle = screen.getByLabelText(/switch to light mode/i);
    fireEvent.click(lightToggle);
    expect(useLastlineStore.getState().isDark).toBe(false);
  });

  it('navigates seamlessly across all four control-room views', async () => {
    render(<App />);

    // 1. Initial: Operations Map
    expect(screen.getByText(/Verdant City Water Distribution Network/i)).toBeInTheDocument();

    // 2. Switch to Agent Reasoning
    fireEvent.click(screen.getByRole('button', { name: /Agent Reasoning/i }));
    await waitFor(() => {
      expect(screen.getByText(/Multi-Agent Reasoning Pipeline/i)).toBeInTheDocument();
      expect(screen.getByText(/1. Sentinel Agent/i)).toBeInTheDocument();
      expect(screen.getByText(/6. Explainer Agent/i)).toBeInTheDocument();
    });

    // 3. Switch to Digital Twin Lab
    fireEvent.click(screen.getByRole('button', { name: /Digital Twin Lab/i }));
    await waitFor(() => {
      expect(screen.getByText(/Telemetry Inspector & Digital Twin State Reconstruction/i)).toBeInTheDocument();
      expect(screen.getByText(/Raw Measured SCADA/i)).toBeInTheDocument();
      expect(screen.getByText(/Reconstructed Physics State/i)).toBeInTheDocument();
    });

    // 4. Switch to Audit Ledger
    fireEvent.click(screen.getByRole('button', { name: /Audit Ledger/i }));
    await waitFor(() => {
      expect(screen.getByText(/CRYPTOGRAPHIC SHA-256 AUDIT CHAIN/i)).toBeInTheDocument();
      expect(screen.getByText('AUD-0001')).toBeInTheDocument();
    });
  });

  it('provides simulation transport replay scrubber and scenario picker', () => {
    render(<App />);

    // Current hour indicator
    expect(screen.getByText(/T\+08\.0h \/ 24h/i)).toBeInTheDocument();

    // Transport buttons
    const playBtn = screen.getByTitle(/Play Simulation/i);
    expect(playBtn).toBeInTheDocument();

    // Step forward button
    const stepBtn = screen.getByTitle(/Step Forward/i);
    fireEvent.click(stepBtn);

    // Speed options
    expect(screen.getByText('1x')).toBeInTheDocument();
    expect(screen.getByText('2x')).toBeInTheDocument();
    expect(screen.getByText('5x')).toBeInTheDocument();
  });

  it('executes human-in-the-loop advisory recommendation workflow', async () => {
    render(<App />);

    // Check pre-approved fallback procedure
    expect(screen.getByText(/Zone B Telemetry Quarantine & Hospital Pressure Verification/i)).toBeInTheDocument();
    expect(screen.getByText(/EPANET TWIN: VERIFIED SAFE/i)).toBeInTheDocument();

    // Check evidence balance sheet sections
    expect(screen.getByText(/EVIDENCE FOR/i)).toBeInTheDocument();
    expect(screen.getByText(/EVIDENCE AGAINST/i)).toBeInTheDocument();
    expect(screen.getByText(/ASSUMPTIONS/i)).toBeInTheDocument();

    // Approve action
    const approveBtn = screen.getByRole('button', { name: /APPROVE PROCEDURE/i });
    expect(approveBtn).toBeInTheDocument();

    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(screen.getByText(/PROCEDURE APPROVED/i)).toBeInTheDocument();
      expect(screen.getByText(/RECORDED IN AUDIT LEDGER/i)).toBeInTheDocument();
    });
  });
});
