"""Real-time 4-panel dashboard: graph animation, bars, table, g-cost line."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import RadioButtons

from drone_delivery.algorithms.astar import astar_steps
from drone_delivery.algorithms.base import SearchResult, SearchStep
from drone_delivery.algorithms.dijkstra import dijkstra_steps
from drone_delivery.algorithms.greedy import greedy_best_first_steps
from drone_delivery.graph import BATTERY_STATIONS, GRAPH, HEURISTIC, STEP_DELAY_MS, node_positions
from drone_delivery.simulation.runner import drone_from_scenario

from .results_plotter import make_bar_chart, make_cost_line, make_metrics_table


@dataclass
class AnimFrame:
    scenario: dict[str, Any]
    algorithm: str
    step: SearchStep
    g_history: list[float]
    phase: str  # "search" | "settle"
    final_path: list[str]


def _build_romania_graph() -> nx.Graph:
    G = nx.Graph()
    for u, nbrs in GRAPH.items():
        for v, w in nbrs:
            G.add_edge(u, v, weight=w)
    return G


def _scenario_has_feasible_path(results: dict[str, SearchResult]) -> bool:
    return any(r.feasible for r in results.values())


def build_animation_frames(
    per_scenario: list[tuple[dict[str, Any], dict[str, SearchResult], list[dict[str, Any]]]],
) -> list[AnimFrame]:
    """Sequential: each scenario × (A*, Dijkstra, Greedy); settle frames after each run.

    Scenarios where no algorithm finds a feasible path are omitted (no graph replay).
    """
    settle_n = max(3, int(1000 / STEP_DELAY_MS))
    frames: list[AnimFrame] = []
    algo_steps: list[tuple[str, Callable[..., Any]]] = [
        ("A*", astar_steps),
        ("Dijkstra", dijkstra_steps),
        ("Greedy BFS", greedy_best_first_steps),
    ]

    for sc, results, _ in per_scenario:
        if not _scenario_has_feasible_path(results):
            continue
        drone = drone_from_scenario(sc)
        start, goal = sc["start"], sc["goal"]
        for algo_name, steps_fn in algo_steps:
            gen = steps_fn(GRAPH, start, goal, HEURISTIC, drone, set(BATTERY_STATIONS))
            g_hist: list[float] = []
            last_step: SearchStep | None = None
            final_path: list[str] = []
            while True:
                try:
                    step = next(gen)
                    g_hist.append(step.g_cost)
                    last_step = step
                    frames.append(
                        AnimFrame(
                            scenario=sc,
                            algorithm=algo_name,
                            step=step,
                            g_history=list(g_hist),
                            phase="search",
                            final_path=[],
                        )
                    )
                except StopIteration as e:
                    res = e.value
                    final_path = list(res.path) if res.feasible else []
                    break

            if last_step is None:
                # No expansions (should not happen for non-empty graph)
                continue

            for _ in range(settle_n):
                frames.append(
                    AnimFrame(
                        scenario=sc,
                        algorithm=algo_name,
                        step=last_step,
                        g_history=list(g_hist),
                        phase="settle",
                        final_path=final_path,
                    )
                )
    return frames


class GraphDashboard:
    """Matplotlib + networkx live dashboard."""

    def __init__(
        self,
        per_scenario: list[tuple[dict[str, Any], dict[str, SearchResult], list[dict[str, Any]]]],
        all_rows: list[dict[str, Any]],
    ) -> None:
        self.per_scenario = per_scenario
        self.all_rows = all_rows
        self.metrics_df = pd.DataFrame(all_rows)
        scenarios = [t[0] for t in per_scenario]
        self.frames = build_animation_frames(per_scenario)
        self._rows_by_sid: dict[int, list[dict[str, Any]]] = {
            int(sc["id"]): rows for sc, _, rows in per_scenario
        }

        self.G = _build_romania_graph()
        self.pos = node_positions()

        self.fig = plt.figure(figsize=(14, 9))
        self.fig.subplots_adjust(left=0.05, right=0.98, top=0.92, bottom=0.08, wspace=0.3, hspace=0.35)
        gs = gridspec.GridSpec(
            2,
            3,
            figure=self.fig,
            width_ratios=[2.2, 2.0, 1.35],
            height_ratios=[2.4, 1.0],
            wspace=0.25,
            hspace=0.35,
        )
        self.ax_graph = self.fig.add_subplot(gs[0, 0:2])
        self.ax_table = self.fig.add_subplot(gs[0, 2])
        self.ax_bar = self.fig.add_subplot(gs[1, 0])
        self.ax_line = self.fig.add_subplot(gs[1, 1])
        self.ax_radio = self.fig.add_subplot(gs[1, 2])
        self.ax_radio.set_title("Y-axis metric", fontsize=9)
        self._metric = "total_cost"
        self._radio = RadioButtons(
            self.ax_radio,
            ("total_cost", "nodes_explored", "time_ms"),
            active=0,
        )
        self._radio.on_clicked(self._on_radio)

        make_bar_chart(self.ax_bar, self.metrics_df, self._metric)
        make_cost_line(self.ax_line, [])
        sid0 = scenarios[0]["id"] if scenarios else 1
        make_metrics_table(self.ax_table, self._rows_by_sid.get(int(sid0), []))

        self.fig.suptitle("Drone delivery — search replay", fontsize=12)

        self._anim: FuncAnimation | None = None

    def _on_radio(self, label: str) -> None:
        mapping = {
            "total_cost": "total_cost",
            "nodes_explored": "nodes_explored",
            "time_ms": "computation_time_ms",
        }
        self._metric = mapping.get(label, "total_cost")
        col = self._metric
        if col == "computation_time_ms" and col not in self.metrics_df.columns:
            col = "computation_time_ms"
        make_bar_chart(self.ax_bar, self.metrics_df, col)
        self.fig.canvas.draw_idle()

    def _node_colors(self, fr: AnimFrame) -> list[str]:
        step = fr.step
        path_set = set(fr.final_path) if fr.phase == "settle" and fr.final_path else set()
        cols: list[str] = []
        for n in self.G.nodes():
            if n in path_set:
                cols.append("#32cd32")  # limegreen
            elif n in step.explored:
                cols.append("#ff6347")  # tomato / explored
            elif n in step.frontier:
                cols.append("#ffd700")  # gold
            elif n in BATTERY_STATIONS:
                cols.append("#9b59b6")  # charging hub
            else:
                cols.append("#e8e8e8")  # unvisited
        return cols

    def _edge_colors(self, fr: AnimFrame) -> list[str]:
        step = fr.step
        path_set = set(fr.final_path) if fr.phase == "settle" and fr.final_path else set()
        ec: list[str] = []
        for u, v in self.G.edges():
            if fr.phase == "settle" and path_set:
                if u in path_set and v in path_set:
                    # edge on path if both endpoints consecutive in path
                    try:
                        iu = fr.final_path.index(u)
                        iv = fr.final_path.index(v)
                        if abs(iu - iv) == 1:
                            ec.append("#228b22")
                            continue
                    except ValueError:
                        pass
            if u in step.explored and v in step.explored:
                ec.append("#cccccc")
            else:
                ec.append("#bbbbbb")
        return ec

    def _node_labels(self, fr: AnimFrame) -> dict[str, str]:
        step = fr.step
        labels: dict[str, str] = {}
        algo = fr.algorithm
        for n in self.G.nodes():
            labels[n] = n
        for state, (g, h, f) in step.node_costs.items():
            if algo == "A*":
                extra = f"{g:.0f}/{h:.0f}/{f:.0f}"
            elif algo == "Dijkstra":
                extra = f"g={g:.0f}"
            else:
                extra = f"h={h:.0f}"
            labels[state] = f"{state}\n{extra}"
        return labels

    def _draw_graph(self, fr: AnimFrame) -> None:
        self.ax_graph.clear()
        sc = fr.scenario
        self.ax_graph.set_title(
            f"Scenario {sc['id']} — {sc['name']} | {fr.algorithm} | "
            f"{sc['start']} → {sc['goal']} | phase={fr.phase}",
            fontsize=10,
        )
        node_color = self._node_colors(fr)
        edge_color = self._edge_colors(fr)
        nx.draw_networkx_edges(
            self.G,
            self.pos,
            ax=self.ax_graph,
            edge_color=edge_color,
            width=1.2,
            alpha=0.9,
        )
        nx.draw_networkx_nodes(
            self.G,
            self.pos,
            ax=self.ax_graph,
            node_color=node_color,
            node_size=520,
            edgecolors="#333333",
            linewidths=1.0,
        )
        cur = fr.step.current
        cur_ec = "#f1c40f" if cur in BATTERY_STATIONS else "black"
        nx.draw_networkx_nodes(
            self.G,
            self.pos,
            nodelist=[cur],
            ax=self.ax_graph,
            node_color="#1e90ff",
            node_size=620,
            edgecolors=cur_ec,
            linewidths=2.0,
        )
        lbls = self._node_labels(fr)
        nx.draw_networkx_labels(
            self.G,
            self.pos,
            labels=lbls,
            ax=self.ax_graph,
            font_size=7,
            font_weight="bold",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", alpha=0.8, edgecolor="#888888"),
        )
        self.ax_graph.axis("off")
        self.ax_graph.set_aspect("equal")

    def _update(self, i: int) -> list[Any]:
        if i >= len(self.frames):
            return []
        fr = self.frames[i]
        self._draw_graph(fr)
        make_cost_line(self.ax_line, fr.g_history)
        sid = int(fr.scenario["id"])
        make_metrics_table(self.ax_table, self._rows_by_sid.get(sid, []))
        return []

    def run(self) -> None:
        if not self.frames:
            plt.show()
            return
        interval = int(STEP_DELAY_MS)
        self._anim = FuncAnimation(
            self.fig,
            self._update,
            frames=len(self.frames),
            interval=interval,
            repeat=True,
            blit=False,
        )
        plt.show()


def run_dashboard_headless_build_frames(
    per_scenario: list[tuple[dict[str, Any], dict[str, SearchResult], list[dict[str, Any]]]],
) -> int:
    """For tests: build frame count without displaying."""
    return len(build_animation_frames(per_scenario))
