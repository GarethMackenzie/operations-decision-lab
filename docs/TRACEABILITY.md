# Requirement and verification mapping

| Requirement | Implementation | Executed verification target |
|---|---|---|
| R1 CSV/window/quality | `data.inspect_csv`, inspect API and UI | `test_data.py`: missing starts, timezone, duplicates, bounds, censoring, worker overlap, row limit |
| R2 explicit assumptions | `report.make_report`, UI confirmation/adoption | `test_assumptions_required_and_no_unattested_adoption`, valid adoption/mismatch test |
| R3 process and boundary | `model.simulate`, `active_time`, `workload` | Hand example; inclusive shift boundary; paused break; stage-specific initial backlog |
| R4 exhaustive feasibility | `model.capacity`, `analysis.compare` | Default exact 120/7 bottleneck, equality unstable, every default scenario fails; known feasible case |
| R5 uncertainty/evaluation | `analysis.interval`, `evaluate`, `compare` | Hand Student-t interval, missing cohort, independent seed sets, reproducibility, sensitivity presence |
| R6 honest costs | `model.capacity`, report/UI | Payroll and marginal cost hand tests; no overtime/penalty implementation |
| R7 reproducible exports | `report.canonical`, `report_html`, CLI replay | API/HTML/JSON equivalence, escaping; clean installed CLI demo and replay |
| R8 interface and privacy | static UI, `web.create_app`, Waitress loopback | Actual browser flow, keyboard, invalid state; API host/origin/size/type tests |
| Warehouse friction | `friction.WarehouseFriction`, `assess_friction`, UI and report | Explicit service-time arithmetic, invalid assumptions, separate adjusted comparison, confirmation and HTML export tests |
| G4 independent calculation | Test-only server-availability recurrence | Four staffing combinations compared order-by-order against SimPy |
| G6 performance | `scripts/benchmark.py` | Full default and maximum-load comparison, wall clock + peak RSS |
| G7 security | CSP, strict JSON/CSV, no disk uploads, one compute lock | Bandit; advisory audit; tracked-file secret scan; invalid input tests |
| G9 publication | `.github/workflows/verify.yml` | Exact remote revision, CI, visibility, clean cloned quick start; recorded separately |

Results belong in [verification evidence](../evidence/VERIFICATION.md). This table identifies tests; it does not imply a test passed until the evidence records its actual execution.
