"""Reproducible JSON input/results and escaped self-contained HTML export."""

from __future__ import annotations

import hashlib
import html
import json
import platform
from importlib.metadata import version
from typing import Any

from . import __version__
from .analysis import compare
from .data import inspect_csv
from .model import Config, config_dict

LIMITATIONS = [
    "Hypothetical research prototype. "
    "No externally validated prediction or staffing recommendation.",
    "Poisson arrivals; independent lognormal service; "
    "homogeneous dedicated workers; FIFO; no batching or sharing.",
    "One shift only. Work pauses over the common midpoint break. No overtime or queue drain.",
    "Initial backlog is queued at the stated stage at time zero; "
    "prior age and in-service work are unsupported.",
    "Service target uses only new orders whose SLA deadline falls within the shift. "
    "Younger orders are excluded.",
    "Completed-only cycle statistics exclude unfinished work "
    "and can look optimistic under overload.",
    "Nominal capacity is a necessary sustained-load screen, "
    "not evidence of long-run or real-world performance.",
    "Payroll covers every scheduled worker-hour, including breaks/idle time, "
    "in user-defined currency units.",
    "No overtime, revenue, penalties or causal savings are calculated. "
    "Marginal payroll is relative to the baseline.",
    "Confidence intervals describe replication means conditional on assumptions; "
    "sensitivity is not validation.",
    "Exports contain the exact input CSV. Review before sharing; "
    "uploaded data is held in memory only.",
]


def canonical(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def make_report(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("Request must be a JSON object.")
    allowed = {
        "csv",
        "window_start",
        "window_end",
        "config",
        "assumptions_confirmed",
        "service_source",
        "active_service_confirmed",
        "data_origin",
    }
    if set(request) - allowed:
        raise ValueError("Unsupported request fields.")
    if request.get("assumptions_confirmed") is not True:
        raise ValueError("Confirm the hypothetical model assumptions before comparing.")
    source = request.get("service_source", "manual")
    if not isinstance(source, str) or source not in {"manual", "attested_intervals"}:
        raise ValueError("Service source must be manual or attested_intervals.")
    origin = request.get("data_origin", "user-provided; provenance unverified")
    if not isinstance(origin, str) or origin not in {
        "synthetic demo",
        "user-provided; provenance unverified",
    }:
        raise ValueError("Unsupported data-origin label.")
    config = Config.parse(request.get("config", {}))
    quality = inspect_csv(
        request.get("csv"), request.get("window_start"), request.get("window_end")
    )
    if source == "attested_intervals":
        if (
            request.get("active_service_confirmed") is not True
            or not quality["eligible_for_attested_intervals"]
        ):
            raise ValueError(
                "Observed interval adoption requires complete eligible data "
                "and active-service confirmation."
            )
        for stage in ("pick", "pack"):
            if (
                abs(getattr(config, stage + "_minutes") - quality["elapsed_interval_means"][stage])
                > 1e-6
            ):
                raise ValueError(
                    "Adopted service means must match the inspected intervals exactly."
                )
    inputs = {
        "csv": request["csv"],
        "window_start": request["window_start"],
        "window_end": request["window_end"],
        "config": config_dict(config),
        "assumptions_confirmed": True,
        "service_source": source,
        "active_service_confirmed": request.get("active_service_confirmed") is True,
        "data_origin": origin,
    }
    return {
        "schema_version": 1,
        "model_version": __version__,
        "evidence_class": "HYPOTHETICAL — NOT EXTERNALLY VALIDATED",
        "input_sha256": hashlib.sha256(canonical(inputs).encode()).hexdigest(),
        "inputs": inputs,
        "data_quality": quality,
        "results": compare(config),
        "limitations": LIMITATIONS,
        "environment": {
            "python": platform.python_version(),
            **{name: version(name) for name in ("simpy", "Flask", "waitress")},
        },
    }


def report_html(report: dict[str, Any]) -> str:
    results = report["results"]
    rows = []
    for item in results["scenarios"]:
        stats = item["stats"]
        sla = stats["sla_fraction"]["mean"]
        rows.append(
            "<tr>"
            + "".join(
                f"<td>{html.escape(str(x))}</td>"
                for x in (
                    f"{item['pickers']} / {item['packers']}",
                    f"{item['capacity_per_hour']:.2f}",
                    f"{item['payroll']:.2f}",
                    "n/a" if sla is None else f"{sla:.1%}",
                    f"{stats['unfinished']['mean']:.1f}",
                    "Pass" if item["feasible"] else "; ".join(item["reasons"]),
                )
            )
            + "</tr>"
        )
    warnings = "".join(f"<li>{html.escape(x)}</li>" for x in report["limitations"])
    encoded = html.escape(canonical(report))
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Operations Decision Lab — reproducible report</title>
<style>body{{font:16px system-ui;max-width:1100px;margin:40px auto;padding:24px;color:#15342e}}
table{{border-collapse:collapse;width:100%}}
td,th{{padding:12px;border-bottom:1px solid #ccd8d3;text-align:left}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f0f4f1;padding:20px}}
.flag{{padding:16px;background:#fff0cf}}@media print{{details{{display:block}}}}</style>
<h1>Operations Decision Lab</h1><p class="flag">{html.escape(report["evidence_class"])}</p>
<h2>{html.escape(results["status"])}</h2><p>Independent evaluation of selected allocation:
{results["selected_allocation"]["pickers"]} picking /
{results["selected_allocation"]["packers"]} packing.</p>
<p>Data: {html.escape(report["inputs"]["data_origin"])}. Input hash: {report["input_sha256"]}</p>
<h2>Selection results</h2><table><thead><tr><th>Pick / pack</th><th>Capacity / h</th>
<th>Scheduled payroll</th><th>Due-cohort SLA mean</th>
<th>Unfinished mean</th><th>Conditional screen</th>
</tr></thead><tbody>{"".join(rows)}</tbody></table>
<h2>Interpretation and limits</h2><p>{html.escape(results["interval_method"])}</p>
<ul>{warnings}</ul><h2>Complete reproducibility record</h2>
<p>Includes original input CSV, observation bounds, assumptions, all replications,
independent evaluation, sensitivity and environment versions.</p>
<pre>{encoded}</pre></html>"""
