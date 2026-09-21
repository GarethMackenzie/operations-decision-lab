"""Build or preview the dependency-free GitHub Pages artifact."""

from __future__ import annotations

import argparse
import functools
import http.server
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    ROOT / "src/decision_lab/static/index.html": Path("index.html"),
    ROOT / "src/decision_lab/static/app.js": Path("static/app.js"),
    ROOT / "src/decision_lab/static/static-engine.js": Path("static/static-engine.js"),
    ROOT / "src/decision_lab/static/style.css": Path("static/style.css"),
    ROOT / "src/decision_lab/samples/synthetic.csv": Path("static/synthetic.csv"),
}


def build(target: Path) -> None:
    """Copy the explicit public allowlist to a new, empty artifact directory."""
    if target.exists() and any(target.iterdir()):
        raise ValueError(f"Pages target must be empty: {target}")
    target.mkdir(parents=True, exist_ok=True)
    for source, relative in FILES.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    (target / ".nojekyll").touch()


def sync_docs() -> None:
    """Refresh the files GitHub Pages publishes from the repository's docs folder."""
    target = ROOT / "docs"
    for source, relative in FILES.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    (target / ".nojekyll").touch()


def serve(port: int) -> None:
    """Serve the artifact at its production project-site subpath."""
    with tempfile.TemporaryDirectory(prefix="operations-decision-pages-") as temporary:
        root = Path(temporary)
        build(root / "operations-decision-lab")
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
        print(f"GitHub Pages preview: http://127.0.0.1:{port}/operations-decision-lab/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("target", type=Path)
    subparsers.add_parser("sync-docs")
    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("--port", type=int, default=8766)
    arguments = parser.parse_args()
    if arguments.command == "build":
        build(arguments.target)
    elif arguments.command == "sync-docs":
        sync_docs()
    else:
        serve(arguments.port)


if __name__ == "__main__":
    main()
