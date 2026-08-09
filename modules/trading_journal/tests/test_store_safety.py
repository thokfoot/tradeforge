import pytest

from modules.alerts.store import AlertStore
from modules.education.store import EducationStore
from modules.market_data.storage.parquet_store import ParquetStore
from modules.trading_journal.store import JournalStore
from modules.watchlists.store import WatchlistStore


@pytest.mark.parametrize(
    "store_factory",
    [
        lambda p: JournalStore(p),
        lambda p: AlertStore(p),
        lambda p: WatchlistStore(p),
        lambda p: EducationStore(p),
    ],
)
@pytest.mark.parametrize("bad_id", ["../../auth/users", "..%2Fetc%2Fpasswd", "a/b", "..\\..\\x", ""])
def test_per_user_stores_reject_traversal(store_factory, bad_id, tmp_path):
    store = store_factory(tmp_path)
    with pytest.raises(ValueError):
        store._file(bad_id)


def test_parquet_store_rejects_traversal(tmp_path):
    store = ParquetStore(tmp_path)
    with pytest.raises(ValueError):
        store._path("..", "1d", "AAPL")
    with pytest.raises(ValueError):
        store._path("US", "..", "AAPL")
    with pytest.raises(ValueError):
        store._path("US", "1d", "../../tmp/pwn")
