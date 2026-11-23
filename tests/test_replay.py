from copy import deepcopy

import pytest

from decision_lab.report import make_report, verify_report
from decision_lab.web import sample_request


@pytest.fixture(scope="module")
def report():
    return make_report(sample_request())


def test_unchanged_report_and_informational_environment(report):
    verify_report(report)
    changed = deepcopy(report)
    changed["environment"] = {"python": "different informational runtime"}
    verify_report(changed)


@pytest.mark.parametrize(
    "field",
    [
        "results",
        "warehouse_friction",
        "data_quality",
        "input_sha256",
        "limitations",
        "evidence_class",
    ],
)
def test_each_deterministic_section_is_verified(report, field):
    changed = deepcopy(report)
    changed[field] = "fabricated mutation"
    with pytest.raises(ValueError, match="Replay mismatch"):
        verify_report(changed)


@pytest.mark.parametrize(
    "field,value", [("schema_version", 999), ("schema_version", 3.0), ("model_version", "other")]
)
def test_incompatible_version_is_explicit(report, field, value):
    changed = deepcopy(report)
    changed[field] = value
    with pytest.raises(ValueError, match="Unsupported"):
        verify_report(changed)


def test_missing_and_extra_derived_fields_rejected(report):
    changed = deepcopy(report)
    del changed["warehouse_friction"]
    with pytest.raises(ValueError, match="Replay mismatch"):
        verify_report(changed)
    changed = deepcopy(report)
    changed["unexpected_decision"] = "approved"
    with pytest.raises(ValueError, match="Replay mismatch"):
        verify_report(changed)
