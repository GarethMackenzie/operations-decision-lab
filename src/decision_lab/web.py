"""Loopback-only application; no persistent upload storage."""

from __future__ import annotations

import json
import secrets
import threading
import time
from importlib.resources import files
from typing import Any

from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import HTTPException

from .data import inspect_csv
from .model import Config, config_dict
from .report import canonical, make_report, report_html


def sample_request() -> dict[str, Any]:
    return {
        "csv": files("decision_lab").joinpath("samples/synthetic.csv").read_text(encoding="utf-8"),
        "window_start": "2026-01-05T08:00:00+00:00",
        "window_end": "2026-01-05T16:00:00+00:00",
        "config": config_dict(Config()),
        "assumptions_confirmed": True,
        "active_service_confirmed": False,
        "service_source": "manual",
        "data_origin": "synthetic demo",
    }


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.update(MAX_CONTENT_LENGTH=2_100_000, TRUSTED_HOSTS=["127.0.0.1", "localhost"])
    lock = threading.Lock()
    # One bounded, short-lived export in process memory; never written to disk.
    export_cache: dict[str, Any] = {}

    @app.before_request
    def guard() -> Response | None:
        if request.method == "POST":
            origin = request.headers.get("Origin")
            if origin and origin != request.host_url.rstrip("/"):
                return jsonify(error="Cross-origin requests are not supported."), 403  # type: ignore[return-value]
            if not request.is_json:
                return jsonify(error="Send application/json."), 415  # type: ignore[return-value]
        return None

    @app.after_request
    def headers(response: Response) -> Response:
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        )
        return response

    @app.errorhandler(ValueError)
    def invalid(error: ValueError) -> tuple[Response, int]:
        return jsonify(error=str(error)), 400

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException) -> tuple[Response, int]:
        return jsonify(error=error.description), error.code or 500

    @app.get("/")
    def index() -> Response:
        return app.send_static_file("index.html")

    @app.get("/api/sample")
    def sample() -> Response:
        return jsonify(sample_request())

    @app.get("/health")
    def health() -> Response:
        return jsonify(status="ok")

    def payload() -> dict[str, Any]:
        try:
            body = json.loads(
                request.get_data(),
                parse_constant=lambda _: (_ for _ in ()).throw(
                    ValueError("Non-finite JSON numbers are not supported.")
                ),
            )
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("Malformed UTF-8 JSON.") from error
        if not isinstance(body, dict):
            raise ValueError("Request must be a JSON object.")
        return body

    @app.post("/api/inspect")
    def inspect() -> Response:
        body = payload()
        return jsonify(
            inspect_csv(body.get("csv"), body.get("window_start"), body.get("window_end"))
        )

    @app.post("/api/compare")
    def run() -> tuple[Response, int] | Response:
        if not lock.acquire(blocking=False):
            return jsonify(
                error="An experiment is already running. Try again after it finishes."
            ), 429
        try:
            report = make_report(payload())
            # Export is created from the same verified calculation, never a client-supplied report.
            encoded = {"json": canonical(report), "html": report_html(report)}
            token = secrets.token_urlsafe(32)
            export_cache.clear()
            export_cache.update(token=token, expires=time.monotonic() + 600, **encoded)
            return jsonify(
                report=report,
                **encoded,
                downloads={kind: f"/exports/{token}/{kind}" for kind in encoded},
            )
        finally:
            lock.release()

    @app.get("/exports/<token>/<kind>")
    def download(token: str, kind: str) -> Response | tuple[Response, int]:
        with lock:
            if (
                kind not in {"json", "html"}
                or not secrets.compare_digest(token, export_cache.get("token", ""))
                or time.monotonic() >= export_cache.get("expires", 0)
            ):
                return jsonify(error="Export expired. Compare again to create a fresh report."), 404
            response = Response(
                export_cache[kind],
                mimetype="application/json" if kind == "json" else "text/html",
            )
            response.headers["Content-Disposition"] = (
                f'attachment; filename="operations-decision-report.{kind}"'
            )
            return response

    return app
