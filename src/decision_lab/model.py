"""Bounded FIFO, dedicated-resource, two-stage shift model.

Time is minutes from shift opening. No drain, overtime, carryover or implicit
calendars. Work pauses during a synchronized break, keeping its resource.
"""

from __future__ import annotations

import math
import random
from collections.abc import Generator
from dataclasses import asdict, dataclass, fields
from statistics import mean
from typing import Any

import simpy

MAX_JOBS = 2000
REPLICATIONS = 30


@dataclass(frozen=True)
class Config:
    arrival_rate: float = 18.0
    pick_minutes: float = 6.0
    pack_minutes: float = 7.0
    service_cv: float = 0.5
    shift_hours: float = 8.0
    break_minutes: float = 0.0
    initial_pick: int = 0
    initial_pack: int = 0
    max_workers: int = 4
    baseline_pickers: int = 2
    baseline_packers: int = 2
    hourly_wage: float = 100.0
    payroll_budget: float = 4800.0
    sla_minutes: float = 60.0
    target_fraction: float = 0.9
    utilization_ceiling: float = 0.9
    seed: int = 42

    def validate(self) -> None:
        limits = {
            "arrival_rate": (0.1, 60),
            "pick_minutes": (0.1, 60),
            "pack_minutes": (0.1, 60),
            "service_cv": (0, 2),
            "shift_hours": (2, 12),
            "break_minutes": (0, 60),
            "initial_pick": (0, 100),
            "initial_pack": (0, 100),
            "max_workers": (2, 6),
            "baseline_pickers": (1, 6),
            "baseline_packers": (1, 6),
            "hourly_wage": (0, 10000),
            "payroll_budget": (0, 1000000),
            "sla_minutes": (1, 240),
            "target_fraction": (0.5, 1),
            "utilization_ceiling": (0.1, 1),
            "seed": (0, 1000000),
        }
        integers = {
            "initial_pick",
            "initial_pack",
            "max_workers",
            "baseline_pickers",
            "baseline_packers",
            "seed",
        }
        for name, (low, high) in limits.items():
            value = getattr(self, name)
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not low <= value <= high
            ):
                raise ValueError(f"{name} must be a finite number from {low} to {high}.")
            if name in integers and type(value) is not int:
                raise ValueError(f"{name} must be an integer.")
        if self.sla_minutes >= self.shift_hours * 60:
            raise ValueError("SLA must be shorter than the shift, so a due cohort exists.")
        if self.baseline_pickers + self.baseline_packers > 6:
            raise ValueError("Baseline may use at most six workers.")

    @classmethod
    def parse(cls, raw: Any) -> Config:
        if not isinstance(raw, dict):
            raise ValueError("Configuration must be a JSON object.")
        unknown = set(raw) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError("Unknown configuration fields: " + ", ".join(sorted(unknown)))
        result = cls(**raw)
        result.validate()
        return result


@dataclass(frozen=True)
class Job:
    arrival: float
    pick: float
    pack: float
    initial_stage: str = "new"


def workload(config: Config, seed: int) -> list[Job]:
    """Independent arrival/service streams and scenario-independent service draws."""
    # Deterministic simulation draws, never credentials or security decisions.
    arrivals = random.Random(seed)  # nosec B311
    picking = random.Random(seed + 10_000_019)  # nosec B311
    packing = random.Random(seed + 20_000_033)  # nosec B311
    sigma = math.sqrt(math.log1p(config.service_cv**2))

    def duration(rng: random.Random, avg: float) -> float:
        return avg if sigma == 0 else rng.lognormvariate(math.log(avg) - sigma**2 / 2, sigma)

    jobs = []
    for stage, count in (("pick", config.initial_pick), ("pack", config.initial_pack)):
        for _ in range(count):
            jobs.append(
                Job(
                    0,
                    duration(picking, config.pick_minutes),
                    duration(packing, config.pack_minutes),
                    stage,
                )
            )
    at = arrivals.expovariate(config.arrival_rate / 60)
    while at < config.shift_hours * 60:
        if len(jobs) >= MAX_JOBS:
            raise ValueError("Generated workload exceeds the 2,000-job limit; reduce demand.")
        jobs.append(
            Job(at, duration(picking, config.pick_minutes), duration(packing, config.pack_minutes))
        )
        at += arrivals.expovariate(config.arrival_rate / 60)
    return jobs


def calendar(config: Config) -> tuple[float, float, float]:
    end = config.shift_hours * 60
    begin_break = end / 2
    return end, begin_break, begin_break + config.break_minutes


def active_time(start: float, end: float, config: Config) -> float:
    cutoff, b0, b1 = calendar(config)
    end = min(end, cutoff)
    if end <= start:
        return 0.0
    return end - start - max(0.0, min(end, b1) - max(start, b0))


def simulate(config: Config, pickers: int, packers: int, jobs: list[Job]) -> dict[str, Any]:
    """All events at cutoff are processed; later completions remain unfinished."""
    config.validate()
    if type(pickers) is not int or type(packers) is not int or min(pickers, packers) < 1:
        raise ValueError("Each stage requires a positive integer worker count.")
    if pickers + packers > 6 or len(jobs) > MAX_JOBS:
        raise ValueError("Simulation worker/job bound exceeded.")
    cutoff, b0, b1 = calendar(config)
    for job in jobs:
        if (
            job.initial_stage not in {"new", "pick", "pack"}
            or not all(math.isfinite(x) for x in (job.arrival, job.pick, job.pack))
            or not 0 <= job.arrival < cutoff
            or min(job.pick, job.pack) <= 0
            or (job.initial_stage != "new" and job.arrival != 0)
        ):
            raise ValueError("Invalid workload job.")
    env = simpy.Environment()
    resources = {
        "pick": simpy.Resource(env, capacity=pickers),
        "pack": simpy.Resource(env, capacity=packers),
    }
    rows: list[dict[str, Any]] = []

    def stage(row: dict[str, Any], name: str, duration: float) -> Generator:
        row[name + "_ready"] = float(env.now)
        with resources[name].request() as request:
            yield request
            start = float(env.now)
            if b0 <= start < b1:
                yield env.timeout(b1 - start)
                start = b1
            row[name + "_start"] = start
            finish = start + duration
            if start < b0 < finish:
                finish += config.break_minutes
            row[name + "_planned_end"] = finish
            yield env.timeout(finish - float(env.now))
            row[name + "_end"] = float(env.now)

    def process(job: Job, row: dict[str, Any]) -> Generator:
        yield env.timeout(job.arrival)
        if job.initial_stage != "pack":
            yield from stage(row, "pick", job.pick)
        yield from stage(row, "pack", job.pack)

    for i, job in enumerate(sorted(jobs, key=lambda j: j.arrival)):
        row = {"id": i, "arrival": job.arrival, "initial_stage": job.initial_stage}
        rows.append(row)
        env.process(process(job, row))
    while env.peek() <= cutoff:
        env.step()

    completed = [r for r in rows if "pack_end" in r]
    new = [r for r in rows if r["initial_stage"] == "new"]
    due = [r for r in new if r["arrival"] + config.sla_minutes <= cutoff]
    on_time = [r for r in due if r.get("pack_end", math.inf) <= r["arrival"] + config.sla_minutes]
    cycles = [r["pack_end"] - r["arrival"] for r in completed if r["initial_stage"] == "new"]
    result: dict[str, Any] = {
        "arrivals": len(new),
        "initial_backlog": len(rows) - len(new),
        "completed": len(completed),
        "unfinished": len(rows) - len(completed),
        "due_orders": len(due),
        "on_time_due": len(on_time),
        "sla_fraction": len(on_time) / len(due) if due else None,
        "completed_cycle_mean": mean(cycles) if cycles else None,
        "completed_cycle_p95": sorted(cycles)[math.ceil(0.95 * len(cycles)) - 1]
        if cycles
        else None,
        "throughput_per_hour": len(completed) / config.shift_hours,
    }
    for name, staff in (("pick", pickers), ("pack", packers)):
        result[name + "_utilization"] = sum(
            active_time(r[name + "_start"], r[name + "_planned_end"], config)
            for r in rows
            if name + "_start" in r
        ) / (staff * (cutoff - config.break_minutes))
        result[name + "_mean_queue"] = (
            sum(
                min(r.get(name + "_start", cutoff), cutoff) - r[name + "_ready"]
                for r in rows
                if name + "_ready" in r
            )
            / cutoff
        )
        result[name + "_queued_at_close"] = sum(
            name + "_ready" in r and name + "_start" not in r for r in rows
        )
        result[name + "_busy_at_close"] = sum(
            name + "_start" in r and name + "_end" not in r for r in rows
        )
    result["trace"] = rows
    return result


def capacity(config: Config, pickers: int, packers: int) -> dict[str, Any]:
    fraction = 1 - config.break_minutes / (config.shift_hours * 60)
    picking = pickers * 60 / config.pick_minutes * fraction
    packing = packers * 60 / config.pack_minutes * fraction
    rho = max(config.arrival_rate / picking, config.arrival_rate / packing)
    payroll = (pickers + packers) * config.shift_hours * config.hourly_wage
    return {
        "pick_capacity": picking,
        "pack_capacity": packing,
        "capacity_per_hour": min(picking, packing),
        "max_nominal_utilization": rho,
        "stable": rho < 1,
        "capacity_pass": rho < 1 and rho <= config.utilization_ceiling,
        "bottleneck": "picking"
        if picking < packing
        else "packing"
        if packing < picking
        else "balanced",
        "payroll": payroll,
        "budget_pass": payroll <= config.payroll_budget,
        "marginal_payroll": payroll
        - (config.baseline_pickers + config.baseline_packers)
        * config.shift_hours
        * config.hourly_wage,
    }


def config_dict(config: Config) -> dict[str, Any]:
    return asdict(config)
