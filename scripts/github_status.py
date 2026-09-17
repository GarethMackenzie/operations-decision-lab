"""Read GitHub identity/destination via configured git credentials; never print secrets."""

import json
import os
import subprocess
import urllib.error
import urllib.request

env = dict(os.environ, GCM_INTERACTIVE="never", GIT_TERMINAL_PROMPT="0")
result = subprocess.run(
    ["git", "credential", "fill"],
    input="protocol=https\nhost=github.com\n\n",
    capture_output=True,
    text=True,
    env=env,
    timeout=20,
)
if result.returncode:
    raise SystemExit(
        "BLOCKED: Git credential manager has no usable noninteractive GitHub credential."
    )
credential = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
secret = credential.get("password")
if not secret:
    raise SystemExit("BLOCKED: no GitHub authentication credential returned.")
for path in ("user", "repos/GarethMackenzie/operations-decision-lab"):
    request = urllib.request.Request(
        "https://api.github.com/" + path,
        headers={
            "Authorization": "Bearer " + secret,
            "Accept": "application/vnd.github+json",
            "User-Agent": "Operations-Decision-Lab-release-verification",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
            print(
                json.dumps(
                    {
                        "endpoint": path,
                        **{
                            k: payload[k]
                            for k in (
                                "login",
                                "full_name",
                                "private",
                                "permissions",
                                "default_branch",
                            )
                            if k in payload
                        },
                    }
                )
            )
    except urllib.error.HTTPError as error:
        print(json.dumps({"endpoint": path, "http_status": error.code}))
