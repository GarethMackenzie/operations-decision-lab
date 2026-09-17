import pytest

from decision_lab.data import inspect_csv

HEADER = "order_id,arrival_time,pick_start,pick_end,pack_start,pack_end,picker,packer\n"
START = "2026-01-05T08:00:00+00:00"
END = "2026-01-05T16:00:00+00:00"
ROW = (
    "A,2026-01-05T08:01:00+00:00,2026-01-05T08:02:00+00:00,"
    "2026-01-05T08:08:00+00:00,2026-01-05T08:09:00+00:00,"
    "2026-01-05T08:16:00+00:00,P1,K1\n"
)


def test_observed_intervals_are_descriptive():
    q = inspect_csv(HEADER + ROW, START, END)
    assert q["elapsed_interval_means"] == {"pick": 6, "pack": 7}
    assert q["arrival_rate_observed"] == 1 / 8
    assert q["completed_cycle_mean"] == 15
    assert not q["eligible_for_attested_intervals"]


def test_completion_only_never_imputes_service():
    row = "A,2026-01-05T08:01:00+00:00,,2026-01-05T08:08:00+00:00,,2026-01-05T08:16:00+00:00,,\n"
    q = inspect_csv(HEADER + row, START, END)
    assert q["missing_starts"] == 2
    assert q["elapsed_interval_means"] == {"pick": None, "pack": None}


def test_window_censoring_and_pre_window_wip():
    row = ROW.replace("08:01", "07:01").replace("08:16", "17:16")
    q = inspect_csv(HEADER + row, START, END)
    assert q["initial_wip"] == 1
    assert q["future_endpoints_censored"] == 1
    assert q["completions_in_window"] == 0
    assert q["elapsed_interval_means"]["pack"] is None


def test_overlapping_resources():
    q = inspect_csv(HEADER + ROW + ROW.replace("A,", "B,"), START, END)
    assert q["overlap_count"] == 2
    assert not q["eligible_for_attested_intervals"]


@pytest.mark.parametrize(
    "text",
    [
        "",
        "a,b\n1,2",
        HEADER + ROW + ROW,
        HEADER + ROW.replace("08:08", "08:00"),
        HEADER + ROW.replace("+00:00", ""),
        HEADER + ROW.replace("08:08", "08:02"),
        HEADER + ROW.replace("A,", ","),
        HEADER + ROW.replace("P1,K1", "P1,K1,extra"),
        HEADER + "x" * 2_000_001,
    ],
    ids=[
        "empty",
        "schema",
        "duplicate",
        "reverse",
        "timezone",
        "zero-duration",
        "empty-id",
        "extra-field",
        "oversize",
    ],
)
def test_bad_csv(text):
    with pytest.raises(ValueError):
        inspect_csv(text, START, END)


def test_window_required_and_empty_future_arrival():
    with pytest.raises(ValueError):
        inspect_csv(HEADER + ROW, END, START)
    with pytest.raises(ValueError):
        inspect_csv(HEADER + ROW.replace("08:01", "17:01"), START, END)


def test_shared_workers_across_stages():
    # Same person overlaps picking on one order and packing on another.
    second = ROW.replace("A,", "B,").replace("P1,K1", "K1,Z1")
    second = second.replace("08:01", "08:09").replace("08:02", "08:10")
    second = second.replace("08:08", "08:16").replace("08:09:00", "08:17:00")
    # Build explicit timestamps to keep release and stage precedence unambiguous.
    second = (
        "B,2026-01-05T08:09:00+00:00,2026-01-05T08:10:00+00:00,"
        "2026-01-05T08:16:00+00:00,2026-01-05T08:17:00+00:00,"
        "2026-01-05T08:24:00+00:00,K1,Z1\n"
    )
    q = inspect_csv(HEADER + ROW + second, START, END)
    assert q["shared_workers"] == 1
    assert q["overlap_count"] == 1


def test_row_limit():
    rows = [ROW.replace("A,", f"X{i},") for i in range(5001)]
    with pytest.raises(ValueError, match="5,000"):
        inspect_csv(HEADER + "".join(rows), START, END)


@pytest.mark.parametrize("bad", [None, {}, [], 7])
def test_invalid_input_types(bad):
    with pytest.raises(ValueError):
        inspect_csv(bad, START, END)
    with pytest.raises(ValueError):
        inspect_csv(HEADER + ROW, bad, END)
