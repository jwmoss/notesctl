"""Read the real Apple Notes database through the installed CLI."""

import json
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> None:
    """Check database access and an actual note listing without source writes."""
    result = subprocess.run(
        ["notesctl", "doctor", "--json"],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    counts = json.loads(result.stdout)
    if not isinstance(counts.get("total_notes"), int) or counts["total_notes"] < 1:
        raise RuntimeError("No real Notes records found; live proof requires a populated database")
    result = subprocess.run(
        ["notesctl", "list-notes", "--limit", "1"],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    if "Notes (" not in result.stdout:
        raise RuntimeError("The CLI did not list a real Notes record")
    with TemporaryDirectory(prefix="notesctl-live-") as work_dir:
        output = Path(work_dir) / "export"
        result = subprocess.run(
            ["notesctl", "export", "--dry-run", "--output", str(output)],
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
        exported = re.search(r"Would export (\d+) notes", result.stdout)
        if not exported or int(exported[1]) < 1 or "Failed to export" in result.stderr:
            raise RuntimeError("The live export preview did not convert real Notes records")
        if output.exists():
            raise RuntimeError("The export preview created its output directory")
    print("PASS real Apple Notes CLI reads and export preview")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"FAIL {error}; run notesctl doctor to inspect database access", file=sys.stderr)
        sys.exit(1)
