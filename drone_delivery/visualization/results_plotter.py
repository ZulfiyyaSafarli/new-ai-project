"""Static plotting helpers for the dashboard."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.table import Table

ALGO_ORDER = ["A*", "Dijkstra", "Greedy BFS"]


def _clear_bar_axis_and_twins(ax: Axes) -> None:
    """Remove twinx siblings sharing the same subplot cell, then clear the primary axis."""
    fig = ax.figure
    ss = ax.get_subplotspec()
    if ss is not None:
        for other in list(fig.axes):
            if other is not ax and other.get_subplotspec() == ss:
                other.remove()
    ax.clear()


def _series_for_algo(
    df: pd.DataFrame, scenarios: list, algo: str, metric: str
) -> tuple[list[float], list[bool]]:
    """Values; `failed` means infeasible run (hatch bars) — only used for total_cost display."""
    vals: list[float] = []
    failed: list[bool] = []
    for sid in scenarios:
        row = df[(df["scenario_id"] == sid) & (df["algorithm"] == algo)]
        if row.empty:
            vals.append(0.0)
            failed.append(False)
            continue
        r0 = row.iloc[0]
        feas = bool(r0.get("feasible", False))
        try:
            v = float(r0[metric])
        except (KeyError, TypeError, ValueError):
            v = float("nan")

        if metric == "total_cost":
            if not feas or not math.isfinite(v):
                vals.append(float("nan"))
                failed.append(True)
            else:
                vals.append(v)
                failed.append(False)
        else:
            failed.append(False)
            if not math.isfinite(v):
                vals.append(0.0)
            else:
                vals.append(v)
    return vals, failed


def make_bar_chart(ax: Axes, df: pd.DataFrame, metric: str) -> None:
    """Grouped bar chart: scenarios 1–5, groups = algorithms. Infeasible runs are hatched, not drawn as zero."""
    _clear_bar_axis_and_twins(ax)
    if df.empty or "scenario_id" not in df.columns:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return

    scenarios = sorted(df["scenario_id"].unique())
    x = np.arange(len(scenarios), dtype=float)
    width = 0.25

    finite_caps: list[float] = []
    for algo in ALGO_ORDER:
        vals, _ = _series_for_algo(df, scenarios, algo, metric)
        finite_caps.extend([v for v in vals if math.isfinite(v)])
    max_fin = max(finite_caps) if finite_caps else 1.0
    fail_height = max(max_fin * 1.12, max_fin + 1.0, 1.0)

    for i, algo in enumerate(ALGO_ORDER):
        vals, failed = _series_for_algo(df, scenarios, algo, metric)
        plot_vals = [fail_height if f and math.isnan(v) else (0.0 if not math.isfinite(v) else v) for v, f in zip(vals, failed)]
        offset = (i - 1) * width
        bars = ax.bar(x + offset, plot_vals, width, label=algo)
        if metric == "total_cost":
            for rect, f in zip(bars.patches, failed):
                if f:
                    rect.set_hatch("xx")
                    rect.set_alpha(0.55)

    ax.set_xticks(x)
    ax.set_xticklabels([str(int(s)) for s in scenarios])
    ax.set_xlabel("Scenario")
    ylabel = {
        "total_cost": "Total cost (hatched = infeasible)",
        "nodes_explored": "Nodes explored",
        "computation_time_ms": "Time (ms)",
        "battery_peak_leg_drain": "Peak leg battery drain",
        "battery_consumption": "Battery consumption (sum edges)",
        "recharge_visits": "Recharge stops",
    }.get(metric, metric)
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

    headers = ["Algo", "Cost", "Peak", "Rchg", "FinBat", "Nodes", "T(ms)", "Opt", "DL"]
    cell_text = []
    for row in rows:
        cost = row["total_cost"]
        cost_s = "inf" if not math.isfinite(float(cost)) else str(int(cost))
        peak = row.get("battery_peak_leg_drain", float("nan"))
        peak_s = "—" if not math.isfinite(float(peak)) else str(int(peak))
        rchg = row.get("recharge_visits", 0)
        fb = row.get("final_battery", float("nan"))
        fb_s = "—" if not math.isfinite(float(fb)) else str(int(fb))
        opt = "✓" if row["is_optimal"] else "✗"
        dl = "✓" if row["deadline_met"] else "✗"
        cell_text.append(
            [
                row["algorithm"],
                cost_s,
                peak_s,
                str(int(rchg)),
                fb_s,
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
    tbl.set_fontsize(7)
    tbl.scale(1.0, 1.35)
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
