# Verification record

Local checks executed 2026-09-16–17 on Windows 11, Python 3.12.14. This is a synthetic research prototype. The code, tests and locked dependencies in this revision define the tested candidate.

| Gate | Status | Executed evidence |
|---|---|---|
| G1 | PASS | Built sdist and wheel with `python -m build --no-isolation`; installed runtime locks and wheel into separate `.venv-clean`. From `scratch/clean-smoke`, ran installed `demo`, `replay`, `run`, `inspect`, and `pip check`. Started installed Waitress server on 127.0.0.1:8765 and loaded packaged assets. |
| G2 | PASS | `ruff check .`: all checks passed; `ruff format --check .`: 25 files formatted; `mypy --cache-dir=nul`: no issues in 7 application source files. Build passed. |
| G3–G5 | PASS | `pytest -q --tb=short -p no:cacheprovider`: **49 passed in 13.07 s**. Includes invalid data/types/limits, hand calculations, independent heap scheduler, cutoff/break/resource conservation, infeasible default, feasible low demand, independent evaluation, intervals, HTML escaping and deterministic replay. |
| G6 | PASS | Actual in-app browser: empty CSV gives schema error; sample loads; inspect reports 132 arrivals, 115 completions and 17 unfinished; Enter/Space activate inspection, assumptions and comparison. Default shows no confirmed feasible option, all six allocations, independent evaluation and sensitivities. JSON and HTML direct-download events succeeded; console had no errors/warnings. Narrow responsive layout visually inspected; screenshot `browser-results.png`. Benchmark: default 2.19 s / 29.98 MiB, bounded maximum 39.39 s / 46.70 MiB; both below fixed limits. See `benchmark.json`. |
| G7 | PASS | `bandit -q -r src`: no findings after review of three deterministic `random.Random` usages (specific B311 suppressions; no security randomness). `pip_audit` found no known runtime dependency vulnerabilities; `dependency-audit.json`. Tracked-file secret scan passed. Runtime license metadata and notices reviewed; only original synthetic data redistributed. |
| G8 | PASS | README installation and CLI paths exercised; specification, architecture, research/dataset findings, limitations and requirement/test mapping reviewed. |
| G9 | PASS | Private staging commit `5a2299a5470317d4a44a7229d096d79ec704a4e5` passed [hosted CI](https://github.com/GarethMackenzie/operations-decision-lab/actions/runs/35194438651) before public visibility was enabled. Anonymous clone succeeded. A new Python 3.12 environment in that clone completed the README locked install, package install, demo, exact numerical replay and `pip check`; its server rendered the packaged interface on port 8766. Final release revision is recorded by annotated tag `v0.1.0` and its own hosted CI. |
| G10 | NOT APPLICABLE | No externally validated operational predictions. No authorized representative warehouse dataset, temporal holdout, customer interviews or intervention trial obtained. |

## Warehouse friction extension verification — 2026-09-22

The extension adds only local inputs that a user explicitly confirms. Its cited research context is documented in [research/WAREHOUSE_ISSUES.md](../research/WAREHOUSE_ISSUES.md); no survey percentage or other external figure supplies an app default.

| Check | Status | Executed evidence |
|---|---|---|
| Unit and integration | PASS | `pytest -q --tb=short -p no:cacheprovider`: **57 passed in 7.99 s**, including timed-adjustment arithmetic, safety-only prompts, invalid inputs and confirmation/export enforcement. |
| Static checks | PASS | `ruff check .`, `ruff format --check .`, and `mypy --cache-dir=nul` passed. |
| Security checks | PASS | `bandit -q -r src` and the tracked-file secret scan passed. `pip_audit --no-deps --disable-pip -r requirements-runtime.lock` reported no known vulnerabilities. |
| Package build | PASS | `python -m build --no-isolation` produced the source distribution and wheel; both include `decision_lab/friction.py`, the updated static assets, tests and warehouse-issues research note. |
| In-app workflow | PASS | Loaded the synthetic sample; supplied confirmed local delays, exception/rework rates and a manual-handling flag; ran the comparison. The results showed 6.00 → 9.00 min picking and 7.00 → 7.40 min packing, the separate adjusted capacity/result, safety prompt, follow-up actions and source links. Browser console had no warnings or errors. |

## Findings resolved during verification

- A hand-computed CI expectation was corrected to the independently calculated sample-variance result; the implementation did not change to fit the incorrect expectation.
- Windows pytest temporary/cache path problems were resolved with short parameter IDs and disabled local cache provider; normal pytest remains in Linux CI.
- Browser blob download events failed. Exports now use server-generated attachment responses for the same calculation, behind a random token. Only the latest report is kept in process memory, links expire after 10 minutes, and new comparisons replace them. Endpoint equality, invalid token and expiration are tested. Both formats were downloaded through the browser. One deliberately stale link failed after the session exceeded its lifetime; regenerating the comparison restored it.
- Earlier Windows sdist cleanup warnings did not prevent building; the final rebuild succeeded.

## Interpretation of the demonstration

Nominal capacity with two pickers and two packers is 17.142857 orders/hour, below demand of 18. The independent evaluation has mean unfinished work 14.7 orders and due-cohort SLA about 87.8%, with an approximate mean interval 79.7–96.0%. These are hypothetical Monte Carlo results conditional on the documented assumptions, not measured warehouse improvements. Finite-shift completion does not establish sustainable capacity.

## Limits of these checks

The secret scan checks specified token/key patterns, not all possible secrets. Dependency audit is a point-in-time advisory check. Browser testing covers the supplied in-app Chromium surface, not every browser or formal accessibility certification. Tests verify the specified model; they do not validate its applicability to a warehouse. Benchmark results depend on machine load. External datasets and upstream research code are not included.

## Release

[Public repository](https://github.com/GarethMackenzie/operations-decision-lab) · [v0.1.0 prototype release and downloadable demo](https://github.com/GarethMackenzie/operations-decision-lab/releases/tag/v0.1.0) · [hosted checks](https://github.com/GarethMackenzie/operations-decision-lab/actions/workflows/verify.yml).

The final follow-up changes record publication evidence and include its screenshot in the source distribution; application code is unchanged from the privately staged, tested revision. The tag is published only after the follow-up revision's hosted verification passes. Public source publication does not deploy a public application server.
