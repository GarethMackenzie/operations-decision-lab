"""Scenario selection, independent evaluation and assumption sensitivity."""

from __future__ import annotations

import math
from dataclasses import replace
from statistics import mean, stdev
from typing import Any

from .model import REPLICATIONS, Config, capacity, simulate, workload

METRICS = (
    "completed",
    "unfinished",
    "sla_fraction",
    "completed_cycle_mean",
    "completed_cycle_p95",
    "throughput_per_hour",
    "pick_utilization",
    "pack_utilization",
    "pick_mean_queue",
    "pack_mean_queue",
)
T_29 = 2.045229642132703


def interval(values: list[float | None]) -> dict[str, Any]:
    numeric = [float(v) for v in values if v is not None]
    if not numeric:
        return {"mean": None, "low": None, "high": None, "n": 0}
    avg = mean(numeric)
    # Exactly 30 independent replications required for inferential intervals.
    if len(numeric) != REPLICATIONS:
        return {"mean": avg, "low": None, "high": None, "n": len(numeric)}
    half = T_29 * stdev(numeric) / math.sqrt(len(numeric))
    return {"mean": avg, "low": avg - half, "high": avg + half, "n": len(numeric)}


def evaluate(config: Config, pickers: int, packers: int, seeds: list[int]) -> dict[str, Any]:
    runs = []
    trace: list[dict[str, Any]] = []
    for seed in seeds:
        run = simulate(config, pickers, packers, workload(config, seed))
        first_trace = run.pop("trace")
        if not trace:
            trace = first_trace
        runs.append({"seed": seed, **run})
    stats = {key: interval([run[key] for run in runs]) for key in METRICS}
    screen = capacity(config, pickers, packers)
    low = stats["sla_fraction"]["low"]
    service_pass = low is not None and low >= config.target_fraction
    reasons = []
    if not screen["stable"]:
        reasons.append("Demand meets or exceeds nominal capacity.")
    elif not screen["capacity_pass"]:
        reasons.append("Utilization exceeds the chosen safety ceiling.")
    if not screen["budget_pass"]:
        reasons.append("Scheduled payroll exceeds budget.")
    if not service_pass:
        reasons.append("Due-cohort service target not supported by the lower confidence bound.")
    return {
        "pickers": pickers,
        "packers": packers,
        **screen,
        "stats": stats,
        "feasible": not reasons,
        "reasons": reasons,
        "runs": runs,
        "trace": trace,
    }


def compare(config: Config) -> dict[str, Any]:
    config.validate()
    selection_seeds = [config.seed + i for i in range(REPLICATIONS)]
    evaluation_seeds = [config.seed + 1_000_000 + i for i in range(REPLICATIONS)]
    scenarios = []
    for total in range(2, config.max_workers + 1):
        for pickers in range(1, total):
            result = evaluate(config, pickers, total - pickers, selection_seeds)
            result.pop("trace")
            scenarios.append(result)
    feasible = [s for s in scenarios if s["feasible"]]
    if feasible:
        selected = min(
            feasible,
            key=lambda s: (s["payroll"], -s["stats"]["sla_fraction"]["mean"], s["pickers"]),
        )
    else:
        selected = min(
            scenarios,
            key=lambda s: (
                -(s["stats"]["sla_fraction"]["mean"] or 0),
                s["stats"]["unfinished"]["mean"],
                s["payroll"],
            ),
        )
    checked = evaluate(config, selected["pickers"], selected["packers"], evaluation_seeds)
    confirmed = bool(feasible) and checked["feasible"]
    baseline = evaluate(config, config.baseline_pickers, config.baseline_packers, evaluation_seeds)
    sensitivities = []
    for label, changed in (
        ("Arrivals +20%", replace(config, arrival_rate=min(60, config.arrival_rate * 1.2))),
        (
            "Service means +20%",
            replace(
                config,
                pick_minutes=min(60, config.pick_minutes * 1.2),
                pack_minutes=min(60, config.pack_minutes * 1.2),
            ),
        ),
        ("Service CV at least 1", replace(config, service_cv=max(1.0, config.service_cv))),
    ):
        result = evaluate(
            changed,
            selected["pickers"],
            selected["packers"],
            [config.seed + 2_000_000 + i for i in range(REPLICATIONS)],
        )
        result.pop("trace")
        sensitivities.append(
            {
                "label": label + " (capped at supported limits)",
                "arrival_rate": changed.arrival_rate,
                "pick_minutes": changed.pick_minutes,
                "pack_minutes": changed.pack_minutes,
                "service_cv": changed.service_cv,
                **result,
            }
        )
    return {
        "status": "CONDITIONALLY FEASIBLE" if confirmed else "NO CONFIRMED FEASIBLE OPTION",
        "selection_status": "candidate passed selection"
        if feasible
        else "no feasible option in selection",
        "selected_allocation": {"pickers": selected["pickers"], "packers": selected["packers"]},
        "confirmed_feasible": confirmed,
        "selection_seeds": selection_seeds,
        "evaluation_seeds": evaluation_seeds,
        "scenarios": scenarios,
        "evaluation": checked,
        "baseline": baseline,
        "sensitivity": sensitivities,
        "interval_method": "95% Student-t interval for a replication mean, df=29, n=30. "
        "Approximate Monte Carlo uncertainty only; "
        "not a prediction interval or input/model uncertainty. "
        "Missing due cohorts suppress the SLA confidence interval and cannot pass the target.",
    }
