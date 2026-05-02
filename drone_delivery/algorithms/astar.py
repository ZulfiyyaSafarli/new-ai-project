"""A* search: f(n) = g(n) + h(n)."""

from __future__ import annotations

import heapq
import itertools
import time
from collections.abc import Generator

from drone_delivery.algorithms.base import (
    SearchNode,
    SearchResult,
    SearchStep,
    build_node_costs_map,
    reconstruct_path,
)
from drone_delivery.drone import edge_feasible
from drone_delivery.graph import GRAPH


def _h(state: str, goal: str, heuristic: dict[str, int]) -> float:
    if state == goal:
        return 0.0
    return float(heuristic.get(state, 0))


def astar_steps(
    graph: dict[str, list[tuple[str, int]]],
    start: str,
    goal: str,
    heuristic: dict[str, int],
    drone,
) -> Generator[SearchStep, None, SearchResult]:
    tie = itertools.count()
    h0 = _h(start, goal, heuristic)
    start_node = SearchNode(
        state=start,
        parent=None,
        g_cost=0.0,
        h_cost=h0,
        f_cost=h0,
    )
    heap: list[tuple[float, int, SearchNode]] = []
    heapq.heappush(heap, (start_node.f_cost, next(tie), start_node))

    explored: set[str] = set()
    frontier_states: set[str] = {start}
    nodes_explored = 0

    while heap:
        _, _, node = heapq.heappop(heap)
        if node.state in explored:
            continue
        explored.add(node.state)
        nodes_explored += 1
        frontier_states.discard(node.state)

        partial = reconstruct_path(node)
        frontier_list = sorted(frontier_states)
        frontier_nodes = [n for _, _, n in heap]
        node_costs = build_node_costs_map(frontier_nodes, node)

        yield SearchStep(
            current=node.state,
            frontier=frontier_list,
            explored=set(explored),
            partial_path=partial,
            g_cost=node.g_cost,
            node_costs=node_costs,
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
            if nbr in explored:
                continue
            if not edge_feasible(drone, node.g_cost, float(edge_cost)):
                continue
            new_g = node.g_cost + edge_cost
            hn = _h(nbr, goal, heuristic)
            fn = new_g + hn
            child = SearchNode(
                state=nbr,
                parent=node,
                g_cost=new_g,
                h_cost=hn,
                f_cost=fn,
            )
            heapq.heappush(heap, (fn, next(tie), child))
            frontier_states.add(nbr)

    return SearchResult(
        path=[],
        total_cost=float("inf"),
        nodes_explored=nodes_explored,
        computation_time_ms=0.0,
        feasible=False,
    )


def astar(
    graph: dict[str, list[tuple[str, int]]],
    start: str,
    goal: str,
    heuristic: dict[str, int],
    drone,
) -> SearchResult:
    t0 = time.perf_counter()
    gen = astar_steps(graph, start, goal, heuristic, drone)
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


def default_astar_steps(start: str, goal: str, heuristic: dict[str, int], drone):
    return astar_steps(GRAPH, start, goal, heuristic, drone)
