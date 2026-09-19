from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import canonical_edge, shortest_path


def _edges_on_path(path: list[str]) -> set[tuple[str, str]]:
    return {canonical_edge(path[i], path[i + 1]) for i in range(len(path) - 1)}


def quote_route(
    edges: list[tuple[str, str]],
    start: str,
    end: str,
    rules: list[dict],
    blocked_edges: list[tuple[str, str]] | None = None,
) -> dict:
    """按最少站数询价。生效中断边不得进入最短路。

    - 去掉中断边后仍连通：给出新的途经站 path、新站数 hops、新票价 fare，
      并在 avoided_edges 中点名绕开的边。
    - 不连通：reachable=False，path=None（不编造途经站），blocked_edges 点名被挡的边。
    """
    blocked = [canonical_edge(a, b) for a, b in (blocked_edges or [])]
    base = {
        "start": start,
        "end": end,
        "hops": None,
        "fare": None,
        "reachable": False,
        "path": None,
        "detoured": False,
        "avoided_edges": [],
        "blocked_edges": [],
    }

    path = shortest_path(edges, start, end, blocked)
    if path is None:
        # 点名被挡的边：无中断时最短路上被登记为生效中断的边。
        # 若删掉这些边后起终点不连通，则原最短路必经过其中至少一条。
        original = shortest_path(edges, start, end)
        if original is not None and blocked:
            hit = sorted(_edges_on_path(original).intersection(blocked))
            base["blocked_edges"] = [{"a": a, "b": b} for a, b in hit]
        return base

    original = shortest_path(edges, start, end)
    hops = len(path) - 1
    base.update(hops=hops, fare=fare_for_hops(hops, rules), reachable=True, path=path)
    if original is not None:
        hit = sorted(_edges_on_path(original).intersection(blocked))
        if hit and path != original:
            base["detoured"] = True
            base["avoided_edges"] = [{"a": a, "b": b} for a, b in hit]
    return base
