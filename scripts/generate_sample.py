"""Generate our original synthetic CSV from a known hypothetical process."""

import csv
from datetime import datetime, timedelta
from pathlib import Path

from decision_lab.model import Config, simulate, workload

config = Config()
trace = simulate(config, 2, 2, workload(config, 17))["trace"]
start = datetime.fromisoformat("2026-01-05T08:00:00+00:00")
target = Path("src/decision_lab/samples/synthetic.csv")
target.parent.mkdir(parents=True, exist_ok=True)
with target.open("w", newline="", encoding="utf-8") as stream:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        ["order_id", "arrival_time", "pick_start", "pick_end", "pack_start", "pack_end"]
    )
    for row in trace:
        writer.writerow(
            [f"SYN-{row['id']:04}"]
            + [
                (start + timedelta(minutes=row[key])).isoformat() if key in row else ""
                for key in ("arrival", "pick_start", "pick_end", "pack_start", "pack_end")
            ]
        )
print(f"Generated {len(trace)} synthetic orders: {target}")
