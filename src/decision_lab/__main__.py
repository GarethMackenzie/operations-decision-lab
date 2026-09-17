"""CLI quick start, file inspection and deterministic report replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data import MAX_BYTES, inspect_csv
from .report import canonical, make_report, report_html
from .web import create_app, sample_request


def bounded_read(path: Path, maximum: int = MAX_BYTES) -> str:
    with path.open("rb") as handle:
        raw = handle.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError(f"File exceeds {maximum} bytes.")
    return raw.decode("utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Operations Decision Lab — hypothetical research prototype"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="Start local workbench")
    serve.add_argument("--port", type=int, default=8765)
    demo = sub.add_parser("demo", help="Run the synthetic example")
    demo.add_argument("--output", type=Path, default=Path("reports/demo"))
    run = sub.add_parser("run", help="Run a JSON request, using the API schema")
    run.add_argument("request", type=Path)
    run.add_argument("--output", type=Path, default=Path("reports/custom"))
    inspect = sub.add_parser("inspect", help="Inspect CSV without simulating")
    inspect.add_argument("csv", type=Path)
    inspect.add_argument("--start", required=True)
    inspect.add_argument("--end", required=True)
    replay = sub.add_parser("replay", help="Recompute and verify a report's numerical results")
    replay.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "serve":
            from waitress import serve as waitress_serve

            if not 1024 <= args.port <= 65535:
                raise ValueError("Port must be between 1024 and 65535.")
            print(f"Operations Decision Lab: http://127.0.0.1:{args.port}", flush=True)
            waitress_serve(
                create_app(),
                host="127.0.0.1",
                port=args.port,
                threads=2,
                max_request_body_size=2_100_000,
                channel_timeout=60,
            )
        elif args.command == "inspect":
            print(canonical(inspect_csv(bounded_read(args.csv), args.start, args.end)))
        elif args.command == "replay":
            report = json.loads(bounded_read(args.report, 10_000_000))
            fresh = make_report(report["inputs"])
            if (
                fresh["results"] != report["results"]
                or fresh["input_sha256"] != report["input_sha256"]
            ):
                raise ValueError("Replay mismatch: numerical results or input hash differ.")
            print("PASS: numerical results and input hash reproduced.")
        else:
            body = (
                sample_request()
                if args.command == "demo"
                else json.loads(bounded_read(args.request, 2_100_000))
            )
            report = make_report(body)
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output / "report.json").write_text(canonical(report), encoding="utf-8")
            (args.output / "report.html").write_text(report_html(report), encoding="utf-8")
            print(report["results"]["status"])
            print(str(args.output.resolve()))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
