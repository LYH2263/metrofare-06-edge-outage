import sqlite3


def list_pairs(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    return [(r["a"], r["b"]) for r in conn.execute("SELECT a,b FROM edges").fetchall()]


def exists(conn: sqlite3.Connection, a: str, b: str) -> bool:
    """Undirected membership check for an adjacency edge."""
    row = conn.execute(
        "SELECT 1 FROM edges WHERE (a=? AND b=?) OR (a=? AND b=?) LIMIT 1",
        (a, b, b, a),
    ).fetchone()
    return row is not None
