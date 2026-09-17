"""Measure bounded workload wall time and peak resident process memory."""

import ctypes
import json
import platform
import sys
import time
from dataclasses import replace
from pathlib import Path

from decision_lab.analysis import compare
from decision_lab.model import Config


def peak_mb():
    if sys.platform == "win32":
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t)
                for name in (
                    "PeakWorkingSetSize",
                    "WorkingSetSize",
                    "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage",
                    "QuotaPeakNonPagedPoolUsage",
                    "QuotaNonPagedPoolUsage",
                    "PagefileUsage",
                    "PeakPagefileUsage",
                )
            ]

        handle = ctypes.windll.kernel32.GetCurrentProcess
        handle.restype = wintypes.HANDLE
        get = ctypes.windll.psapi.GetProcessMemoryInfo
        get.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not get(handle(), ctypes.byref(counters), counters.cb):
            raise OSError("Unable to measure process peak memory.")
        return counters.PeakWorkingSetSize / 1024**2
    import resource

    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw / (1024**2 if sys.platform == "darwin" else 1024)


results = {"python": platform.python_version(), "platform": platform.platform(), "cases": []}
for name, config, limit in (
    ("default", Config(), 15),
    (
        "bounded maximum",
        replace(
            Config(),
            arrival_rate=60,
            shift_hours=12,
            max_workers=6,
            initial_pick=100,
            initial_pack=100,
        ),
        60,
    ),
):
    started = time.perf_counter()
    result = compare(config)
    elapsed = time.perf_counter() - started
    memory = peak_mb()
    results["cases"].append(
        {
            "name": name,
            "seconds": elapsed,
            "peak_rss_mb": memory,
            "time_limit_seconds": limit,
            "memory_limit_mb": 512,
            "status": "PASS" if elapsed < limit and memory < 512 else "FAIL",
            "scenarios": len(result["scenarios"]),
        }
    )
Path("evidence").mkdir(exist_ok=True)
Path("evidence/benchmark.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
if any(case["status"] != "PASS" for case in results["cases"]):
    raise SystemExit(1)
