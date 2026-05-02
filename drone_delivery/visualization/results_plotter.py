"""Static plotting helpers for the dashboard."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.table import Table

ALGO_ORDER = ["A*", "Dijkstra", "Greedy BFS"]


def make_bar_chart(ax: Axes, df: pd.DataFrame, metric: str) -> None:
    """Grouped bar chart: scenarios 1–5, groups = algorithms."""
    ax.clear()
    if df.empty or "scenario_id" not in df.columns:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return

    scenarios = sorted(df["scenario_id"].unique())
    x = np.arange(len(scenarios), dtype=float)
    width = 0.25

    def series_for_algo(algo: str) -> list[float]:
        vals: list[float] = []
        for sid in scenarios:
            row = df[(df["scenario_id"] == sid) & (df["algorithm"] == algo)]
            if row.empty:
                vals.append(0.0)
                continue
            v = float(row.iloc[0][metric])
            if not math.isfinite(v):
                vals.append(0.0)
            else:
                vals.append(v)
        return vals

    for i, algo in enumerate(ALGO_ORDER):
        heights = series_for_algo(algo)
        offset = (i - 1) * width
        ax.bar(x + offset, heights, width, label=algo)

    ax.set_xticks(x)
    ax.set_xticklabels([str(int(s)) for s in scenarios])
    ax.set_xlabel("Scenario")
    ylabel = {"total_cost": "Total cost", "nodes_explored": "Nodes explored", "computation_time_ms": "Time (ms)"}.get(
        metric, metric
    )
    ax.set_ylabel(ylabel)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title("Algorithm comparison")


def make_metrics_table(ax: Axes, rows: list[dict[str, Any]]) -> Table | None:
    """Draw a table of metrics for one scenario; returns table handle."""
    ax.clear()
    ax.axis("off")
    if not rows:
        ax.text(0.5, 0.5, "—", ha="center", va="center", transform=ax.transAxes)
        return None

    headers = ["Algorithm", "Cost", "Nodes", "Time(ms)", "Optimal", "Deadline"]
    cell_text = []
    for row in rows:
        cost = row["total_cost"]
        cost_s = "inf" if not math.isfinite(float(cost)) else str(int(cost))
        opt = "✓" if row["is_optimal"] else "✗"
        dl = "✓" if row["deadline_met"] else "✗"
        cell_text.append(
            [
                row["algorithm"],
                cost_s,
                str(row["nodes_explored"]),
                f"{row['computation_time_ms']:.2f}",
                opt,
                dl,
            ]
        )

    tbl = ax.table(
        cellText=cell_text,
        colLabels=headers,
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1.0, 1.4)
    ax.set_title("Metrics (current scenario)", fontsize=10, pad=8)
    return tbl


def make_cost_line(ax: Axes, g_history: list[float]) -> None:
    """Line chart: cumulative g after each expansion."""
    ax.clear()
    if not g_history:
        ax.set_title("Path cost g(n) per expansion")
        ax.set_xlabel("Expansion #")
        ax.set_ylabel("g cost")
        return
    ax.plot(range(1, len(g_history) + 1), g_history, color="tab:blue", linewidth=1.5)
    ax.set_title("Cumulative path cost g(n)")
    ax.set_xlabel("Expansion #")
    ax.set_ylabel("g cost")
    ax.grid(True, alpha=0.3)
