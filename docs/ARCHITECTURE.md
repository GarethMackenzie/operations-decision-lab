# ADR 001 — A small local decision workbench

Status: accepted 2026-09-16, before implementation.

Use Python 3.12, SimPy 4.1.2, Flask and Waitress; plain browser HTML/CSS/JavaScript, no frontend build chain. Flask provides the local API and packaged static assets. Waitress binds only 127.0.0.1 with a bounded request size. One compute lock prevents overlapping experiments; return a clear busy response. No database, telemetry or cloud calls. Report export runs from the submitted inputs and returns downloadable bytes; no user-controlled output path on the server. A single latest export is retained in process memory behind an unguessable token, with links valid for 10 minutes. A new comparison replaces it; shutdown clears memory. This supports browsers that cannot download blob URLs.

Modules: `data.py` parses and describes; `model.py` defines assumptions and simulation; `analysis.py` enumerates/evaluates; `report.py` creates reproducible bundles; `web.py` serves; `__main__.py` provides CLI. The UI uses the same API/core as CLI. All calculations are in tested Python.

Alternatives: Streamlit would speed initial prototyping but add a larger dependency/UI runtime. React is unnecessary for this workflow. A custom simulator reduces dependencies but raises verification burden; use an independently written heap-based two-stage reference only in tests. Simod/Prosimos are not installed into the app because their package Python requirements exclude 3.12; Prosimos redistribution rights unresolved. Use separate Python 3.11 environments if later benchmarking is justified.

Consequences: narrow but understandable model, reproducible local use, modest maintenance burden. Not production hosting. A true workforce scheduler or digital twin will need a new ADR, richer data and renewed release gates.
