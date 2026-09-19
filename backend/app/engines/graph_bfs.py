from collections import defaultdict, deque


def _build_graph(edges: list[tuple[str, str]]):
    g: dict[str, set[str]] = defaultdict(set)
    for a, b in edges:
        g[a].add(b)
        g[b].add(a)
    return g


def canonical_edge(a: str, b: str) -> tuple[str, str]:
    """无向边按两端编码排序归一化。"""
    return tuple(sorted((a, b)))


def _normalize_blocked(blocked_edges):
    """无向边按端点编码排序归一化，便于与图中邻接做比较。"""
    blocked = set()
    for a, b in blocked_edges or []:
        blocked.add(canonical_edge(a, b))
    return blocked


def shortest_path(
    edges: list[tuple[str, str]],
    start: str,
    end: str,
    blocked_edges: list[tuple[str, str]] | None = None,
) -> list[str] | None:
    """无向图 BFS 最短路（站数最少）；中断生效边不得进入最短路。

    返回途经站编码列表（含起终点）；不可达时返回 None。
    """
    if start == end:
        return [start]
    blocked = _normalize_blocked(blocked_edges)
    g = _build_graph(edges)
    if start not in g or end not in g:
        return None
    q = deque([start])
    prev: dict[str, str | None] = {start: None}
    while q:
        cur = q.popleft()
        for nxt in g[cur]:
            if nxt in prev:
                continue
            if tuple(sorted((cur, nxt))) in blocked:
                continue  # 生效中断边不得进入最短路
            prev[nxt] = cur
            if nxt == end:
                path = [end]
                while prev[path[-1]] is not None:
                    path.append(prev[path[-1]])
                path.reverse()
                return path
            q.append(nxt)
    return None


def shortest_hops(
    edges: list[tuple[str, str]],
    start: str,
    end: str,
    blocked_edges: list[tuple[str, str]] | None = None,
) -> int | None:
    """Undirected graph BFS hop count; None if unreachable."""
    path = shortest_path(edges, start, end, blocked_edges)
    if path is None:
        return None
    return len(path) - 1
