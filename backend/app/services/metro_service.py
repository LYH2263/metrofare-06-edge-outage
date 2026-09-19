from app.db import connect
from app.engines.route_quote import quote_route
from app.repositories import disruptions as disruptions_repo
from app.repositories import edges as edges_repo
from app.repositories import fare_rules as rules_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import stations as stations_repo
import sqlite3


class DisruptionError(ValueError):
    """Registration/lift rejected; transaction must leave no active row."""


class MetroService:
    def __init__(self):
        self._conn = connect()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def stations(self):
        return stations_repo.list_all(self._conn)

    def station(self, code: str):
        return stations_repo.get_by_code(self._conn, code)

    def edges(self):
        active = {
            disruptions_repo.norm(d["a"], d["b"]): d
            for d in disruptions_repo.list_active(self._conn)
        }
        items = []
        for a, b in edges_repo.list_pairs(self._conn):
            d = active.get(disruptions_repo.norm(a, b))
            items.append(
                {
                    "a": a,
                    "b": b,
                    "disrupted": d is not None,
                    "reason": d["reason"] if d else None,
                }
            )
        return items

    def fare_rules(self):
        return rules_repo.list_ordered(self._conn)

    def settings(self):
        return settings_repo.get_map(self._conn)

    def disruptions(self):
        return disruptions_repo.list_all(self._conn)

    def register_disruption(self, a: str, b: str, reason: str) -> dict:
        """Register an active disruption on edge (a, b).

        All validation happens inside one transaction; any failure rolls back
        so no active disruption is ever left behind.
        """
        try:
            if not stations_repo.get_by_code(self._conn, a):
                raise DisruptionError(f"站点不存在: {a}")
            if not stations_repo.get_by_code(self._conn, b):
                raise DisruptionError(f"站点不存在: {b}")
            if not edges_repo.exists(self._conn, a, b):
                raise DisruptionError(f"邻接边不存在: {a} — {b}")
            if disruptions_repo.get_active_by_edge(self._conn, a, b):
                raise DisruptionError(f"该区间已存在生效中断: {a} — {b}")
            rid = disruptions_repo.insert(self._conn, a, b, reason)
            self._conn.commit()
        except sqlite3.IntegrityError as e:
            self._conn.rollback()
            raise DisruptionError(f"登记失败（可能已存在生效中断）: {a} — {b}") from e
        except Exception:
            self._conn.rollback()
            raise
        row = self._conn.execute(
            "SELECT id, a, b, reason, active, created_at, lifted_at "
            "FROM disruptions WHERE id=?",
            (rid,),
        ).fetchone()
        return dict(row)

    def lift_disruption(self, a: str, b: str) -> dict:
        try:
            n = disruptions_repo.deactivate_edge(self._conn, a, b)
            if n == 0:
                raise DisruptionError(f"该区间没有生效中断: {a} — {b}")
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return disruptions_repo.get_latest_by_edge(self._conn, a, b)

    def quote(self, start: str, end: str, persist: bool):
        edges = edges_repo.list_pairs(self._conn)
        rules = rules_repo.as_calc_rules(self._conn)
        blocked = disruptions_repo.active_pairs(self._conn)
        result = quote_route(edges, start, end, rules, blocked)
        # Read-only trial: persist=false never writes; unreachable never writes.
        run_id = None
        if persist and result.get("reachable"):
            run_id = runs_repo.insert(self._conn, "quote", {"start": start, "end": end}, result)
        return {"run_id": run_id, **result}

    def history(self, limit=50):
        return runs_repo.list_recent(self._conn, limit)

    def dashboard(self):
        st = stations_repo.list_all(self._conn)
        clean = [s for s in st if "种子" not in s["name"]]
        dirty = [s for s in st if "种子" in s["name"]]
        return {
            "station_count": len(st),
            "edge_count": len(edges_repo.list_pairs(self._conn)),
            "clean_stations": len(clean),
            "dirty_stations": len(dirty),
            "active_disruptions": len(disruptions_repo.list_active(self._conn)),
        }
