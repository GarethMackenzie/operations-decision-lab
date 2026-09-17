# Research dossier

Access dates: 2026-09-15 to 2026-09-16. Scope: targeted primary-source searches for warehouse staffing, public picking data, BPI 2019, simulation validation, SimPy, Simod, Prosimos, log-distance-measures and PM4Py. Three API research repositories were shallow-cloned and inspected locally. This is not an exhaustive GitHub or market search. No interviews have occurred; no customer demand, adoption or willingness to pay has been established.

## Recommendation and first user

**Recommendation:** release a local, synthetic research prototype for an operations analyst supporting a small fulfilment shift supervisor. The proposed decision is how to allocate a fixed or slightly expandable team between dedicated picking and packing for one shift, before the next roster is set. Daily/weekly decision frequency, purchasing authority and value are hypotheses to test. Constraints include skills, paid hours, breaks, initial backlog, available workstations and delivery deadlines.

The useful contribution is an auditable path from evidence quality to explicit assumptions to a staffing comparison, including an honest “no feasible option.” It is not a new general-purpose simulator, automated staffing policy or validated digital twin. A portfolio demonstration is achievable now; operational efficacy requires a partner dataset and intervention evidence.

**Proceed:** a complete reproducible synthetic workflow with correct conservation and capacity logic. **Narrow:** if only completion events exist, provide descriptive counts and request service assumptions. **Stop a claim:** do not publish productivity savings, optimal real staffing or predictive accuracy without externally held-out evidence and stakeholder review.

## Model choice

| Approach | Appropriate use | Main failure / cost | Decision |
|---|---|---|---|
| Workload/capacity arithmetic | Necessary stability screen; transparent hand check | Ignores variability, finite-horizon backlog and service targets; O(scenarios) | Mandatory first screen |
| Two-stage discrete-event simulation | Queues, variable service, shift cutoffs, dedicated staff | Wrong calendar/service semantics give convincing but wrong output; O(replications × jobs × log(events)) | SimPy, fixed seeds |
| Queueing formulas (M/M/c) | Independent simple steady-state checks | Poisson/exponential/stationary assumptions; tandem and break effects need care | Reference cases only, not product prediction |
| Exhaustive integer allocations | Small team (2–6 workers), explainable feasible set | Grows combinatorially with skills/calendars | Enumerate every pair within budget |
| MILP / CP-SAT | Large roster and legal/skill constraints | Service-level constraints need surrogate or simulation coupling | Later, after validated need |
| Simod + Prosimos discovery/optimization | Rich event logs, BPMN, differentiated calendars | Missing starts can be estimated; inferred duration is not observed active work; older Python compatibility | Isolated future benchmark |
| Generative ML / RL | Large validated training corpus and repeated decisions | Intervention validity, opacity, training cost | No MVP role |

Use common random workloads to compare allocations. Select a candidate on 30 replications, then independently evaluate it on 30 new seeds; do not select again on the evaluation set. Approximate 95% Student-t intervals on replication means describe Monte Carlo uncertainty conditional on assumptions, not input uncertainty or prediction intervals. Test arrival and service-time sensitivity separately. Explicitly retain incomplete work at shift end. Never stop arrivals, drain the queue, then claim steady-state sufficiency.

The literature supports evaluating temporal behavior as well as activity sequence. Camargo et al. describe automated calibration and limitations of temporal fit ([2019 paper](https://arxiv.org/abs/1910.05404), [2021 paper](https://arxiv.org/abs/2103.11944)). Our inference: matching historic traces is insufficient to establish the causal effect of reallocating staff. Input dependence, task mix and worker adaptation remain unverified.

## Product/competitor comparison

| Tool | Verified capability / evidence | Reuse or difference |
|---|---|---|
| SimPy 4.1.2 | Process/resource simulation, MIT, Python >=3.8; installed `core.py` uses event heaps; `resources/resource.py` implements requests/releases | Reuse engine; add data gates, costs, scenario policy and report |
| Simod 5.1.6 | Discovery pipeline, hyperparameter optimization, train/test config and simulation evaluation tests | More general; no direct integration on Python 3.12 |
| Prosimos 2.0.6 | BPMN execution, differentiated resource calendars, batching and priorities | Richer future benchmark; Python and license issues below |
| log-distance-measures 2.2.0 | Temporal, arrival, cycle and WIP distances, with fixtures/tests | Method reference; optional isolated benchmark |
| PM4Py | Process discovery/conformance library; current source LICENSE is AGPL-3.0 | Not required for a fixed two-stage workflow; reassess integration obligations before reuse |
| AnyLogic | Commercial warehouse modelling, layout and staffing examples | Broader modelling environment; local prototype emphasizes a narrow reproducible decision report |
| Spreadsheet arithmetic | Easy capacity/cost comparison | Baseline competitor; our hypothesis is that explicit uncertainty/data gates justify added complexity |

Primary sources: [SimPy documentation](https://simpy.readthedocs.io/en/4.1.2/), [SimPy package/release](https://pypi.org/project/simpy/4.1.2/), [PM4Py LICENSE](https://github.com/process-intelligence-solutions/pm4py/blob/release/LICENSE), [AnyLogic warehouse case studies](https://www.anylogic.com/resources/case-studies/?industry=warehouse-operations). Vendor examples evidence availability, not independently verified ROI or demand for this product. No current commercial price is quoted.

## Repository inspection beyond READMEs

All links can be made immutable by replacing the branch with the SHA below. Source clones are excluded from publication; no upstream code copied into the application.

### Simod

[Repository](https://github.com/AutomatedProcessImprovement/Simod), SHA `56cd99f61f64e2b08656f88d617586eac2687416`, commit 2025-05-27. `pyproject.toml`: 5.1.6, Python ^3.9,<3.12; Prosimos, pix-framework, pandas, scipy, hyperopt and Java tooling. Root LICENSE: Apache-2.0. Inspected `src/simod/event_log/preprocessor.py`: missing starts invoke an estimator and optional multitasking adjustment. Inspected `src/simod/simulation/prosimos.py`: repeated simulation and evaluation. `resources/config/configuration_example_with_evaluation.yml` separates train/test logs and lists multiple metrics. `tests/test_simulation/test_evaluate_logs.py` checks serial/parallel evaluation; smoke assertion is nonempty output, not numerical accuracy. CI and tests exist, but were not run; a commit date is maintenance evidence, not a maintenance guarantee.

### Prosimos

[Repository](https://github.com/AutomatedProcessImprovement/Prosimos), SHA `ec2c57eb845d87392ea03e5acfe31595fe2da94d`, commit 2025-01-30. `pyproject.toml`: 2.0.6, Python >=3.9,<3.12, numpy/pandas/scipy/pix-framework. Inspected `prosimos/simulation_engine.py`: resource availability, priority queues and batched-case handling. `simulation_scenario_example.json` includes worker cost, tasks and calendar references. `testing_scripts/test_simulation_arrival_time_calendar.py` tests starts inside/outside calendars. CI installs Python 3.9 and Poetry 1.4.2. No root LICENSE found in inspected tree, and no license field in the package declaration. Redistribution permission therefore unresolved; do not vendor or integrate until clarified. README's “3.9+” is less restrictive than actual package constraints.

### log-distance-measures

[Repository](https://github.com/AutomatedProcessImprovement/log-distance-measures), SHA `068bcc933c6587b486b62992460aa5a096f3a4ba`, commit 2026-07-27. `pyproject.toml`: 2.2.0, Python >=3.11,<3.12; pandas/scipy/jellyfish/pulp. LICENSE: Apache-2.0. `src/log_distance_measures/work_in_progress.py` computes interval overlap in windows and warns of normalization sensitivity. `tests/work_in_progress_test.py` includes exact expected window weights and identical/different log comparisons. `tests/assets/test_event_log_1.csv` has Resource, Activity, start_time, end_time, case_id; first rows have equal start/end times, showing why positive-duration validation matters. CI matrix still includes 3.9/3.10 despite current 3.11-only constraint: inspect actual hosted status before reuse. Tests were inspected, not executed.

## Delivery, security and economics

Recommendation: Python 3.12 + SimPy + Flask + Waitress, local loopback only, static HTML/CSS/JS interface, no database, accounts, external AI or telemetry. Package static assets and sample with the wheel. Lock runtime and verification dependencies after installation. Keep parsing, model, evaluation and presentation separate. No public application hosting is required for GitHub source publication.

Local incremental hosting/API spend is zero under the assumption that an existing computer is used; electricity and staff time are excluded. Maintenance estimate (not observed cost): 2–4 engineering hours/month for dependency updates/security checks, plus work driven by defects or new data. Public deployment is deferred: would need authentication, TLS, quotas, worker isolation, retention policy and an operating-cost quote. A local bounded tool is not a production multi-tenant service.

## Interview guide and next evidence

1. Describe the last pick/pack staffing decision, deadline, decision owner and consequence.
2. Which constraints could you actually change: people, roles, hours, breaks, stations?
3. What do WMS start/complete events mean? Can a task pause or span shifts?
4. How do waves, batch sizes, SKU mix, travel, congestion and shared workers change service?
5. What is the current spreadsheet/tool, and where does it fail?
6. Which metric would justify a trial, and what deterioration is unacceptable?
7. Can we obtain authorized event and roster data with observation windows and backlog?
8. What evidence would you require before acting? Who could authorize a controlled pilot?

No outreach sent. Next: 5–8 interviews across at least two operations; obtain one consented, semantically documented dataset; pre-register a temporal validation and monitored intervention plan. Counts are proposed research targets, not completed research.
