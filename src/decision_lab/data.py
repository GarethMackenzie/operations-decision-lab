"""Strict descriptive CSV inspection. No inferred service or automatic calibration."""

from __future__ import annotations

import csv
import hashlib
import io
from datetime import datetime
from statistics import mean
from typing import Any

MAX_BYTES = 2_000_000
MAX_ROWS = 5000
COLUMNS = {"order_id", "arrival_time", "pick_start", "pick_end", "pack_start", "pack_end"}
OPTIONAL = {"picker", "packer"}
TIMES = ("arrival_time", "pick_start", "pick_end", "pack_start", "pack_end")


def timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Observation bounds and timestamps must be ISO 8601 strings.")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError("Use ISO 8601 timestamps with a UTC offset.") from error
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timestamps need a timezone offset, for example +00:00.")
    return result


def inspect_csv(text: object, window_start: object, window_end: object) -> dict[str, Any]:
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("CSV must be UTF-8 text, at most 2 MB.")
    start, end = timestamp(window_start), timestamp(window_end)
    hours = (end - start).total_seconds() / 3600
    if not 0 < hours <= 24 * 366:
        raise ValueError("Observation window must be positive and at most 366 days.")
    try:
        reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")), strict=True)
        names = reader.fieldnames or []
        if len(names) != len(set(names)) or not COLUMNS <= set(names):
            raise ValueError("CSV needs unique headers: " + ", ".join(sorted(COLUMNS)))
        if set(names) - COLUMNS - OPTIONAL:
            raise ValueError("Unsupported CSV columns. Use only the documented schema.")
        raw_rows: list[dict[str, str]] = []
        for row in reader:
            if len(raw_rows) >= MAX_ROWS:
                raise ValueError("CSV exceeds the 5,000-order limit.")
            if None in row or any(v is None for v in row.values()):
                raise ValueError("CSV row has the wrong number of fields.")
            raw_rows.append(row)
    except csv.Error as error:
        raise ValueError("Malformed CSV or field too large.") from error
    if not raw_rows:
        raise ValueError("CSV contains no orders.")
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    missing_starts = 0
    censored_events = 0
    for index, raw in enumerate(raw_rows, 2):
        identifier = raw["order_id"].strip()
        if not identifier or len(identifier) > 128 or identifier in seen:
            raise ValueError(
                f"Row {index}: order_id must be unique, nonempty and <=128 characters."
            )
        seen.add(identifier)
        parsed = {key: timestamp(raw[key].strip()) if raw[key].strip() else None for key in TIMES}
        arrival = parsed["arrival_time"]
        if arrival is None or arrival >= end:
            raise ValueError(f"Row {index}: arrival_time is required and must precede window end.")
        known = [value for value in parsed.values() if value is not None]
        if any(a > b for a, b in zip(known, known[1:], strict=False)):
            raise ValueError(f"Row {index}: timestamps are out of process order.")
        for stage in ("pick", "pack"):
            a, b = parsed[stage + "_start"], parsed[stage + "_end"]
            if a is not None and b is not None and a == b:
                raise ValueError(f"Row {index}: recorded stage durations must be positive.")
            if b is not None and a is None:
                missing_starts += 1
        if (parsed["pack_start"] is not None or parsed["pack_end"] is not None) and parsed[
            "pick_end"
        ] is None:
            raise ValueError(f"Row {index}: packing requires a recorded picking completion.")
        # Discard future evidence at the observation boundary, keeping its count visible.
        for key in TIMES[1:]:
            endpoint = parsed[key]
            if endpoint is not None and endpoint > end:
                parsed[key] = None
                censored_events += 1
        rows.append(
            {
                **parsed,
                "picker": raw.get("picker", "").strip(),
                "packer": raw.get("packer", "").strip(),
            }
        )
    cohort = [r for r in rows if r["arrival_time"] >= start]
    completed = [r for r in cohort if r["pack_end"] is not None]
    arrivals = len(cohort)
    backlog = [
        r
        for r in rows
        if r["arrival_time"] < start and (r["pack_end"] is None or r["pack_end"] > start)
    ]
    completions = sum(r["pack_end"] is not None and start <= r["pack_end"] <= end for r in rows)
    means = {}
    overlaps = 0
    missing_resources = 0
    by_resource: dict[str, list[tuple[datetime, datetime]]] = {}
    stage_workers: dict[str, set[str]] = {"pick": set(), "pack": set()}
    for stage, resource in (("pick", "picker"), ("pack", "packer")):
        intervals = [
            (r[stage + "_start"], r[stage + "_end"], r[resource])
            for r in rows
            if r[stage + "_start"] is not None
            and r[stage + "_end"] is not None
            and r[stage + "_start"] >= start
        ]
        means[stage] = (
            mean((b - a).total_seconds() / 60 for a, b, _ in intervals) if intervals else None
        )
        for a, b, who in intervals:
            if not who:
                missing_resources += 1
            else:
                by_resource.setdefault(who, []).append((a, b))
                stage_workers[stage].add(who)
    for spans in by_resource.values():
        latest = None
        for a, b in sorted(spans):
            if latest is not None and a < latest:
                overlaps += 1
            latest = max(latest, b) if latest else b
    shared_workers = len(stage_workers["pick"] & stage_workers["pack"])
    warnings = [
        "Observed intervals are elapsed processing time, not proven active labor.",
        "Calendars, pauses, task mix and dedicated staffing are not established by this CSV.",
        "Cycle statistics use completed arrival-cohort orders and can be biased by censoring.",
    ]
    unfinished = arrivals - len(completed)
    if missing_starts:
        warnings.append(
            "Completion-only stages: service time is unknown. Supply explicit assumptions."
        )
    if unfinished or censored_events:
        warnings.append(
            "Incomplete or future stages are censored at observation end; no duration imputation."
        )
    if overlaps:
        warnings.append(
            "Overlapping work for a worker conflicts with the dedicated single-task model."
        )
    if backlog:
        warnings.append(
            "Pre-window work exists. Enter initial stage queues explicitly; "
            "ages are not reconstructed."
        )
    if shared_workers:
        warnings.append(
            "Workers appear in both roles; the dedicated staffing model is unsupported."
        )
    if missing_resources:
        warnings.append("Missing worker IDs prevent a complete overlap audit.")
    cycles = [(r["pack_end"] - r["arrival_time"]).total_seconds() / 60 for r in completed]
    eligible = (
        arrivals >= 10
        and len(completed) == arrivals
        and not backlog
        and not missing_starts
        and not overlaps
        and not shared_workers
        and not censored_events
        and not missing_resources
        and all(value is not None for value in means.values())
    )
    return {
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "rows": len(rows),
        "window_hours": hours,
        "arrivals_in_window": arrivals,
        "initial_wip": len(backlog),
        "completions_in_window": completions,
        "unfinished_arrival_cohort": unfinished,
        "arrival_rate_observed": arrivals / hours,
        "throughput_observed": completions / hours,
        "completed_cycle_mean": mean(cycles) if cycles else None,
        "elapsed_interval_means": means,
        "missing_starts": missing_starts,
        "overlap_count": overlaps,
        "shared_workers": shared_workers,
        "missing_resources": missing_resources,
        "future_endpoints_censored": censored_events,
        "eligible_for_attested_intervals": eligible,
        "warnings": warnings,
    }
