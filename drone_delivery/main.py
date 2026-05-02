"""Entry point: run all scenarios, print tables, export CSV, optional live dashboard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Support `python drone_delivery/main.py` from repo root
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

from drone_delivery.simulation.runner import (
    evaluate,
    export_metrics,
    print_scenario_table,
    run_scenario,
)
from drone_delivery.simulation.scenarios import SCENARIOS
from drone_delivery.visualization.graph_animator import GraphDashboard


def main() -> None:
    parser = argparse.ArgumentParser(description="Drone delivery route optimization (Romania graph)")
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Skip matplotlib dashboard (console + CSV only)",
    )
    args = parser.parse_args()

    all_rows: list = []
    per_scenario: list = []

    for scenario in SCENARIOS:
        results = run_scenario(scenario)
        rows = evaluate(scenario, results)
        print_scenario_table(scenario, rows)
        all_rows.extend(rows)
        per_scenario.append((scenario, results, rows))

    csv_path = export_metrics(all_rows)
    print(f"Metrics written to: {csv_path}")

    if args.no_gui:
        return

    dash = GraphDashboard(per_scenario, all_rows)
    dash.run()


if __name__ == "__main__":
    main()
