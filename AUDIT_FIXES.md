# Audit fixes — 23 November 2026

Replay now verifies all deterministic report fields, including warehouse friction and data quality. Only environment metadata is excluded. Reports with a different model/schema version are rejected explicitly; replay old reports with their original package version. This remains a local synthetic research prototype.
