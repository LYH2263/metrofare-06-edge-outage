from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_hops, shortest_path
from app.engines.route_quote import quote_route

EDGES = [
    ("A1", "A2"),
    ("A2", "A3"),
    ("A3", "A4"),
    ("A4", "A5"),
    ("A5", "B2"),
    ("A2", "B1"),
    ("B1", "B2"),
    ("B2", "B3"),
]
RULES = [
    {"max_hops": 2, "price": 3.0},
    {"max_hops": 4, "price": 4.0},
    {"max_hops": None, "price": 6.0},
]


def test_hops_a1_a3():
    assert shortest_hops(EDGES, "A1", "A3") == 2


def test_hops_a1_b2():
    assert shortest_hops(EDGES, "A1", "B2") == 3


def test_fare_by_hops():
    assert fare_for_hops(2, RULES) == 3.0
    assert fare_for_hops(3, RULES) == 4.0
    assert fare_for_hops(10, RULES) == 6.0


def test_quote_baseline():
    q = quote_route(EDGES, "A1", "B2", RULES)
    assert q["reachable"]
    assert q["hops"] == 3
    assert q["fare"] == 4.0
    assert q["path"] == ["A1", "A2", "B1", "B2"]


def test_quote_detour_when_edge_blocked():
    # Blocking the direct corridor A2-B1 forces the long loop.
    q = quote_route(EDGES, "A1", "B2", RULES, blocked=[("A2", "B1")])
    assert q["reachable"]
    assert q["path"] == ["A1", "A2", "A3", "A4", "A5", "B2"]
    assert q["hops"] == 5
    assert q["fare"] == 6.0
    assert {"a": "A2", "b": "B1"} in q["detour_edges"]
    assert "B1" not in q["path"]


def test_blocked_edge_orientation_insensitive():
    assert shortest_path(EDGES, "A1", "B2", blocked=[("B1", "A2")]) == [
        "A1",
        "A2",
        "A3",
        "A4",
        "A5",
        "B2",
    ]


def test_quote_unreachable_names_blocking_edge_and_no_fabrication():
    # B3 is a leaf hanging off B2; blocking B2-B3 strands it.
    q = quote_route(EDGES, "A1", "B3", RULES, blocked=[("B2", "B3")])
    assert not q["reachable"]
    assert q["hops"] is None
    assert q["fare"] is None
    assert q["path"] == []
    assert {"a": "B2", "b": "B3"} in q["blocking_edges"]
    assert q["detour_edges"] == []


def test_unreachable_does_not_blame_unrelated_active_edge():
    # A2-B1 is active-disrupted but irrelevant to reaching leaf B3 once B2-B3
    # is also cut... both cuts coexist; the blamed set must still include the
    # actually stranding edge and must never invent a path.
    q = quote_route(
        EDGES, "A1", "B3", RULES, blocked=[("A2", "B1"), ("B2", "B3")]
    )
    assert not q["reachable"]
    assert q["path"] == []
    assert {"a": "B2", "b": "B3"} in q["blocking_edges"]


def test_lift_restores_original_path_hops_fare():
    blocked_quote = quote_route(EDGES, "A1", "B2", RULES, blocked=[("A2", "B1")])
    assert blocked_quote["hops"] == 5
    lifted = quote_route(EDGES, "A1", "B2", RULES)
    assert lifted["path"] == ["A1", "A2", "B1", "B2"]
    assert lifted["hops"] == 3
    assert lifted["fare"] == 4.0


def test_start_equals_end():
    assert shortest_path(EDGES, "A1", "A1") == ["A1"]
    assert shortest_hops(EDGES, "A1", "A1") == 0
