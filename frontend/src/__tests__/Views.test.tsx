import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { TwinLabView } from '../components/TwinLabView';
import { AuditLogView } from '../components/AuditLogView';
import { useLastlineStore } from '../store/useLastlineStore';
import { MOCK_FRAME, MOCK_AUDIT } from '../api/client';

describe('PROJECT LASTLINE: Perspective Views Unit Tests', () => {
  beforeEach(() => {
    useLastlineStore.setState({
      frame: MOCK_FRAME,
      selectedSensorId: 'P_J7',
      auditEntries: MOCK_AUDIT.entries,
      isChainValid: true,
    });
  });

  it('renders TwinLabView dual-series curves and uncertainty ribbons', () => {
    render(<TwinLabView />);

    expect(screen.getByText(/Telemetry Inspector & Digital Twin State Reconstruction/i)).toBeInTheDocument();
    expect(screen.getByText(/Raw Measured SCADA/i)).toBeInTheDocument();
    expect(screen.getByText(/Reconstructed Physics State/i)).toBeInTheDocument();
    expect(screen.getByText(/±1.96σ Bayesian Uncertainty Band/i)).toBeInTheDocument();

    // Verify statistical residuals
    expect(screen.getByText(/RAW SCADA READING/i)).toBeInTheDocument();
    expect(screen.getByText(/RECONSTRUCTED \(WLS\)/i)).toBeInTheDocument();
    expect(screen.getByText(/PHYSICAL RESIDUAL/i)).toBeInTheDocument();
    expect(screen.getByText(/SENSOR TRUST WEIGHT/i)).toBeInTheDocument();

    // Switch sensor
    const select = screen.getByLabelText(/SELECT INSTRUMENT:/i);
    fireEvent.change(select, { target: { value: 'L_T1' } });
    expect(useLastlineStore.getState().selectedSensorId).toBe('L_T1');
  });

  it('renders AuditLogView with cryptographic verification badge and entries', () => {
    render(<AuditLogView />);

    expect(screen.getByText(/CRYPTOGRAPHIC SHA-256 AUDIT CHAIN: 100% VALID & TAMPER-FREE/i)).toBeInTheDocument();
    expect(screen.getByText('AUD-0001')).toBeInTheDocument();
    expect(screen.getByText('CYBER_ANOMALY_DETECTED')).toBeInTheDocument();

    // Search filter
    const searchInput = screen.getByPlaceholderText(/Search audit trail/i);
    fireEvent.change(searchInput, { target: { value: 'RECONSTRUCTION' } });

    expect(screen.getByText('AUD-0003')).toBeInTheDocument();
    expect(screen.queryByText('AUD-0001')).not.toBeInTheDocument();
  });
});
