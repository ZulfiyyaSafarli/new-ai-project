"""Romania road map (AIMA) and straight-line heuristic to Bucharest."""

STEP_DELAY_MS = 300

GRAPH = {
    "Arad": [("Zerind", 75), ("Sibiu", 140), ("Timisoara", 118)],
    "Zerind": [("Arad", 75), ("Oradea", 71)],
    "Oradea": [("Zerind", 71), ("Sibiu", 151)],
    "Sibiu": [
        ("Arad", 140),
        ("Oradea", 151),
        ("Fagaras", 99),
        ("Rimnicu Vilcea", 80),
    ],
    "Timisoara": [("Arad", 118), ("Lugoj", 111)],
    "Lugoj": [("Timisoara", 111), ("Mehadia", 70)],
    "Mehadia": [("Lugoj", 70), ("Drobeta", 75)],
    "Drobeta": [("Mehadia", 75), ("Craiova", 120)],
    "Craiova": [
        ("Drobeta", 120),
        ("Rimnicu Vilcea", 146),
        ("Pitesti", 138),
    ],
    "Rimnicu Vilcea": [
        ("Sibiu", 80),
        ("Craiova", 146),
        ("Pitesti", 97),
    ],
    "Fagaras": [("Sibiu", 99), ("Bucharest", 211)],
    "Pitesti": [
        ("Rimnicu Vilcea", 97),
        ("Craiova", 138),
        ("Bucharest", 101),
    ],
    "Bucharest": [
        ("Fagaras", 211),
        ("Pitesti", 101),
        ("Giurgiu", 90),
        ("Urziceni", 85),
    ],
    "Giurgiu": [("Bucharest", 90)],
    "Urziceni": [
        ("Bucharest", 85),
        ("Hirsova", 98),
        ("Vaslui", 142),
    ],
    "Hirsova": [("Urziceni", 98), ("Eforie", 86)],
    "Eforie": [("Hirsova", 86)],
    "Vaslui": [("Urziceni", 142), ("Iasi", 92)],
    "Iasi": [("Vaslui", 92), ("Neamt", 87)],
    "Neamt": [("Iasi", 87)],
}

HEURISTIC = {
    "Arad": 366,
    "Bucharest": 0,
    "Craiova": 160,
    "Drobeta": 242,
    "Eforie": 161,
    "Fagaras": 176,
    "Giurgiu": 77,
    "Hirsova": 151,
    "Iasi": 226,
    "Lugoj": 244,
    "Mehadia": 241,
    "Neamt": 234,
    "Oradea": 380,
    "Pitesti": 100,
    "Rimnicu Vilcea": 193,
    "Sibiu": 253,
    "Timisoara": 329,
    "Urziceni": 80,
    "Vaslui": 199,
    "Zerind": 374,
}


def node_positions() -> dict[str, tuple[float, float]]:
    """Approximate geographic layout (x, y) for visualization."""
    return {
        "Arad": (1.0, 4.2),
        "Zerind": (0.5, 4.8),
        "Oradea": (0.8, 5.5),
        "Sibiu": (2.2, 4.0),
        "Timisoara": (0.2, 3.2),
        "Lugoj": (0.8, 2.8),
        "Mehadia": (1.2, 2.2),
        "Drobeta": (1.8, 1.8),
        "Craiova": (2.8, 1.5),
        "Rimnicu Vilcea": (2.5, 3.2),
        "Fagaras": (3.2, 3.8),
        "Pitesti": (3.8, 2.8),
        "Bucharest": (5.0, 2.5),
        "Giurgiu": (4.8, 1.5),
        "Urziceni": (5.5, 3.2),
        "Hirsova": (6.5, 3.5),
        "Eforie": (7.2, 3.2),
        "Vaslui": (6.2, 4.8),
        "Iasi": (6.8, 5.5),
        "Neamt": (6.5, 6.2),
    }
