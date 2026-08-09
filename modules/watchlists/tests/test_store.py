import json
import tempfile
from pathlib import Path

from modules.watchlists.store import WatchlistStore


def test_add_and_list():
    with tempfile.TemporaryDirectory() as tmp:
        store = WatchlistStore(Path(tmp))
        result = store.add("u1", "US", "AAPL")
        assert "US" in result
        assert "AAPL" in result["US"]

        result = store.add("u1", "US", "TSLA")
        assert result["US"] == ["AAPL", "TSLA"]

        result = store.add("u1", "IN", "RELIANCE")
        assert "IN" in result
        assert result["IN"] == ["RELIANCE"]


def test_remove():
    with tempfile.TemporaryDirectory() as tmp:
        store = WatchlistStore(Path(tmp))
        store.add("u1", "US", "AAPL")
        store.add("u1", "US", "TSLA")
        result = store.remove("u1", "US", "AAPL")
        assert result["US"] == ["TSLA"]


def test_duplicate_ignored():
    with tempfile.TemporaryDirectory() as tmp:
        store = WatchlistStore(Path(tmp))
        store.add("u1", "US", "AAPL")
        result = store.add("u1", "US", "AAPL")
        assert result["US"] == ["AAPL"]


def test_list_empty():
    with tempfile.TemporaryDirectory() as tmp:
        store = WatchlistStore(Path(tmp))
        assert store.list("u1") == {}


def test_per_user_isolation():
    with tempfile.TemporaryDirectory() as tmp:
        store = WatchlistStore(Path(tmp))
        store.add("u1", "US", "AAPL")
        store.add("u2", "US", "MSFT")
        assert store.list("u1") == {"US": ["AAPL"]}
        assert store.list("u2") == {"US": ["MSFT"]}
