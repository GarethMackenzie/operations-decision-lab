# Picking and packing staffing — external evaluation protocol

**Status: measurement protocol; no external results recorded.**

Owner: [REQUIRED]. Reviewer: [REQUIRED]. Evaluation version: [REQUIRED]. Registration date: [REQUIRED]. Code commit and environment lock: [REQUIRED].

## 1. Executive result

Complete this section last.

> For [population] during [dates], [intervention] changed [primary metric] from [baseline, denominator] to [evaluation, denominator]. The estimated effect was [absolute change, relative change, uncertainty]. The design supports [association / prediction performance / causal effect with justification]. [Failures and unresolved limitations].

If evaluation has not happened, retain: **External impact has not been measured.**

## 2. Operational problem and baseline metrics

**Decision owner:** [role and authority]. **Recurring decision:** [action and frequency]. **Constraint:** [capacity, cost, risk or service limit]. **Cost of an incorrect decision:** [observable consequence].

Describe the existing workflow and why its output is insufficient. Do not use tool adoption as a substitute for a business outcome.

| Metric | Exact definition | Baseline window | Numerator / denominator | Value | Evidence |
|---|---|---|---|---|---|
| Primary outcome | [one preregistered definition] | [UTC start/end] | [counts] | Not measured | [artifact] |
| Turnaround | [start/end events; median and p90] | [window] | [eligible/completed/censored] | Not measured | [artifact] |
| Error rate | [adjudicated defects / eligible opportunities] | [window] | [counts] | Not measured | [artifact] |
| Guardrail | [SLA, escaped defects, or other harm] | [window] | [counts] | Not measured | [artifact] |
| Resource cost | [paid hours, infrastructure and review cost] | [window] | [units] | Not measured | [artifact] |

Specify timezone, observation cutoff, missingness, duplicates, exclusions, reopened cases and unfinished work. Completed-only cycle time must not conceal unfinished cases. Describe population changes across periods.

## 3. Evaluation contract

- **Design:** [shadow mode / randomized pilot / matched comparison / before-after]. Explain what the design can establish.
- **Unit:** [order, shift, release candidate, or repository]. Identify clustering and repeated observations.
- **Eligibility and exclusions:** [rules fixed before inspecting results].
- **Sample plan:** [effect of practical interest, variance assumptions, sample-size justification, fixed duration].
- **Primary hypothesis:** [metric, direction and minimum useful effect].
- **Guardrails and stopping rules:** [threshold, escalation owner and action].
- **Holdout:** [temporal boundary; training/tuning data cannot cross it].
- **Comparator:** [existing workflow plus a simple baseline].
- **Adjudication:** [independent reviewer, rubric, disagreement resolution; blinding where feasible].
- **Analysis:** [uncertainty method consistent with the design; cluster at shift/repository if required].
- **Permission:** [documented data access and operational approval].

For Release Gate: label both flagged and unflagged cases to estimate missed defects. Include false-positive review time and tool failures. Avoid comparing a new gate only against defects it already detects.

For Decision Lab: first test prediction calibration on held-out shifts. Shadow mode cannot show that staffing changes improved outcomes. A live intervention requires a separate approval and evaluation contract.

## 4. Initial approach and why it failed

| Hypothesis | Observed failure | Minimal reproduction | Operational consequence | Evidence |
|---|---|---|---|---|
| [initial belief] | [observed behavior, not speculation] | [input + command + commit] | [affected users/cases] | [artifact] |

Classify each failure: **input defect**, **implementation defect**, **invalid modeling assumption**, **legitimate infeasibility**, or **workflow mismatch**.

**Illustrative edge case, not an external incident:** Decision Lab's documented four-worker example cannot sustain 18 orders/hour under its declared service times. “No confirmed feasible option” is a correct model response. The failed assumption would be that a feasible allocation must exist; do not describe the refusal itself as a software bug.

Record root cause, blast radius, how detection occurred, and why previous controls missed it. A retrospective narrative must link to contemporaneous evidence or acknowledge its absence.

## 5. Pivot and engineering intervention

**Change:** [specific behavior]. **Mechanism:** [why it should affect the metric]. **Alternative rejected:** [credible option and downside]. **Cost accepted:** [latency, dependency, complexity or reduced scope].

| Change | Commit / ADR | Regression evidence | Rollout and rollback |
|---|---|---|---|
| [intervention] | [links] | [test that fails before and passes after] | [owner and trigger] |

Version revised assumptions. Do not tune against the held-out period and continue calling it a holdout. Retain failed experiments and explain protocol deviations.

## 6. Final measured impact

| Outcome | Baseline | Evaluation | Absolute change | Relative change | Uncertainty | Sample / evidence |
|---|---|---|---|---|---|---|
| Primary | Not measured | Not measured | — | — | — | — |
| Guardrail | Not measured | Not measured | — | — | — | — |
| Review workload | Not measured | Not measured | — | — | — | — |
| Tool/model failures | Not measured | Not measured | — | — | — | — |

For a lower-is-better metric: absolute reduction = baseline − evaluation. Relative reduction = (baseline − evaluation) / baseline × 100%; undefined when baseline is zero. Rate differences must be labeled **percentage points**, separately from relative percentages.

Report effect sizes and uncertainty, not just significance. Include negative results, excluded observations and guardrail deterioration. Identify seasonality, demand mix, staffing and other concurrent changes. A before-after comparison alone does not establish causation.

## 7. Quantifiable ROI

Use the same observation horizon for benefits and costs. Report the currency and valuation date.

```text
Capacity released (hours) = eligible volume × observed minutes saved per unit / 60
Modeled labor value = capacity released × documented loaded hourly cost
Realized financial benefit = documented incremental cash benefit or avoided spend
Total cost = build + integration + training + operation + review + maintenance
Net benefit = realized financial benefit − total cost
ROI (%) = net benefit / total cost × 100, only when total cost > 0
```

Hours released are not cash savings unless they produce documented avoided spend or incremental value. Do not count the same labor saving and throughput benefit twice. Do not annualize a short pilot without stating the extrapolation and seasonality assumptions.

| Item | Quantity | Unit cost | Amount | Observed or modeled | Evidence |
|---|---|---|---|---|---|
| Benefit | Not measured | — | — | — | — |
| Cost | Not measured | — | — | — | — |

Report conservative/base/optimistic scenarios only for explicitly modeled components. If monetary benefits cannot be demonstrated, publish operational results and label ROI **not established**.

## 8. Evidence manifest and reproducibility

| Artifact | Version/checksum | Access | Purpose |
|---|---|---|---|
| Approved protocol | [hash] | [public/restricted] | Prevent retrospective metric selection |
| Data dictionary and cohort query | [commit] | [access] | Define inclusion and semantics |
| Immutable input snapshot | [SHA-256] | [access] | Reproduce the observation |
| Analysis and dependency lock | [commit/hash] | [access] | Recompute results |
| Raw evaluation outputs | [hash] | [access] | Inspect failures and variance |
| Reviewer sign-off | [dated record] | [access] | Establish independent review |

Provide exact execution commands, random seeds, runtime versions and expected outputs. Publish permitted aggregates or synthetic reproductions when raw data cannot be shared; state what an external reviewer cannot independently verify.

## 9. Decision, limitations and next test

**Decision:** [adopt / revise / stop / gather more evidence]. **Reason:** [results against preregistered criteria]. **Unresolved risks:** [specific conditions]. **Next falsifiable test:** [hypothesis and acceptance threshold].

Publication checklist: every numerical claim traces to evidence; observed and simulated results are separated; failed cases remain visible; permissions are recorded; an independent reviewer checked definitions and calculations.
