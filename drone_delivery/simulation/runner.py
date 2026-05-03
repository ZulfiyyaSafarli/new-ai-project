"""Run scenarios, collect metrics, print tables, export CSV."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

from drone_delivery.algorithms.base import SearchResult
from drone_delivery.algorithms.astar import astar
from drone_delivery.algorithms.dijkstra import dijkstra
from drone_delivery.algorithms.greedy import greedy_best_first
from drone_delivery.drone import Drone
from drone_delivery.graph import BATTERY_STATIONS, GRAPH, HEURISTIC

ALGO_KEYS = ("A*", "Dijkstra", "Greedy BFS")
_STATIONS: set[str] = set(BATTERY_STATIONS)


def _edge_weight(graph: dict[str, list[tuple[str, int]]], a: str, b: str) -> float | None:
    for nbr, w in graph.get(a, []):
        if nbr == b:
            return float(w)
    return None


def path_battery_stats(
    path: list[str],
    graph: dict[str, list[tuple[str, int]]],
    charging_stations: set[str],
    capacity: int,
) -> tuple[float, int, float]:
    """Peak drain between full charges, station arrivals (recharges), final battery at goal."""
    if len(path) < 2:
        return (float("nan"), 0, float(capacity))
    bat = float(capacity)
    leg = 0.0
    peak = 0.0
    recharges = 0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        w = _edge_weight(graph, u, v)
        if w is None or bat < w:
            return (float("nan"), 0, float("nan"))
        bat -= w
        leg += w
        if v in charging_stations:
            peak = max(peak, leg)
            leg = 0.0
            recharges += 1
            bat = float(capacity)
    peak = max(peak, leg)
    return (peak, recharges, bat)


def drone_from_scenario(scenario: dict[str, Any]) -> Drone:
    return Drone(
        id=f"D{scenario['id']}",
        battery_capacity=int(scenario["battery"]),
        current_battery=int(scenario["battery"]),
        speed=60.0,
        payload=2.0,
        deadline=int(scenario["deadline"]),
    )


def run_scenario(scenario: dict[str, Any]) -> dict[str, SearchResult]:
    drone = drone_from_scenario(scenario)
    start, goal = scenario["start"], scenario["goal"]
    return {
        "A*": astar(GRAPH, start, goal, HEURISTIC, drone, _STATIONS),
        "Dijkstra": dijkstra(GRAPH, start, goal, HEURISTIC, drone, _STATIONS),
        "Greedy BFS": greedy_best_first(GRAPH, start, goal, HEURISTIC, drone, _STATIONS),
    }


def _is_optimal(
    name: str,
    result: SearchResult,
    results: dict[str, SearchResult],
) -> bool:
    if not result.feasible:
        return False
    d = results["Dijkstra"]
    if d.feasible:
        return math.isclose(result.total_cost, d.total_cost, rel_tol=0, abs_tol=1e-6)
    feasible_costs = [
        r.total_cost for k, r in results.items() if r.feasible and math.isfinite(r.total_cost)
    ]
    if not feasible_costs:
        return False
    best = min(feasible_costs)
    return math.isclose(result.total_cost, best, rel_tol=0, abs_tol=1e-6)


def evaluate(
    scenario: dict[str, Any],
    results: dict[str, SearchResult],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    deadline = int(scenario["deadline"])
    cap = int(scenario["battery"])
    for name in ALGO_KEYS:
        r = results[name]
        path = r.path
        cost = r.total_cost
        if r.feasible and path:
            peak_leg, n_recharge, final_b = path_battery_stats(path, GRAPH, _STATIONS, cap)
            battery_consumption = float(cost)  # sum of edge weights == total trip distance
        else:
            peak_leg, n_recharge, final_b = float("nan"), 0, float("nan")
            battery_consumption = float("nan")
        rows.append(
            {
                "scenario_id": scenario["id"],
                "scenario_name": scenario["name"],
                "algorithm": name,
                "path": path,
                "total_cost": cost if r.feasible else float("inf"),
                "nodes_explored": r.nodes_explored,
                "computation_time_ms": r.computation_time_ms,
                "battery_consumption": battery_consumption,
                "battery_peak_leg_drain": peak_leg,
                "recharge_visits": n_recharge,
                "final_battery": final_b,
                "path_length": max(len(path) - 1, 0) if path else 0,
                "is_optimal": _is_optimal(name, r, results),
                "deadline_met": r.feasible and cost <= deadline,
                "feasible": r.feasible,
            }
        )
    return rows


def _format_path(path: list[str], max_len: int = 42) -> str:
    if not path:
        return "—"
    s = "→".join(path)
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "…"


def print_scenario_table(scenario: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    sid = scenario["id"]
    name = scenario["name"]
    start, goal = scenario["start"], scenario["goal"]
    bat, dl = scenario["battery"], scenario["deadline"]
    line = "━" * 40
    print(line)
    print(f"Scenario {sid} — {name}")
    print(f"Start: {start}  →  Goal: {goal}")
    print(f"Battery: {bat}  |  Deadline: {dl}")
    print(line)
    header = f"{'Algorithm':<14} {'Path':<42} {'Cost':>6} {'Nodes':>6} {'Time(ms)':>9} {'Optimal':>8}"
    print(header)
    for row in rows:
        algo = row["algorithm"]
        p = _format_path(row["path"])
        if row["feasible"]:
            cost_s = f"{int(row['total_cost'])}"
        else:
            cost_s = "inf"
        opt = "✓" if row["is_optimal"] else "✗"
        print(
            f"{algo:<14} {p:<42} {cost_s:>6} {row['nodes_explored']:>6} "
            f"{row['computation_time_ms']:>9.2f} {opt:>8}"
        )
    print()


def export_metrics(all_rows: list[dict[str, Any]], path: str | Path | None = None) -> Path:
    if path is None:
        path = Path(__file__).resolve().parent.parent / "results" / "metrics.csv"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(all_rows)
    # CSV-friendly path column
    if "path" in df.columns:
        df["path"] = df["path"].apply(
            lambda p: "→".join(p) if isinstance(p, list) and p else ""
        )
    df.to_csv(path, index=False)
    return path
