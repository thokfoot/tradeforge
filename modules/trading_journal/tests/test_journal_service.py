import pytest

from modules.shared.contracts.interfaces import Analytics
from modules.trading_journal import JournalService, JournalStore
from modules.trading_journal.service import JournalEntry


@pytest.fixture
def service(tmp_path):
    return JournalService(JournalStore(tmp_path / "journal"))


def test_add_entry(service):
    entry = service.add_entry("u1", "t1", "good setup", symbol="RELIANCE", pnl=120.5)
    assert entry.entry_id
    assert entry.note == "good setup"
    assert entry.symbol == "RELIANCE"
    assert entry.pnl == 120.5
    assert entry.created_at is not None


def test_list_entries_roundtrip(service):
    service.add_entry("u1", "t1", "note one")
    service.add_entry("u1", "t2", "note two", tags=["sma", "trend"], rating=4)
    entries = service.list_entries("u1")
    assert len(entries) == 2
    assert isinstance(entries[0], JournalEntry)
    assert entries[1].tags == ["sma", "trend"]
    assert entries[1].rating == 4


def test_entries_isolated_per_user(service):
    service.add_entry("u1", "t1", "mine")
    assert service.list_entries("u2") == []


def test_delete_entry(service):
    entry = service.add_entry("u1", "t1", "to delete")
    assert service.delete_entry("u1", entry.entry_id) is True
    assert service.delete_entry("u1", "missing") is False
    assert service.list_entries("u1") == []


def test_validate_note_required(service):
    with pytest.raises(ValueError):
        service.add_entry("u1", "t1", "   ")


def test_validate_rating(service):
    with pytest.raises(ValueError):
        service.add_entry("u1", "t1", "ok", rating=7)


def test_satisfies_analytics_contract(service):
    assert isinstance(service, Analytics)
