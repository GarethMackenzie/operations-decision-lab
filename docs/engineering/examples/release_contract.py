"""Proposed fail-closed evidence contract; standard library only."""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class CheckResult:
    rule_id: str
    outcome: str
    examined: int
    violations: int


class ReleaseBlocked(ValueError):
    """The required evidence does not authorize release."""


def require_release(required: frozenset[str], results: Iterable[CheckResult]) -> None:
    if not required or any(
        type(rule) is not str or not rule.strip() for rule in required
    ):
        raise ReleaseBlocked("Required rule IDs must be nonempty strings")
    seen: set[str] = set()
    for result in results:
        if not isinstance(result, CheckResult):
            raise ReleaseBlocked("Unsupported result type")
        if type(result.rule_id) is not str or result.rule_id not in required:
            raise ReleaseBlocked("Unexpected rule ID")
        if result.rule_id in seen:
            raise ReleaseBlocked("Duplicate rule ID")
        seen.add(result.rule_id)
        # bool is a subclass of int: exact type checks are deliberate.
        if type(result.examined) is not int or type(result.violations) is not int:
            raise ReleaseBlocked("Counts must be integers, excluding booleans")
        if result.examined <= 0 or not 0 <= result.violations <= result.examined:
            raise ReleaseBlocked("Invalid counts or empty evaluated population")
        if result.outcome != "PASS" or result.violations != 0:
            raise ReleaseBlocked("Check failed, errored or lacks clean evidence")
    if seen != required:
        raise ReleaseBlocked("Required checks are missing")
