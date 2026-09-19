import sqlite3
from datetime import datetime, timezone


def norm(a: str, b: str) -> tuple[str, str]:
    """Canonical undirected ordering of an edge's endpoint codes."""
    return (a, b) if a <= b else (b, a)


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, a, b, reason, active, created_at, lifted_at "
        "FROM disruptions ORDER BY id DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def list_active(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, a, b, reason, active, created_at, lifted_at "
        "FROM disruptions WHERE active=1 ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


def active_pairs(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    return [(r["a"], r["b"]) for r in conn.execute(
        "SELECT a, b FROM disruptions WHERE active=1"
    ).fetchall()]


def get_active_by_edge(conn: sqlite3.Connection, a: str, b: str) -> dict | None:
    x, y = norm(a, b)
    row = conn.execute(
        "SELECT * FROM disruptions WHERE a=? AND b=? AND active=1", (x, y)
    ).fetchone()
    return dict(row) if row else None


def get_latest_by_edge(conn: sqlite3.Connection, a: str, b: str) -> dict | None:
    x, y = norm(a, b)
    row = conn.execute(
        "SELECT id, a, b, reason, active, created_at, lifted_at "
        "FROM disruptions WHERE a=? AND b=? ORDER BY id DESC LIMIT 1",
        (x, y),
    ).fetchone()
    return dict(row) if row else None


def insert(conn: sqlite3.Connection, a: str, b: str, reason: str) -> int:
    x, y = norm(a, b)
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO disruptions(a, b, reason, active, created_at) VALUES (?,?,?,1,?)",
        (x, y, reason, now),
    )
    return int(cur.lastrowid)


def deactivate_edge(conn: sqlite3.Connection, a: str, b: str) -> int:
    """Lift the active disruption on an edge; returns number of rows lifted."""
    x, y = norm(a, b)
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "UPDATE disruptions SET active=0, lifted_at=? WHERE a=? AND b=? AND active=1",
        (now, x, y),
    )
    return cur.rowcount
