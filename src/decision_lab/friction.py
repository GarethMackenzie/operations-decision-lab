"""Explicit warehouse-friction assumptions and their limited model translation.

The values in this module are supplied by the user.  They are not industry
benchmarks and they are deliberately kept separate from observed CSV metrics.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, fields, replace
from typing import Any

from .analysis import compare
from .model import Config

SOURCES = (
    {
        "title": "OSHA: Warehousing — hazards and solutions",
        "url": "https://www.osha.gov/warehousing/hazards-solutions",
    },
    {
        "title": "2025 Warehouse/DC Operations Survey",
        "url": "https://www.scmr.com/article/2025-warehouse-dc-operations-survey-tech-adoption-marches-on",
    },
)


@dataclass(frozen=True)
class WarehouseFriction:
    """Per-order delay assumptions plus a deliberately qualitative safety screen."""

    travel_congestion_minutes: float = 0.0
    replenishment_delay_minutes: float = 0.0
    inventory_exception_rate: float = 0.0
    inventory_exception_recovery_minutes: float = 0.0
    packing_rework_rate: float = 0.0
    packing_rework_minutes: float = 0.0
    manual_handling_risk: bool = False
    vehicle_pedestrian_interaction: bool = False
    aisle_or_storage_obstruction: bool = False

    def validate(self) -> None:
        limits = {
            "travel_congestion_minutes": (0, 30),
            "replenishment_delay_minutes": (0, 30),
            "inventory_exception_rate": (0, 1),
            "inventory_exception_recovery_minutes": (0, 60),
            "packing_rework_rate": (0, 1),
            "packing_rework_minutes": (0, 60),
        }
        for name, (low, high) in limits.items():
            value = getattr(self, name)
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not low <= value <= high
            ):
                raise ValueError(f"{name} must be a finite number from {low} to {high}.")
        for name in (
            "manual_handling_risk",
            "vehicle_pedestrian_interaction",
            "aisle_or_storage_obstruction",
        ):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be true or false.")

    @classmethod
    def parse(cls, raw: Any) -> WarehouseFriction:
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise ValueError("Warehouse-friction inputs must be a JSON object.")
        unknown = set(raw) - {item.name for item in fields(cls)}
        if unknown:
            raise ValueError("Unknown warehouse-friction fields: " + ", ".join(sorted(unknown)))
        result = cls(**raw)
        result.validate()
        return result

    def time_adjustments(self) -> dict[str, float]:
        return {
            "travel_congestion_pick_minutes": self.travel_congestion_minutes,
            "replenishment_pick_minutes": self.replenishment_delay_minutes,
            "inventory_exception_pick_minutes": self.inventory_exception_rate
            * self.inventory_exception_recovery_minutes,
            "packing_rework_minutes": self.packing_rework_rate * self.packing_rework_minutes,
        }

    def has_timing_effect(self) -> bool:
        return any(value > 0 for value in self.time_adjustments().values())

    def has_inputs(self) -> bool:
        return self.has_timing_effect() or any(
            (
                self.inventory_exception_rate,
                self.inventory_exception_recovery_minutes,
                self.packing_rework_rate,
                self.packing_rework_minutes,
                self.manual_handling_risk,
                self.vehicle_pedestrian_interaction,
                self.aisle_or_storage_obstruction,
            )
        )


def friction_dict(friction: WarehouseFriction) -> dict[str, Any]:
    return asdict(friction)


def assess_friction(config: Config, friction: WarehouseFriction) -> dict[str, Any]:
    """Produce safety prompts and an optional full comparison with added mean time.

    Rates times recovery minutes are expected added minutes per order.  This is
    a transparent planning approximation, not a claim about event timing,
    independent causes, or the probability of a safety incident.
    """

    config.validate()
    friction.validate()
    adjustments = friction.time_adjustments()
    adjusted = replace(
        config,
        pick_minutes=config.pick_minutes
        + adjustments["travel_congestion_pick_minutes"]
        + adjustments["replenishment_pick_minutes"]
        + adjustments["inventory_exception_pick_minutes"],
        pack_minutes=config.pack_minutes + adjustments["packing_rework_minutes"],
    )
    adjusted.validate()
    flags: list[dict[str, str]] = []
    if friction.manual_handling_risk:
        flags.append(
            {
                "issue": "Manual handling / repetition flagged",
                "action": (
                    "Review lift heights, reaches, loads, repetition and task pace with the site's "
                    "competent safety staff. Do not use a throughput target to override a "
                    "safety concern."
                ),
            }
        )
    if friction.vehicle_pedestrian_interaction:
        flags.append(
            {
                "issue": "Powered-equipment and pedestrian interaction flagged",
                "action": (
                    "Review traffic separation, marked travel routes, visibility and operator "
                    "training "
                    "before changing the work plan."
                ),
            }
        )
    if friction.aisle_or_storage_obstruction:
        flags.append(
            {
                "issue": "Aisle, floor, rack or storage condition flagged",
                "action": (
                    "Clear and mark access routes, inspect storage/rack condition and follow "
                    "the site's "
                    "isolation and maintenance procedure for defects."
                ),
            }
        )
    actions: list[str] = []
    if friction.travel_congestion_minutes or friction.replenishment_delay_minutes:
        actions.append(
            "Measure travel, waiting and replenishment time by zone and shift before changing "
            "slotting, staging or release rules."
        )
    if friction.inventory_exception_rate or friction.inventory_exception_recovery_minutes:
        actions.append(
            "Track exception type, location and recovery time; separate stock accuracy, location "
            "accuracy and replenishment availability."
        )
    if friction.packing_rework_rate or friction.packing_rework_minutes:
        actions.append(
            "Classify packing rework by cause, then measure its duration and check/label quality "
            "before treating it as normal service time."
        )
    if not actions and not flags:
        actions.append(
            "No warehouse-friction assumptions are active. Capture local observations before using "
            "this screen to change service-time inputs."
        )
    return {
        "active": friction.has_timing_effect(),
        "requires_confirmation": friction.has_inputs(),
        "inputs": friction_dict(friction),
        "time_adjustments_minutes_per_order": adjustments,
        "base_service_minutes": {"pick": config.pick_minutes, "pack": config.pack_minutes},
        "adjusted_service_minutes": {"pick": adjusted.pick_minutes, "pack": adjusted.pack_minutes},
        "safety_flags": flags,
        "actions": actions,
        "sources": [dict(source) for source in SOURCES],
        "comparison": compare(adjusted) if friction.has_timing_effect() else None,
        "method_note": (
            "Timed issues are modeled as expected added service minutes per order. "
            "Safety flags are review prompts, not a safety audit, incident prediction "
            "or legal compliance determination."
        ),
    }
