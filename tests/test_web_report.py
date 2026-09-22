import copy

import pytest

from decision_lab.report import canonical, make_report, report_html
from decision_lab.web import create_app, sample_request


@pytest.fixture
def client():
    return create_app().test_client()


def test_health_assets_and_security_headers(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"RESEARCH PROTOTYPE" in response.data
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/health").json == {"status": "ok"}
    assert client.get("/", headers={"Host": "attacker.invalid"}).status_code == 400


def test_api_errors_and_limits(client):
    assert client.post("/api/inspect", json=[]).status_code == 400
    assert client.post("/api/inspect", data="x").status_code == 415
    assert (
        client.post("/api/inspect", json={}, headers={"Origin": "https://evil.example"}).status_code
        == 403
    )
    assert (
        client.post(
            "/api/inspect", data="x" * 2_100_001, content_type="application/json"
        ).status_code
        == 413
    )
    assert (
        client.post("/api/inspect", data="{broken", content_type="application/json").status_code
        == 400
    )
    assert (
        client.post(
            "/api/compare", data='{"config":{"seed":NaN}}', content_type="application/json"
        ).status_code
        == 400
    )


def test_sample_end_to_end_and_html_escaping(client):
    request = client.get("/api/sample").json
    assert client.post("/api/inspect", json=request).status_code == 200
    request["csv"] = request["csv"].replace("SYN-0000", "<script>alert(1)</script>")
    response = client.post("/api/compare", json=request)
    assert response.status_code == 200
    report = response.json["report"]
    assert report["results"]["status"] == "NO CONFIRMED FEASIBLE OPTION"
    assert "<script>alert(1)</script>" not in response.json["html"]
    assert "&lt;script&gt;" in response.json["html"]
    assert canonical(report) == response.json["json"]
    assert report_html(report) == response.json["html"]
    assert make_report(report["inputs"])["results"] == report["results"]
    for kind, url in response.json["downloads"].items():
        exported = client.get(url)
        assert exported.status_code == 200
        assert exported.get_data(as_text=True) == response.json[kind]
        assert exported.headers["Content-Disposition"].endswith(f'.{kind}"')
    assert client.get("/exports/unknown/json").status_code == 404


def test_export_expiration(client, monkeypatch):
    import decision_lab.web as web

    monkeypatch.setattr(web.time, "monotonic", lambda: 100)
    response = client.post("/api/compare", json=sample_request())
    url = response.json["downloads"]["json"]
    monkeypatch.setattr(web.time, "monotonic", lambda: 701)
    assert client.get(url).status_code == 404


def test_assumptions_required_and_no_unattested_adoption():
    body = sample_request()
    body["assumptions_confirmed"] = False
    with pytest.raises(ValueError):
        make_report(body)
    body["assumptions_confirmed"] = True
    body["service_source"] = "attested_intervals"
    with pytest.raises(ValueError):
        make_report(body)
    changed = copy.deepcopy(body)
    changed["active_service_confirmed"] = True
    with pytest.raises(ValueError):
        make_report(changed)


def test_friction_requires_confirmation_and_is_exported():
    body = sample_request()
    body["config"].update(arrival_rate=2, max_workers=2, service_cv=0, target_fraction=0.5)
    body["friction"] = {
        "travel_congestion_minutes": 2,
        "replenishment_delay_minutes": 0,
        "inventory_exception_rate": 0,
        "inventory_exception_recovery_minutes": 0,
        "packing_rework_rate": 0,
        "packing_rework_minutes": 0,
        "manual_handling_risk": True,
        "vehicle_pedestrian_interaction": False,
        "aisle_or_storage_obstruction": False,
    }
    with pytest.raises(ValueError, match="Confirm warehouse-friction"):
        make_report(body)
    body["friction_confirmed"] = True
    report = make_report(body)
    assert report["warehouse_friction"]["active"] is True
    assert report["warehouse_friction"]["adjusted_service_minutes"]["pick"] == 8
    assert "Warehouse friction screen" in report_html(report)


def test_valid_interval_adoption_and_mismatch():
    from datetime import datetime, timedelta

    from decision_lab.data import inspect_csv

    body = sample_request()
    lines = ["order_id,arrival_time,pick_start,pick_end,pack_start,pack_end,picker,packer"]
    start = datetime.fromisoformat(body["window_start"])
    for index in range(10):
        t = start + timedelta(minutes=20 * index)
        stamps = [(t + timedelta(minutes=m)).isoformat() for m in (0, 0, 6, 6, 13)]
        lines.append(",".join([str(index), *stamps, "picker", "packer"]))
    body["csv"] = "\n".join(lines) + "\n"
    assert inspect_csv(body["csv"], body["window_start"], body["window_end"])[
        "eligible_for_attested_intervals"
    ]
    body["config"].update(arrival_rate=2, max_workers=2, target_fraction=0.8)
    body.update(
        service_source="attested_intervals",
        active_service_confirmed=True,
        data_origin="user-provided; provenance unverified",
    )
    report = make_report(body)
    assert report["inputs"]["service_source"] == "attested_intervals"
    body["config"]["pick_minutes"] = 5
    with pytest.raises(ValueError, match="match"):
        make_report(body)


@pytest.mark.parametrize("key", ["service_source", "data_origin"])
def test_unhashable_api_fields_are_useful_errors(client, key):
    body = sample_request()
    body[key] = []
    assert client.post("/api/compare", json=body).status_code == 400
