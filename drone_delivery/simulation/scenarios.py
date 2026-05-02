"""Predefined delivery scenarios."""

SCENARIOS = [
    {
        "id": 1,
        "name": "Standard Delivery",
        "start": "Arad",
        "goal": "Bucharest",
        "battery": 450,
        "deadline": 500,
    },
    {
        "id": 2,
        "name": "Long Range",
        "start": "Oradea",
        "goal": "Eforie",
        "battery": 600,
        "deadline": 900,
    },
    {
        "id": 3,
        "name": "Tight Battery",
        "start": "Arad",
        "goal": "Bucharest",
        "battery": 300,
        "deadline": 500,
    },
    {
        "id": 4,
        "name": "Time-Critical",
        "start": "Timisoara",
        "goal": "Vaslui",
        "battery": 700,
        "deadline": 600,
    },
    {
        "id": 5,
        "name": "Constrained Cross-Country",
        "start": "Lugoj",
        "goal": "Iasi",
        "battery": 400,
        "deadline": 700,
    },
]
