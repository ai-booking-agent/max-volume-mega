"""Installs the daily launchd job that runs the automation unattended.

    python -m scripts.install_scheduler --hour 9 --minute 0

Loads a launch agent that fires once a day at the given local time. Requires
Spotify, the Discord webhook, and both one-time logins to already be set up.
"""
import argparse
import subprocess
import sys
from pathlib import Path

from src import config

TEMPLATE = config.ROOT_DIR / "launchd" / "com.maxvolumemega.daily.plist.template"
PLIST_LABEL = "com.maxvolumemega.daily"
DEST = Path.home() / "Library" / "LaunchAgents" / f"{PLIST_LABEL}.plist"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hour", type=int, required=True, help="0-23, local time")
    parser.add_argument("--minute", type=int, default=0, help="0-59")
    args = parser.parse_args()

    python_bin = sys.executable
    content = TEMPLATE.read_text()
    content = (
        content.replace("{{PYTHON_BIN}}", python_bin)
        .replace("{{PROJECT_DIR}}", str(config.ROOT_DIR))
        .replace("{{HOUR}}", str(args.hour))
        .replace("{{MINUTE}}", str(args.minute))
    )

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(content)
    print(f"Wrote {DEST}")

    subprocess.run(["launchctl", "unload", str(DEST)], capture_output=True)
    subprocess.run(["launchctl", "load", str(DEST)], check=True)
    print(f"Scheduled daily run at {args.hour:02d}:{args.minute:02d} local time.")
    print(f"Logs: {config.LOG_DIR}")


if __name__ == "__main__":
    main()
