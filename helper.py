"""Run common development commands."""

import subprocess
import sys

COMMANDS = {
    "test": [
        ["uv", "run", "--group", "dev", "pytest"],
    ],
    "lint": [
        ["uv", "run", "--group", "lint", "ruff", "check", "."],
        ["uv", "run", "--group", "lint", "ruff", "format", "--check", "."],
        ["uv", "run", "--group", "lint", "mypy", "src/rykit"],
    ],
    "test-build": [["uv", "build"]],
    "install": [["uv", "sync", "--all-groups"]],
}

if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
    options = ", ".join(COMMANDS)
    raise SystemExit(f"Usage: python helper.py <{options}>")

for command in COMMANDS[sys.argv[1]]:
    subprocess.run(command, check=True)
