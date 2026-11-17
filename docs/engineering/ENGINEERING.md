# Engineering depth: explicit evidence, fail-closed releases

## Proposed structure

This is a blueprint. Keep the existing Decision Lab modules; introduce boundaries only when they solve a concrete maintenance problem.

```text
src/<package>/
  domain/              # Typed inputs, invariants and decision results; no I/O
  application/         # Orchestrates checks, simulation or evaluation
  adapters/            # Filesystem, database, CLI and web boundaries
  reporting/           # Stable serialized evidence and human-readable output
tests/
  unit/                # Hand calculations, boundaries and malformed inputs
  contract/            # CLI exit codes and serialized report compatibility
  integration/         # Real filesystem/database behavior and rollback
  regression/          # Minimal fixtures for actual fixed defects
  reference/           # Independent oracle for critical computations
docs/
  adr/                 # Decisions, alternatives, consequences, revisit triggers
  defects/             # Reproduction, root cause, fix and regression evidence
  images/              # Actual outputs, not fabricated performance graphics
evidence/
  manifest.json        # Version, hashes, assumptions, commands and results
```

Domain code returns explicit results; adapters translate failures to nonzero exit codes. A timeout, unsupported input or missing check must never become a clean audit. Persist complete evidence before release promotion. Classify logging fields so credentials and operational data cannot leak through exceptions.

## ADR template

```markdown
# ADR NNN: [decision]
Status: proposed / accepted / superseded / retrospective
Date and owner:
Context and measured constraints:
Decision:
Alternative A and why rejected:
Alternative B and why rejected:
Consequences, including costs:
Verification and evidence:
Revisit trigger:
Supersedes / superseded by:
```

## Complex defect resolution template

```markdown
# [Actual defect and affected versions]
Symptom and operational consequence:
Minimal input, command and observed output:
Expected invariant:
Root cause and why previous tests missed it:
Rejected fixes and their failure modes:
Smallest safe fix and commit:
Regression test that fails on the parent revision:
Independent oracle or hand calculation:
Affected data, repair and rollback:
Remaining limitations:
```

Do not describe hypothetical bugs as resolved incidents. For Decision Lab, investigate actual boundary defects using shift end, break overlap, unfinished work and resource conservation. For Release Gate, inspect malformed configuration, unreadable inputs and missing required checks.

## Executable Python example

[release_contract.py](examples/release_contract.py) implements a proposed evidence contract using only the standard library. It rejects missing, duplicate and unexpected checks; non-integer counts; unsupported outcomes; violations; and unknown execution states. PASS requires a nonempty evaluated population and zero violations. This prevents absent evidence from becoming an approval.

```python
from release_contract import CheckResult, require_release

require_release(
    frozenset({"FACT_UNIQUE"}),
    [CheckResult("FACT_UNIQUE", "PASS", examined=1200, violations=0)],
)
```

The numbers above are illustrative input, not portfolio measurements. A caller must convert `ReleaseBlocked` into a nonzero exit and retain the results. This contract cannot prove that a producer calculated its counts correctly; integration tests and independent queries supply that evidence. Empty datasets deliberately fail here. A legitimate empty partition needs a separately reviewed applicability policy, not an automatic PASS.

## PostgreSQL reconciliation example

Assumed schema: `expected_daily_totals(batch_id, expected_count, expected_amount)` contains exactly one control row per batch; `fact_claims(batch_id, claim_id, amount)` contains the loaded facts. Amounts use fixed-precision NUMERIC in the same currency and accounting basis. NULL identifiers/amounts are invalid. The query validates a single immutable batch; `%s` is a driver-bound parameter, never string interpolation.

```sql
WITH control AS (
    SELECT count(*) AS control_rows,
           min(expected_count) AS expected_count,
           min(expected_amount) AS expected_amount
    FROM expected_daily_totals
    WHERE batch_id = %s
), actual AS (
    SELECT count(*) AS actual_count,
           count(*) - count(DISTINCT claim_id) AS duplicate_or_null_ids,
           count(*) FILTER (WHERE amount IS NULL) AS null_amounts,
           coalesce(sum(amount), 0::numeric) AS actual_amount
    FROM fact_claims
    WHERE batch_id = %s
)
SELECT CASE
    WHEN control_rows <> 1 THEN 'ERROR'
    WHEN expected_count IS NULL OR expected_amount IS NULL THEN 'ERROR'
    WHEN expected_count <= 0 THEN 'ERROR'
    WHEN duplicate_or_null_ids > 0 OR null_amounts > 0 THEN 'FAIL'
    WHEN actual_count <> expected_count THEN 'FAIL'
    WHEN actual_amount <> expected_amount THEN 'FAIL'
    ELSE 'PASS'
END AS outcome,
control_rows, expected_count, actual_count,
expected_amount, actual_amount, duplicate_or_null_ids, null_amounts
FROM control CROSS JOIN actual;
```

Bind the same batch ID twice. Aggregation before joining prevents a duplicated control row from multiplying fact totals. Missing controls yield ERROR, including when facts are absent. Exact amount equality is intentional; introduce a tolerance only with a documented currency/rounding policy.

Run inside a repeatable-read transaction for consistent multi-query evidence. That snapshot alone does not prevent subsequent writes: freeze/version the batch, restrict write privileges, and validate/promote the same immutable version. On failure, roll back promotion and retain audit evidence separately. Do not infer approval from a swallowed SQL exception.

## Test strategy

| Risk | Test and independent expectation |
|---|---|
| No checks executed | Empty result set blocks release |
| Boolean accepted as integer | `True` for a count is rejected |
| Misleading PASS | Positive violation count blocks release |
| Forged or partial coverage | Duplicate, unexpected and missing IDs block release |
| Tool execution failed | ERROR and unknown outcomes block release |
| Zero-row false confidence | Empty evaluated population blocks release |
| Duplicate controls | SQL returns ERROR even when totals match |
| Missing controls and facts | SQL returns ERROR, not a vacuous PASS |
| Join multiplication | Duplicate control rows cannot inflate fact totals |
| Mutable load after validation | Integration test proves promotion uses the frozen version |

Python tests are included. PostgreSQL scenarios are an integration-test specification, not executed evidence. For production, add timeouts, evidence provenance, immutable batch identity, compatibility tests and CI on the supported database version.


## Run the illustrative contract tests

From the repository root:

```sh
python -m unittest discover -s docs/engineering/examples -p 'test_*.py' -v
```

These examples are independent of the production package. PostgreSQL integration tests remain outstanding.
