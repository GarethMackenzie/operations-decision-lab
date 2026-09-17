"""Small transparent tracked-file secret scan; not a guarantee of secret absence."""

import re
import subprocess
from pathlib import Path

patterns = {
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}"),
    "AWS access key": re.compile(rb"AKIA[A-Z0-9]{16}"),
    "credential assignment": re.compile(
        rb"(?i)(?:api_key|password|secret_token)\s*[:=]\s*[\"'][A-Za-z0-9/+_=-]{16,}[\"']"
    ),
}
paths = subprocess.run(["git", "ls-files", "-z"], check=True, capture_output=True).stdout.split(
    b"\0"
)
failures = []
for raw in paths:
    if not raw:
        continue
    path = Path(raw.decode("utf-8"))
    if path.suffix in {".png", ".jpg", ".zip", ".whl"}:
        continue
    data = path.read_bytes()
    for label, pattern in patterns.items():
        if pattern.search(data):
            failures.append(f"{path}: {label}")
if failures:
    print("FAIL\n" + "\n".join(failures))
    raise SystemExit(1)
print(f"PASS: scanned {sum(bool(p) for p in paths)} tracked files; no known token/key patterns.")
