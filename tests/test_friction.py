import pytest

from decision_lab.friction import WarehouseFriction, assess_friction
from decision_lab.model import Config


def test_friction_turns_local_delays_into_explicit_service_assumptions():
    config = Config(arrival_rate=2, max_workers=2, service_cv=0, target_fraction=0.5)
    friction = WarehouseFriction(
        travel_congestion_minutes=1.5,
        replenishment_delay_minutes=0.5,
        inventory_exception_rate=0.2,
        inventory_exception_recovery_minutes=5,
        packing_rework_rate=0.1,
        packing_rework_minutes=4,
    )
    result = assess_friction(config, friction)
    assert result["active"]
    assert result["time_adjustments_minutes_per_order"] == {
        "travel_congestion_pick_minutes": 1.5,
        "replenishment_pick_minutes": 0.5,
        "inventory_exception_pick_minutes": 1.0,
        "packing_rework_minutes": 0.4,
    }
    assert result["adjusted_service_minutes"] == {"pick": 9.0, "pack": 7.4}
    assert result["comparison"] is not None
    assert result["comparison"]["evaluation"]["pickers"] == 1


def test_safety_flags_create_prompts_without_a_performance_scenario():
    friction = WarehouseFriction(
        manual_handling_risk=True,
        vehicle_pedestrian_interaction=True,
        aisle_or_storage_obstruction=True,
    )
    result = assess_friction(Config(), friction)
    assert result["active"] is False
    assert result["comparison"] is None
    assert len(result["safety_flags"]) == 3
    assert {item["issue"] for item in result["safety_flags"]} == {
        "Manual handling / repetition flagged",
        "Powered-equipment and pedestrian interaction flagged",
        "Aisle, floor, rack or storage condition flagged",
    }


@pytest.mark.parametrize(
    "raw",
    [
        {"travel_congestion_minutes": -1},
        {"inventory_exception_rate": 1.1},
        {"manual_handling_risk": 1},
        {"unknown": 0},
        [],
    ],
)
def test_reject_bad_friction(raw):
    with pytest.raises(ValueError):
        WarehouseFriction.parse(raw)
