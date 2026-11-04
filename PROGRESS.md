# PROJECT LASTLINE: Progress & State Tracker

## Active Phase
- **Current Phase**: Phase 1 — Digital Twin (EPANET + WNTR)
- **Current Branch**: `phase/01-digital-twin`
- **Iteration Count**: 1 / 10
- **Status**: Planning & Acceptance Test Authoring

## Phase Gate Checklist
- [x] **Phase 0: Scaffold**: Monorepo (`/backend`, `/frontend`, `/twin`, `/data`, `/docs`, `/benchmarks`, `/assets`), CI, Makefile. Gate: CI green, 86% coverage, zero write endpoints verified.
- [ ] **Phase 1: Digital Twin**: EPANET water network with sensors, pumps, valves, tanks, zones; baseline simulation. Gate: reproducible baseline hydraulics, unit tests.
- [ ] **Phase 2: Attack/Failure Injector**: Sensor spoofing, replay attacks, PLC setpoint tampering, communication loss, sensor dropout; $\ge 10$ labelled seeded scenarios + BATADAL ingestion. Gate: scenarios reproducible and labelled.
- [ ] **Phase 3: Detection & Telemetry Trust Scoring**: Per sensor/PLC. Gate: $F_1 \ge 0.85$ and $\text{FPR} \le 5\%$ on held-out test scenarios; TTD better than threshold baseline.
- [ ] **Phase 4: Physical State Reconstruction**: Trusted sensors + hydraulic constraints (WLS/Kalman/Bayesian fusion), uncertainty estimates. Gate: RMSE at least 40% lower than raw-telemetry baseline under attack; top-3 attribution accuracy $\ge 80\%$.
- [ ] **Phase 5: Specialized Agents**: Sentinel, Integrity, Reconstruction, Impact, Response, Explainer. Typed contracts, orchestrator, audit log. Gate: contract and integration tests pass.
- [ ] **Phase 6: Recommendations**: Pre-approved fallback playbooks per site, twin simulation prior to display. Gate: 100% of recommendations satisfy minimum-pressure and tank-level constraints; evidence, confidence, and assumptions list.
- [ ] **Phase 7: Streaming API & Sandbox Barrier**: REST + WebSockets live stream, replay controls. Gate: p95 latency < 200ms; stream updates $\le 1$s; read-only safety test proves no control-write path exists.
- [ ] **Phase 8: Control Room Frontend**: Map, topology, reasoning graph, recommendation drawer, audit log. Gate: Lighthouse $\ge 90$, stable 60 fps, INP < 200ms, zero console errors, E2E tests pass.
- [ ] **Phase 9: Hardening & Threat Model**: Coverage $\ge 80\%$, dependency audit, `/docs/THREAT_MODEL.md`, full benchmark run. Gate: all tests green.
- [ ] **Phase 10: Final Release & Assets**: Self-hosted SVG hero, animated tagline, architecture diagrams, `v1.0.0` tagged.

## Next Steps
1. Write Phase 1 acceptance tests (`tests/test_digital_twin.py`) testing EPANET network loading, hydraulic simulation, diurnal patterns, sensor placement, and mass conservation.
2. Build network model generator (Richmond / C-Town or calibrated municipal benchmark model) with tanks, pumps, valves, junctions, and zones.
3. Implement `twin/model.py` and `twin/simulator.py`.
4. Verify baseline hydraulics: zero solver failures, mass conservation holds.
5. Merge `phase/01-digital-twin` into `main`, tag `v0.1.0`.
