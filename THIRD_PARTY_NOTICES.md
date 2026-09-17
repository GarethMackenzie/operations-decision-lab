# Third-party attribution

This project depends on separately installed packages; it does not vendor their source. Their respective copyright and license notices remain in the installed distributions.

| Runtime package | License | Source |
|---|---|---|
| SimPy 4.1.2 | MIT | https://gitlab.com/team-simpy/simpy |
| Flask 3.1.3 | BSD-3-Clause | https://github.com/pallets/flask |
| Waitress 3.0.2 | ZPL-2.1 | https://github.com/Pylons/waitress |
| Werkzeug 3.1.8 | BSD-3-Clause | https://github.com/pallets/werkzeug |
| Jinja2 3.1.6 | BSD-3-Clause | https://github.com/pallets/jinja |
| MarkupSafe 3.0.3 | BSD-3-Clause | https://github.com/pallets/markupsafe |
| Click 8.5.0 | BSD-3-Clause | https://github.com/pallets/click |
| ItsDangerous 2.2.0 | BSD-3-Clause | https://github.com/pallets/itsdangerous |
| Blinker 1.9.0 | MIT | https://github.com/pallets-eco/blinker |
| Colorama 0.4.6 (Windows) | BSD-3-Clause | https://github.com/tartley/colorama |

Development-only packages are pinned in `requirements-dev.lock`; installed package metadata is recorded in `evidence/dependency-licenses.json`. Recheck all licenses and vulnerability findings after upgrades.

Research citations to Simod, Prosimos, log-distance-measures, PM4Py, AnyLogic and public datasets are in the research dossier. They are not runtime dependencies; their source/data is not copied into the release. Prosimos licensing is unresolved in the inspected checkout and is explicitly excluded from integration.

`synthetic.csv` is generated originally for this project using SimPy and the documented seed. It contains no third-party operational records or personal data and is licensed under the project's MIT license. Browser visuals use system fonts and original CSS; no external imagery or fonts.
