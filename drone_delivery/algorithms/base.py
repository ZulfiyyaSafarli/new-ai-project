"""Shared search node, step, result, and path reconstruction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SearchNode:
    """Search node; heap ordering is (priority, tie_breaker) in heapq tuples."""

    state: str
    parent: SearchNode | None = None
    g_cost: float = 0.0
    h_cost: float = 0.0
    f_cost: float = 0.0


@dataclass
class SearchStep:
    """One expansion step for visualization."""

    current: str
    frontier: list[str]
    explored: set[str]
    partial_path: list[str]
    g_cost: float
    node_costs: dict[str, tuple[float, float, float]]  # state -> (g, h, f)


@dataclass
class SearchResult:
    path: list[str]
    total_cost: float
    nodes_explored: int
    computation_time_ms: float
    feasible: bool


def reconstruct_path(node: SearchNode | None) -> list[str]:
    if node is None:
        return []
    path: list[str] = []
    cur: SearchNode | None = node
    while cur is not None:
        path.append(cur.state)
        cur = cur.parent
    path.reverse()
    return path


def build_node_costs_map(
    frontier_nodes: list[SearchNode],
    current: SearchNode,
) -> dict[str, tuple[float, float, float]]:
    """(g, h, f) for frontier nodes and current (best last-write wins for duplicates)."""
    m: dict[str, tuple[float, float, float]] = {}
    for n in frontier_nodes:
        m[n.state] = (n.g_cost, n.h_cost, n.f_cost)
    m[current.state] = (current.g_cost, current.h_cost, current.f_cost)
    return m
