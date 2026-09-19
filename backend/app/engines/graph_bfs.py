from collections import defaultdict, deque
from typing import Iterable

Edge = tuple[str, str]


def _norm(edge: Edge) -> frozenset[str]:
    return frozenset(edge)


def build_graph(edges: Iterable[Edge], blocked: Iterable[Edge] | None = None) -> dict[str, set[str]]:
    """Undirected adjacency; edges in blocked are excluded."""
    blocked_set = {_norm(e) for e in (blocked or [])}
    g: dict[str, set[str]] = defaultdict(set)
    for a, b in edges:
        if _norm((a, b)) in blocked_set:
            continue
        g[a].add(b)
        g[b].add(a)
    return g


def shortest_path(
    edges: Iterable[Edge], start: str, end: str, blocked: Iterable[Edge] | None = None
) -> list[str] | None:
    """BFS shortest path as a station-code sequence [start, ..., end]; None if unreachable."""
    g = build_graph(edges, blocked)
    if start == end:
        return [start]
    if start not in g or end not in g:
        return None
    q = deque([start])
    parent = {start: None}
    while q:
        cur = q.popleft()
        for nxt in g[cur]:
            if nxt in parent:
                continue
            parent[nxt] = cur
            if nxt == end:
                path = [end]
                while parent[path[-1]] is not None:
                    path.append(parent[path[-1]])
                path.reverse()
                return path
            q.append(nxt)
    return None


def shortest_hops(edges: list[tuple[str, str]], start: str, end: str) -> int | None:
    """Undirected graph BFS hop count; None if unreachable."""
    path = shortest_path(edges, start, end)
    if path is None:
        return None
    return len(path) - 1
