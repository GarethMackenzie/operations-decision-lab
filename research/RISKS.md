# Risk register

| Risk | Severity | Mitigation / release rule | Remaining evidence |
|---|---|---|---|
| Four-person illustration overloaded | Critical | Exact capacity gate; return no feasible option | Unit and full workflow tests |
| Completion gaps misread as service | Critical | Never infer; explicit manual assumptions or verified interval attestation | Operator semantic review |
| Synthetic output treated as real recommendation | Critical | Persistent hypothetical label, no external-validated state in MVP | Partner validation and intervention |
| Selection bias / small Monte Carlo sample | High | 30 selection + 30 independent evaluation runs; no reselection | Input/model uncertainty remains |
| Empty-start optimism and shift censoring | High | Initial pick/pack queue inputs, exact cutoff, unfinished counts | Real backlog ages/stage state |
| Breaks, skills, sharing, waves or batching differ | High | One synchronized pausing break; dedicated homogeneous workers; disclose unsupported cases | Site observation and richer model |
| Public dataset semantics/rights unresolved | High | Use original synthetic demo only | Inspect records and license before adoption |
| Upstream dependency mismatch/license | High | Pin tested environment; no Prosimos integration | Isolated licensed benchmark later |
| Upload abuse / browser injection | High | Size/row/job bounds; strict JSON/CSV; DOM text/escaped export; loopback; no disk persistence | Security tests, dependency audit |
| Costs overclaimed | Medium | Scheduled payroll and marginal payroll shown; no invented overtime/savings | Actual wage/currency/contract data |
| No customer need demonstrated | High | Label market assumptions; interviews before expansion | Interviews / trial behavior |
| GitHub access or hosted check block | Medium | Preserve local artifact; no public release/tag until required gates pass | Authenticated destination and CI evidence |
| Monte Carlo CI misunderstood | High | Interval for mean under fixed model; show replication values, sensitivity | Input uncertainty studies |

Owner: project maintainer, GarethMackenzie. Review after each new dataset, model extension or dependency update. No risk is closed solely because tests exist.
