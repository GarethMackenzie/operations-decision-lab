# MVP specification and release gates

Recorded before implementation, 2026-09-16. Release class: **synthetic research prototype**, not validated operational advice. First user/decision and hypotheses: [research dossier](../research/DOSSIER.md).

## Mandatory capabilities

R1. Load bundled synthetic CSV or bounded supported user CSV, report errors, missing stages, resource overlaps, censoring and window exposure. Descriptive metrics remain separate from assumptions.

R2. Require explicit assumptions. Interval adoption requires active-service attestation and complete positive intervals, with overlap blocking. Completion timestamps alone never generate service estimates. Accept manual means regardless of descriptive limitations, with prominent hypothetical labels.

R3. Simulate FIFO picking then packing with dedicated homogeneous staff, independent Poisson arrivals and lognormal service (CV zero gives deterministic service). One common mid-shift break pauses all service and retains the job/resource. Initial backlog supports queues at either stage; no pre-existing in-service jobs or age reconstruction. All simulation stops at scheduled shift end, without drain or overtime.

R4. Enumerate positive pick/pack integer allocations using up to 2–6 total workers. Check workload against break-adjusted nominal capacity, strict utilization <1, user utilization ceiling, payroll budget and a due-cohort service target. Feasibility is conditional on assumptions. Distinguish best tested candidate from sufficient capacity. Default: 18 orders/hour, 6/7 min, four staff, 8 hours, no break. Best nominal capacity = min(2×60/6,2×60/7)=17.142857/hour <18; all allocations fail.

R5. Thirty common-random-number replications per scenario; independent 30-run evaluation of the selected candidate. Approximate 95% Student-t mean intervals. If evaluation fails, state no confirmed feasible option; do not pick a runner-up using evaluation seeds. Sensitivity: +20% arrivals, +20% both mean services, and CV at least 1 for selected allocation, using independent runs.

R6. Report scheduled payroll = total staff × shift hours × hourly wage, even for idle/break time. Compare marginal payroll with explicit baseline allocation. No overtime or penalty costs in MVP; do not present hypothetical penalties as cash savings.

R7. Export self-contained HTML plus deterministic JSON with exact submitted CSV text (browser line endings may be normalized), its hash, observation bounds, data findings, explicit configuration, every replication result, selection/evaluation seeds, model version and environment versions. Original input in exports is deliberate and labelled; uploaded data is not saved server-side. CLI can replay JSON and verify identical numerical results. No timestamp in deterministic report payload.

R8. Keyboard-labelled responsive interface with sample, inspect, configure, compare, results and export. CLI supports the same core. No paid API or external network during use.

## Deliberate exclusions

No BPMN discovery, optimization of shift schedules, heterogeneous skills, multitasking, batching, conveyors, SKU-dependent travel, demand seasonality, overnight carryover simulation, in-service initial work, overtime, multi-tenant hosting or AI-generated numerical explanations. These require different evidence/model scope. A single-shift run does not validate long-run performance.

## Gates fixed before implementation

| Gate | Requirement | Evidence |
|---|---|---|
| G1 Install/build | Clean Python 3.12 environment, locked install, wheel; all documented CLI/server paths work | Commands, wheel smoke and replay |
| G2 Quality | Ruff lint/format, mypy on application, compile/build | Executed output |
| G3 Input integrity | Invalid schema/types/dates, missing stages, duplicates, overlap, oversized payloads and censoring tests | Meaningful negative tests |
| G4 Numerical | Hand cases, conservation, capacity/shift/break constraints, independent scheduling reference | Executed tests |
| G5 Evaluation | Default no feasible; known feasible case; independent seeds; CI and sensitivity; deterministic replay | Tests and example report |
| G6 UX/performance | Actual browser sample→inspect→compare→export; invalid state and keyboard; default <15 s, bounded max <60 s and peak process <512 MiB on recorded local machine | Browser observations + measured benchmark |
| G7 Security/rights | Secret scan, Bandit, runtime dependency audit; review findings; own synthetic data, third-party notices | Executed checks + attribution |
| G8 Docs/traceability | README commands/examples match current code; requirement/test mapping and known limitations | Review + recorded commands |
| G9 Hosted release | Only after G1–G8 pass: verified account, private new repo, CI passes exact revision, public visibility verified, clean remote quick start, release tag | Remote SHA/CI/visibility evidence |
| G10 External predictions | Authorized representative data, temporal holdout and monitored intervention | NOT APPLICABLE to prototype; mandatory for predictive claims |

Every gate receives PASS, FAIL, BLOCKED or NOT APPLICABLE with reasons. G1–G8 are mandatory before first project upload. G9 is mandatory before declaring public release. G10 cannot be described as passed by synthetic tests.
