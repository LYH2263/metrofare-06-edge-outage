import pytest

from app import seed
from app.db import connect
from app.services.metro_service import DisruptionError, MetroService


@pytest.fixture()
def db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("app.db.DB_PATH", db_path)
    seed.init_db()
    yield db_path


def _active_count(conn):
    return conn.execute("SELECT COUNT(*) c FROM disruptions WHERE active=1").fetchone()["c"]


def _run_count(conn):
    return conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]


def test_register_then_quote_detours(db):
    with MetroService() as s:
        s.register_disruption("A2", "B1", "区间检修")
        q = s.quote("A1", "B2", persist=True)
    assert q["reachable"]
    assert q["path"] == ["A1", "A2", "A3", "A4", "A5", "B2"]
    assert q["hops"] == 5
    assert q["fare"] == 6.0
    assert {"a": "A2", "b": "B1"} in q["detour_edges"]


def test_register_edge_reverse_orientation_normalized(db):
    with MetroService() as s:
        s.register_disruption("B1", "A2", "区间检修")
        edges = {d for e in s.edges() if e["disrupted"] for d in [(e["a"], e["b"])]}
    assert ("A2", "B1") in edges


def test_register_nonexistent_edge_leaves_no_active(db):
    with connect() as conn:
        before = _active_count(conn)
    with pytest.raises(DisruptionError):
        with MetroService() as s:
            s.register_disruption("A1", "B2", "不存在的边")
    with connect() as conn:
        assert _active_count(conn) == before


def test_register_nonexistent_station_leaves_no_active(db):
    with pytest.raises(DisruptionError):
        with MetroService() as s:
            s.register_disruption("A1", "ZZ", "幽灵站")
    with connect() as conn:
        assert _active_count(conn) == 0


def test_duplicate_register_rejected_and_single_active(db):
    with MetroService() as s:
        s.register_disruption("A2", "B1", "第一次")
        with pytest.raises(DisruptionError):
            s.register_disruption("A2", "B1", "重复登记")
    with connect() as conn:
        assert _active_count(conn) == 1


def test_unreachable_names_blocking_edge(db):
    with MetroService() as s:
        s.register_disruption("B2", "B3", "尽头封闭")
        q = s.quote("A1", "B3", persist=True)
    assert not q["reachable"]
    assert q["path"] == []
    assert {"a": "B2", "b": "B3"} in q["blocking_edges"]


def test_lift_restores_original_quote(db):
    with MetroService() as s:
        s.register_disruption("A2", "B1", "区间检修")
        detoured = s.quote("A1", "B2", persist=False)
        s.lift_disruption("A2", "B1")
        restored = s.quote("A1", "B2", persist=False)
    assert detoured["hops"] == 5
    assert restored["path"] == ["A1", "A2", "B1", "B2"]
    assert restored["hops"] == 3
    assert restored["fare"] == 4.0


def test_lift_without_active_is_error(db):
    with pytest.raises(DisruptionError):
        with MetroService() as s:
            s.lift_disruption("A2", "B1")


def test_read_only_trial_does_not_persist(db):
    with connect() as conn:
        before = _run_count(conn)
    with MetroService() as s:
        s.quote("A1", "A3", persist=False)
    with connect() as conn:
        assert _run_count(conn) == before


def test_unreachable_trial_does_not_persist_even_when_requested(db):
    with MetroService() as s:
        s.register_disruption("B2", "B3", "尽头封闭")
    with connect() as conn:
        before = _run_count(conn)
    with MetroService() as s:
        s.quote("A1", "B3", persist=True)
    with connect() as conn:
        assert _run_count(conn) == before


def test_history_snapshot_not_rewritten_after_later_disruption(db):
    with MetroService() as s:
        snap = s.quote("A1", "B2", persist=True)
        run_id = snap["run_id"]
        assert snap["path"] == ["A1", "A2", "B1", "B2"]
        # Later disruption changes live quotes...
        s.register_disruption("A2", "B1", "区间检修")
        changed = s.quote("A1", "B2", persist=False)
        assert changed["hops"] == 5
    # ...but the written record keeps the path as it was at write time.
    with MetroService() as s:
        rows = [r for r in s.history() if r["id"] == run_id]
    assert len(rows) == 1
    import json

    saved = json.loads(rows[0]["result_json"])
    assert saved["path"] == ["A1", "A2", "B1", "B2"]
    assert saved["hops"] == 3
    assert saved["fare"] == 4.0
