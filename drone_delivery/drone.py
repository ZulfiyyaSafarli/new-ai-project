"""Drone model and battery helpers."""

from collections.abc import Set
from dataclasses import dataclass


@dataclass
class Drone:
    id: str
    battery_capacity: int  # max battery units (e.g. 450)
    current_battery: int  # current battery
    speed: float  # km/h
    payload: float  # kg
    deadline: int  # max allowed path cost (delivery time window)


def remaining_battery(drone: Drone, g_cost: float) -> float:
    """Remaining battery after traveling path cost g_cost (1:1 with edge cost)."""
    return float(drone.battery_capacity) - float(g_cost)


def edge_feasible(drone: Drone, g_so_far: float, edge_cost: float) -> bool:
    """True if we can take this edge from state with accumulated cost g_so_far."""
    new_g = g_so_far + edge_cost
    if remaining_battery(drone, new_g) < 0:
        return False
    if new_g > drone.deadline:
        return False
    return True


def deadline_ok(drone: Drone, new_g: float) -> bool:
    return new_g <= float(drone.deadline)


def battery_after_edge(
    battery: float,
    edge_cost: float,
    dest: str,
    charging_stations: Set[str],
    capacity: int,
) -> float | None:
    """Battery after traversing one edge to dest; full recharge if dest is a station. None if drain impossible."""
    w = float(edge_cost)
    if battery < w:
        return None
    b = battery - w
    if dest in charging_stations:
        return float(capacity)
    return b
