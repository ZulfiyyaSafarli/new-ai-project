"""Dijkstra's algorithm: f(n) = g(n), with per-edge battery and charging stations."""

from __future__ import annotations

import heapq
import itertools
import time
from collections.abc import Generator, Set

from drone_delivery.algorithms.base import (
    SearchNode,
    SearchResult,
    SearchStep,
    build_node_costs_map,
    reconstruct_path,
)
from drone_delivery.drone import battery_after_edge, deadline_ok
from drone_delivery.graph import BATTERY_STATIONS, GRAPH


def dijkstra_steps(
    graph: dict[str, list[tuple[str, int]]],
    start: str,
    goal: str,
    heuristic: dict[str, int],  # unused; kept for uniform API
    drone,
    charging_stations: Set[str],
) -> Generator[SearchStep, None, SearchResult]:
    _ = heuristic
    tie = itertools.count()
    capacity = int(drone.battery_capacity)
    start_bat = float(capacity)
    start_node = SearchNode(
        state=start,
        parent=None,
        g_cost=0.0,
        h_cost=0.0,
        f_cost=0.0,
        battery=start_bat,
    )
    heap: list[tuple[float, int, SearchNode]] = []
    heapq.heappush(heap, (start_node.g_cost, next(tie), start_node))

    explored_keys: set[tuple[str, int]] = set()
    explored_cities: set[str] = set()
    nodes_explored = 0

    while heap:
        _, _, node = heapq.heappop(heap)
        key = (node.state, int(round(node.battery)))
        if key in explored_keys:
            continue
        explored_keys.add(key)
        explored_cities.add(node.state)
        nodes_explored += 1

        partial = reconstruct_path(node)
        frontier_list = sorted({n.state for _, _, n in heap})
        frontier_nodes = [n for _, _, n in heap]
        node_costs = build_node_costs_map(frontier_nodes, node)

        yield SearchStep(
            current=node.state,
            frontier=frontier_list,
            explored=set(explored_cities),
            partial_path=partial,
            g_cost=node.g_cost,
            node_costs=node_costs,
            current_battery=node.battery,
        )

        if node.state == goal:
            return SearchResult(
                path=partial,
                total_cost=node.g_cost,
                nodes_explored=nodes_explored,
                computation_time_ms=0.0,
                feasible=True,
            )

        for nbr, edge_cost in graph.get(node.state, []):
            new_bat = battery_after_edge(
                node.battery, float(edge_cost), nbr, charging_stations, capacity
            )
            if new_bat is None:
                continue
            new_g = node.g_cost + edge_cost
            if not deadline_ok(drone, new_g):
                continue
            child = SearchNode(
                state=nbr,
                parent=node,
                g_cost=new_g,
                h_cost=0.0,
                f_cost=new_g,
                battery=new_bat,
            )
            heapq.heappush(heap, (new_g, next(tie), child))

    return SearchResult(
        path=[],
        total_cost=float("inf"),
        nodes_explored=nodes_explored,
        computation_time_ms=0.0,
        feasible=False,
    )


def dijkstra(
    graph: dict[str, list[tuple[str, int]]],
    start: str,
    goal: str,
    heuristic: dict[str, int],
    drone,
    charging_stations: Set[str],
) -> SearchResult:
    t0 = time.perf_counter()
    gen = dijkstra_steps(graph, start, goal, heuristic, drone, charging_stations)
    result: SearchResult | None = None
    try:
        while True:
            next(gen)
    except StopIteration as e:
        result = e.value
    assert result is not None
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return SearchResult(
        path=result.path,
        total_cost=result.total_cost,
        nodes_explored=result.nodes_explored,
        computation_time_ms=elapsed_ms,
        feasible=result.feasible,
    )


def default_dijkstra_steps(start: str, goal: str, heuristic: dict[str, int], drone):
    return dijkstra_steps(GRAPH, start, goal, heuristic, drone, set(BATTERY_STATIONS))
