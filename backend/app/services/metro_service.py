import json

from app.db import connect
from app.engines.route_quote import quote_route
from app.repositories import disruptions as disruptions_repo
from app.repositories import edges as edges_repo
from app.repositories import fare_rules as rules_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import stations as stations_repo


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
        return [{"a": a, "b": b} for a, b in edges_repo.list_pairs(self._conn)]

    def fare_rules(self):
        return rules_repo.list_ordered(self._conn)

    def settings(self):
        return settings_repo.get_map(self._conn)

    # ---- 区间中断 ----
    def disruptions(self):
        return disruptions_repo.list_all(self._conn)

    def create_disruption(self, a: str, b: str, reason: str):
        return disruptions_repo.create(self._conn, a, b, reason, active=True)

    def release_disruption(self, disruption_id: int):
        return disruptions_repo.release(self._conn, disruption_id)

    def quote(self, start: str, end: str, persist: bool):
        edges = edges_repo.list_pairs(self._conn)
        rules = rules_repo.as_calc_rules(self._conn)
        active = disruptions_repo.list_active(self._conn)
        result = quote_route(
            edges, start, end, rules, blocked_edges=[(d["a"], d["b"]) for d in active]
        )
        # 附上中断原因，前端可以直接展示“绕开/被挡的是哪条边、为何中断”
        reason_by_edge = {(d["a"], d["b"]): d for d in active}
        for key in ("avoided_edges", "blocked_edges"):
            for e in result.get(key, []):
                d = reason_by_edge.get((e["a"], e["b"]))
                if d:
                    e["disruption_id"] = d["id"]
                    e["reason"] = d["reason"]
        run_id = None
        if persist and result.get("reachable"):
            run_id = runs_repo.insert(self._conn, "quote", {"start": start, "end": end}, result)
        return {"run_id": run_id, **result}

    def history(self, limit=50):
        # result_json/input_json 是落库当时的完整快照；解除中断后也不得改写，
        # 这里只解析给前端展示，不回写数据库。
        items = []
        for row in runs_repo.list_recent(self._conn, limit):
            d = dict(row)
            d["input"] = json.loads(d.pop("input_json") or "{}")
            d["result"] = json.loads(d.pop("result_json") or "{}")
            items.append(d)
        return items

    def dashboard(self):
        st = stations_repo.list_all(self._conn)
        clean = [s for s in st if "种子" not in s["name"]]
        dirty = [s for s in st if "种子" in s["name"]]
        return {
            "station_count": len(st),
            "edge_count": len(edges_repo.list_pairs(self._conn)),
            "clean_stations": len(clean),
            "dirty_stations": len(dirty),
        }
