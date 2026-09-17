"""Record the tested package versions; run intentionally when refreshing locks."""

import json
from importlib.metadata import distributions, version
from pathlib import Path

runtime = [
    "simpy",
    "Flask",
    "waitress",
    "Werkzeug",
    "Jinja2",
    "MarkupSafe",
    "click",
    "itsdangerous",
    "blinker",
    "colorama",
]
lines = [f"{name}=={version(name)}" for name in sorted(runtime, key=str.lower)]
Path("requirements-runtime.lock").write_text("\n".join(lines) + "\n", encoding="utf-8")
Path("requirements.lock").write_text(
    "-r requirements-runtime.lock\n"
    + "\n".join(f"{name}=={version(name)}" for name in ("pip", "setuptools", "wheel", "packaging"))
    + "\n",
    encoding="utf-8",
)
installed = sorted(distributions(), key=lambda d: d.metadata["Name"].lower())
Path("requirements-dev.lock").write_text(
    "\n".join(
        f"{d.metadata['Name']}=={d.version}"
        for d in installed
        if d.metadata["Name"] != "operations-decision-lab"
    )
    + "\n",
    encoding="utf-8",
)
licenses = [
    {
        "name": d.metadata["Name"],
        "version": d.version,
        "license": d.metadata.get("License-Expression")
        or (d.metadata.get("License") or "unspecified")[:100],
        "license_classifiers": [
            c for c in d.metadata.get_all("Classifier", []) if c.startswith("License ::")
        ],
    }
    for d in installed
]
Path("evidence/dependency-licenses.json").write_text(json.dumps(licenses, indent=2) + "\n")
print("Recorded runtime, installer and development locks plus license metadata.")
