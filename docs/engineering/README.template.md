# [REQUIRED: project name]

**[REQUIRED: one sentence naming the user, operational problem and useful output].**

**Business question:** [REQUIRED: one answerable question, including the relevant constraint].

> [!IMPORTANT]
> **Decision supported**
> **Owner:** [role]. **Action:** [specific action]. **Evidence:** [output and acceptance threshold].
> **Stop condition:** [when the system refuses to recommend or requires review].

**Status:** [prototype / evaluated pilot / production]. **Data:** [public / synthetic / permitted operational]. **Impact:** [measured with evidence link / not yet measured].

## See the result

| Visual | Required content | Caption must establish |
|---|---|---|
| Primary screenshot | Main decision, constraints and result | Dataset, version, whether synthetic |
| Failure screenshot | Invalid input or no feasible option | Why action was withheld and the next step |
| Architecture diagram | Inputs → validation → computation → output | Trust boundaries and persistence |

<!-- Add real assets before enabling image links:
![Decision output and its constraints](docs/images/decision.png)
![Refused recommendation and explanation](docs/images/failure.png)
-->

Do not present decorative charts as measured results. Supply meaningful alt text and redact operational identifiers.

## Reproduce one decision

```sh
# [REQUIRED: supported environment, installation and one runnable command]
```

Expected result: [artifact, exit status, or documented outcome]. Record the input checksum, commit, dependency lock and assumptions. Explain how to reproduce a failure as well as a successful run.

## Architecture and decisions

| Decision | Chosen approach | Rejected alternative | Cost accepted | Revisit trigger |
|---|---|---|---|---|
| [REQUIRED: meaningful choice] | [implementation] | [credible alternative and reason] | [specific limitation] | [measurable condition] |

Link each row to a dated ADR. Mark retrospective explanations as retrospective; do not invent historical deliberations.

## Evidence and limitations

- **Correctness:** [independent oracle, invariant tests, adversarial fixtures].
- **Reproducibility:** [replay command, input/version manifest].
- **Operational evaluation:** [case study and underlying evidence, or not evaluated].
- **Known failure modes:** [unsupported conditions and their observable behavior].
- **Ownership:** [maintainer, support scope, release process].

## Measured impact

[REQUIRED: link to an observed evaluation, or state “External impact has not been measured.”]

Distinguish synthetic demonstrations, retrospective backtests, shadow-mode observations and live interventions. Include denominators, uncertainty and costs with every outcome claim.

## Development and release

[REQUIRED: setup, checks, supported versions, release policy, license and contribution links].
