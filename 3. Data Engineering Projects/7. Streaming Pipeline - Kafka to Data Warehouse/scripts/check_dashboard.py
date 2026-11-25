"""Headless render check for the monitoring dashboard.

Streamlit's own test harness executes the app script the same way `streamlit run`
does, so this catches import errors, bad SQL and layout exceptions without a
browser. Used by CI after the integration tests.

Usage:
    python -m scripts.check_dashboard
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DASHBOARD_AUTO_REFRESH", "0")

from streamlit.testing.v1 import AppTest  # noqa: E402 - must follow the env default

# AppTest resolves relative paths against this file, so anchor on the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP = str(PROJECT_ROOT / "src" / "monitoring" / "dashboard.py")


def main() -> int:
    app = AppTest.from_file(APP, default_timeout=120)
    app.run()

    if app.exception:
        for exc in app.exception:
            print(f"EXCEPTION: {exc.value}")
        return 1

    metrics = app.get("metric")
    tabs = app.get("tabs")
    print(f"rendered: {len(metrics)} metrics, {len(tabs)} tab group(s)")

    labels = [metric.label for metric in metrics]
    expected = {"Raw records", "Orders", "Payments", "Max partition lag", "Open dead letters"}
    missing = expected - set(labels)
    if missing:
        print(f"MISSING METRICS: {sorted(missing)}")
        return 1

    print("dashboard renders cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
