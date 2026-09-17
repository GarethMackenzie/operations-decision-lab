from dataclasses import replace
from heapq import heapify, heappop, heappush

import pytest

from decision_lab.analysis import compare, evaluate, interval
from decision_lab.model import Config, Job, capacity, simulate, workload


def reference(jobs, pickers, packers):
    """Independent server-availability recurrence: no SimPy or app scheduling helpers."""
    p = [0.0] * pickers
    q = [0.0] * packers
    heapify(p)
    heapify(q)
    picked = []
    for i, job in enumerate(sorted(jobs, key=lambda j: j.arrival)):
        finish = max(job.arrival, heappop(p)) + job.pick
        heappush(p, finish)
        picked.append((finish, i, job.pack))
    completed = {}
    for ready, i, duration in sorted(picked):
        finish = max(ready, heappop(q)) + duration
        heappush(q, finish)
        completed[i] = finish
    return completed


def test_hand_case_and_conservation():
    c = Config(shift_hours=2)
    result = simulate(c, 1, 1, [Job(0, 6, 7), Job(0, 6, 7)])
    assert [r["pack_end"] for r in result["trace"]] == [13, 20]
    assert result["completed_cycle_mean"] == 16.5
    assert result["completed"] + result["unfinished"] == result["arrivals"]
    assert result["pack_utilization"] == pytest.approx(14 / 120)
    assert result["pick_mean_queue"] == pytest.approx(6 / 120)


def test_shift_boundary_is_inclusive_without_drain():
    c = Config(shift_hours=2)
    result = simulate(c, 1, 1, [Job(0, 60, 60), Job(1, 60, 60)])
    assert result["completed"] == 1
    assert result["unfinished"] == 1
    assert result["trace"][0]["pack_end"] == 120
    assert "pack_end" not in result["trace"][1]


def test_break_pauses_work_and_utilization():
    c = Config(shift_hours=2, break_minutes=30)
    result = simulate(c, 1, 1, [Job(50, 20, 10)])
    assert result["trace"][0]["pick_end"] == 100
    assert result["trace"][0]["pack_end"] == 110
    assert result["pick_utilization"] == pytest.approx(20 / 90)
    during = simulate(c, 1, 1, [Job(65, 5, 5)])
    assert during["trace"][0]["pick_start"] == 90
    assert during["pick_mean_queue"] == pytest.approx(25 / 120)


def test_initial_stage_backlogs_and_due_cohort():
    result = simulate(
        Config(shift_hours=2), 1, 1, [Job(0, 6, 7, "pack"), Job(0, 6, 7, "pick"), Job(110, 6, 7)]
    )
    assert result["initial_backlog"] == 2
    assert result["arrivals"] == 1
    assert result["completed"] == 2
    assert result["unfinished"] == 1
    assert result["due_orders"] == 0
    assert result["sla_fraction"] is None
    assert "pick_start" not in result["trace"][0]


@pytest.mark.parametrize("pickers,packers", [(1, 1), (2, 2), (1, 3), (3, 2)])
def test_independent_reference(pickers, packers):
    c = Config(arrival_rate=24, shift_hours=8, service_cv=1)
    jobs = workload(c, 91)
    expected = reference(jobs, pickers, packers)
    actual = simulate(c, pickers, packers, jobs)
    for row in actual["trace"]:
        finish = expected[row["id"]]
        if finish <= 480:
            assert row["pack_end"] == pytest.approx(finish)
        else:
            assert "pack_end" not in row
    assert actual["completed"] + actual["unfinished"] == len(jobs)
    assert 0 <= actual["pick_utilization"] <= 1 + 1e-12
    assert 0 <= actual["pack_utilization"] <= 1 + 1e-12
    assert (
        sum(actual[f"{s}_{k}_at_close"] for s in ("pick", "pack") for k in ("queued", "busy"))
        == actual["unfinished"]
    )


def test_default_capacity_and_payroll():
    c = Config()
    assert capacity(c, 2, 2)["capacity_per_hour"] == pytest.approx(120 / 7)
    assert not any(capacity(c, p, 4 - p)["stable"] for p in range(1, 4))
    assert not capacity(replace(c, arrival_rate=120 / 7), 2, 2)["stable"]
    assert capacity(replace(c, break_minutes=30), 2, 2)["payroll"] == 3200
    assert capacity(c, 2, 3)["marginal_payroll"] == 800


def test_default_no_feasible_and_independent_selection():
    report = compare(Config())
    assert report["confirmed_feasible"] is False
    assert not any(s["feasible"] for s in report["scenarios"])
    assert set(report["selection_seeds"]).isdisjoint(report["evaluation_seeds"])
    assert len(report["sensitivity"]) == 3
    assert len(report["scenarios"]) == 6


def test_known_feasible_and_reproducible():
    c = Config(arrival_rate=2, service_cv=0, target_fraction=0.8, max_workers=2)
    first = compare(c)
    assert first["confirmed_feasible"] is True
    assert first == compare(c)


def test_interval_and_missing_cohort_cannot_pass():
    values = [float(i) for i in range(30)]
    ci = interval(values)
    assert ci["mean"] == 14.5
    # Hand formula: mean=14.5, sample variance=77.5, t(29)=2.0452296421.
    assert ci["low"] == pytest.approx(11.21275326754)
    assert interval([None] * 30)["low"] is None
    assert interval([1.0] * 29 + [None])["low"] is None
    c = Config(arrival_rate=0.1, shift_hours=2)
    assert not evaluate(c, 2, 2, list(range(30)))["feasible"]


@pytest.mark.parametrize(
    "raw",
    [
        {"arrival_rate": float("nan")},
        {"max_workers": True},
        {"seed": 1.5},
        {"max_workers": 100},
        {"alien": 1},
        {"pick_minutes": 0},
        {"arrival_rate": "18"},
        {"shift_hours": 2, "sla_minutes": 120},
        [],
    ],
)
def test_reject_bad_config(raw):
    with pytest.raises(ValueError):
        Config.parse(raw)
