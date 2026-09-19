import json

from app.db import connect
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
STATIONS = [
    ("A1", "城站"),
    ("A2", "市心"),
    ("A3", "东湾"),
    ("A4", "江口"),
    ("A5", "岭北"),
    ("B1", "北苑"),
    ("B2", "机场"),
    ("B3", "机库"),
]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]

SCHEMA = """
CREATE TABLE IF NOT EXISTS stations(id INTEGER PRIMARY KEY, code TEXT, name TEXT);
CREATE TABLE IF NOT EXISTS edges(a TEXT, b TEXT);
CREATE TABLE IF NOT EXISTS fare_rules(id INTEGER PRIMARY KEY, max_hops INTEGER, price REAL);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS disruptions(
    id INTEGER PRIMARY KEY,
    a TEXT NOT NULL,
    b TEXT NOT NULL,
    reason TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    lifted_at TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS ux_active_edge
    ON disruptions(a, b) WHERE active=1;
CREATE TABLE IF NOT EXISTS calc_runs(
    id INTEGER PRIMARY KEY, kind TEXT, input_json TEXT, result_json TEXT, created_at TEXT);
"""


def _existing_edge_set(conn) -> set[tuple[str, str]]:
    return {tuple(sorted((r["a"], r["b"]))) for r in conn.execute("SELECT a,b FROM edges")}


def _ensure_stations_and_edges(conn):
    """Idempotent top-up so upgraded databases gain later-added stations/edges."""
    codes = {r["code"] for r in conn.execute("SELECT code FROM stations").fetchall()}
    for code, name in STATIONS:
        if code not in codes:
            conn.execute("INSERT INTO stations(code, name) VALUES (?,?)", (code, name))
    edges = _existing_edge_set(conn)
    for a, b in EDGES:
        if tuple(sorted((a, b))) not in edges:
            conn.execute("INSERT INTO edges(a,b) VALUES (?,?)", (a, b))


def init_db():
    conn = connect()
    conn.executescript(SCHEMA)
    fresh = conn.execute("SELECT COUNT(*) c FROM stations").fetchone()["c"] == 0
    if fresh:
        for code, name in STATIONS:
            conn.execute("INSERT INTO stations(code, name) VALUES (?,?)", (code, name))
        for a, b in EDGES:
            conn.execute("INSERT INTO edges(a,b) VALUES (?,?)", (a, b))
        conn.executemany(
            "INSERT INTO fare_rules(max_hops, price) VALUES (?,?)",
            [(2, 3.0), (4, 4.0), (None, 6.0)],
        )
        conn.execute("INSERT INTO settings(key,value) VALUES ('currency','CNY')")
        q1 = quote_route(EDGES, "A1", "A3", RULES)
        conn.execute(
            "INSERT INTO calc_runs(kind,input_json,result_json,created_at) VALUES (?,?,?,datetime('now'))",
            ("quote", json.dumps({"start": "A1", "end": "A3"}), json.dumps(q1, ensure_ascii=False)),
        )
    else:
        _ensure_stations_and_edges(conn)
    conn.commit()
    conn.close()
