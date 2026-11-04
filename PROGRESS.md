# PROJECT LASTLINE: Progress & State Tracker

## Active Phase
- **Current Phase**: Phase 4 — Physical State Reconstruction
- **Current Branch**: `phase/04-state-reconstruction`
- **Iteration Count**: 1 / 10
- **Status**: Planning & Acceptance Test Authoring

## Phase Gate Checklist
- [x] **Phase 0: Scaffold**: Monorepo (`/backend`, `/frontend`, `/twin`, `/data`, `/docs`, `/benchmarks`, `/assets`), CI, Makefile. Gate: CI green, 86% coverage, zero write endpoints verified.
- [x] **Phase 1: Digital Twin**: EPANET water network with sensors, pumps, valves, tanks, zones; baseline simulation. Gate: reproducible baseline hydraulics, unit tests (97% coverage, 10/10 tests passing).
- [x] **Phase 2: Attack/Failure Injector**: Sensor spoofing, replay attacks, PLC setpoint tampering, communication loss, sensor dropout; $\ge 10$ labelled seeded scenarios + BATADAL ingestion. Gate: scenarios reproducible and labelled (11 scenarios, 96% coverage, 15/15 tests passing).
- [x] **Phase 3: Detection & Telemetry Trust Scoring**: Per sensor/PLC. Gate: $F_1 \ge 0.85$ and $\text{FPR} \le 5\%$ on held-out test scenarios; TTD better than threshold baseline ($F_1 = 1.0000$, $\text{FPR} = 0.00\%$, TTD $= 0.00$h vs $18.00$h baseline, 18/18 tests passing).
- [ ] **Phase 4: Physical State Reconstruction**: Trusted sensors + hydraulic constraints (WLS/Kalman/Bayesian fusion), uncertainty estimates. Gate: RMSE at least 40% lower than raw-telemetry baseline under attack; top-3 attribution accuracy $\ge 80\%$.
- [ ] **Phase 5: Specialized Agents**: Sentinel, Integrity, Reconstruction, Impact, Response, Explainer. Typed contracts, orchestrator, audit log. Gate: contract and integration tests pass.
- [ ] **Phase 6: Recommendations**: Pre-approved fallback playbooks per site, twin simulation prior to display. Gate: 100% of recommendations satisfy minimum-pressure and tank-level constraints; evidence, confidence, and assumptions list.
- [ ] **Phase 7: Streaming API & Sandbox Barrier**: REST + WebSockets live stream, replay controls. Gate: p95 latency < 200ms; stream updates $\le 1$s; read-only safety test proves no control-write path exists.
- [ ] **Phase 8: Control Room Frontend**: Map, topology, reasoning graph, recommendation drawer, audit log. Gate: Lighthouse $\ge 90$, stable 60 fps, INP < 200ms, zero console errors, E2E tests pass.
- [ ] **Phase 9: Hardening & Threat Model**: Coverage $\ge 80\%$, dependency audit, `/docs/THREAT_MODEL.md`, full benchmark run. Gate: all tests green.
- [ ] **Phase 10: Final Release & Assets**: Self-hosted SVG hero, animated tagline, architecture diagrams, `v1.0.0` tagged.

## Next Steps
1. Write acceptance tests (`tests/test_state_reconstruction.py`) enforcing:
   - State reconstruction RMSE $\ge 40\%$ lower than raw-telemetry baseline under attack.
   - Compromised-component attribution top-3 accuracy $\ge 80\%$.
   - Uncertainty estimates ($95\%$ confidence bounds $\hat{x}_i \pm 1.96 \sigma_i$).
2. Implement `backend/reconstruction/estimator.py`:
   - Weighted Least Squares (WLS) state estimator weighting measurements by real-time trust scores $w_i = T_i(t)$.
   - Incorporates hydraulic constraints (mass continuity at junctions and tanks).
   - Solves for true nodal pressures and flows using trusted physical anchors.
   - Computes posterior covariance matrix for uncertainty quantification.
3. Implement `backend/reconstruction/attribution.py`:
   - Ranks suspicious components based on anomaly residuals and trust degradation.
4. Verify gate benchmarks, merge to `main`, and tag `v0.4.0`.
