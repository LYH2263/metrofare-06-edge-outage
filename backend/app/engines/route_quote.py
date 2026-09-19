from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_path


def _edge_key(edge: tuple[str, str]) -> frozenset[str]:
    return frozenset(edge)


def quote_route(
    edges: list[tuple[str, str]],
    start: str,
    end: str,
    rules: list[dict],
    blocked: list[tuple[str, str]] | None = None,
) -> dict:
    """Quote over the graph with blocked edges removed.

    Reachable: returns the new path/hops/fare and ``detour_edges`` -- the
    active blocked edges that the disruption-free shortest path would have
    used. Unreachable: names exactly the blocked edges whose individual
    restoration reconnects start to end, and never fabricates a path.
    """
    active = blocked or []
    base = {"start": start, "end": end}
    path = shortest_path(edges, start, end, active)
    if path is None:
        blocking = []
        for a, b in active:
            others = [e for e in active if _edge_key(e) != _edge_key((a, b))]
            if shortest_path(edges, start, end, others) is not None:
                blocking.append({"a": a, "b": b})
        return {
            **base,
            "hops": None,
            "fare": None,
            "reachable": False,
            "path": [],
            "detour_edges": [],
            "blocking_edges": blocking,
        }
    hops = len(path) - 1
    fare = fare_for_hops(hops, rules)
    baseline = shortest_path(edges, start, end)
    baseline_edges = (
        {_edge_key((u, v)) for u, v in zip(baseline, baseline[1:])} if baseline else set()
    )
    detour = [
        {"a": a, "b": b} for a, b in active if _edge_key((a, b)) in baseline_edges
    ]
    return {
        **base,
        "hops": hops,
        "fare": fare,
        "reachable": True,
        "path": path,
        "detour_edges": detour,
        "blocking_edges": [],
    }
