from modules.screener import ScanStore, new_saved_scan


def test_crud(tmp_path):
    store = ScanStore(tmp_path)
    scan = new_saved_scan("u1", "Momentum", "US", {"min_rsi": 60}, 20)
    saved = store.add(scan)
    assert saved.id == scan.id
    listed = store.list("u1")
    assert len(listed) == 1
    assert listed[0].name == "Momentum"
    assert listed[0].market == "US"
    assert listed[0].filters == {"min_rsi": 60}
    got = store.get("u1", scan.id)
    assert got is not None and got.limit == 20
    assert store.get("u1", "nope") is None
    assert store.delete("u1", scan.id) is True
    assert store.list("u1") == []
    assert store.delete("u1", scan.id) is False


def test_user_isolation(tmp_path):
    store = ScanStore(tmp_path)
    store.add(new_saved_scan("u1", "A", "IN", {}, 10))
    store.add(new_saved_scan("u2", "B", "US", {}, 10))
    assert [s.name for s in store.list("u1")] == ["A"]
    assert store.get("u1", "B") is None


def test_persistence(tmp_path):
    store = ScanStore(tmp_path)
    store.add(new_saved_scan("u1", "Breakout", "IN", {"min_change_1d_pct": 2}, 30))
    reloaded = ScanStore(tmp_path)
    scans = reloaded.list("u1")
    assert len(scans) == 1
    assert scans[0].filters == {"min_change_1d_pct": 2}
