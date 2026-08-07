import pytest

from modules.auth_billing import AuthService, UserStore
from modules.shared.contracts.interfaces import AuthService as AuthContract


@pytest.fixture
def service(tmp_path):
    return AuthService(UserStore(tmp_path / "auth"))


def test_implements_contract(service):
    assert isinstance(service, AuthContract)


def test_register_creates_free_user(service):
    user = service.register("a@b.com", "password123")
    assert user.plan == "free"
    assert user.email == "a@b.com"


def test_register_normalizes_email(service):
    user = service.register("  A@B.COM  ", "password123")
    assert user.email == "a@b.com"


def test_register_invalid_email(service):
    with pytest.raises(ValueError):
        service.register("not-an-email", "password123")


def test_register_short_password(service):
    with pytest.raises(ValueError):
        service.register("a@b.com", "short")


def test_register_duplicate_email(service):
    service.register("a@b.com", "password123")
    with pytest.raises(ValueError):
        service.register("a@b.com", "password456")


def test_login_roundtrip(service):
    service.register("a@b.com", "password123")
    session = service.login("a@b.com", "password123")
    assert session.token
    user = service.user_for_token(session.token)
    assert user is not None and user.email == "a@b.com"


def test_login_wrong_password(service):
    service.register("a@b.com", "password123")
    with pytest.raises(ValueError):
        service.login("a@b.com", "wrongpass")


def test_login_unknown_user(service):
    with pytest.raises(ValueError):
        service.login("nobody@b.com", "password123")


def test_subscription_upgrade(service):
    user = service.register("a@b.com", "password123")
    upgraded = service.create_subscription(user.id, "pro")
    assert upgraded.plan == "pro"
    assert service.get_user(user.id).plan == "pro"


def test_subscription_invalid_plan(service):
    user = service.register("a@b.com", "password123")
    with pytest.raises(ValueError):
        service.create_subscription(user.id, "platinum")


def test_expired_session_invalid(service):
    service.register("a@b.com", "password123")
    session = service.login("a@b.com", "password123")
    from datetime import datetime, timedelta

    service._store.create_session(
        "stale-token", session.user_id, datetime.now() - timedelta(minutes=1)
    )
    assert service.user_for_token("stale-token") is None
    assert service.user_for_token(session.token) is not None


def test_password_hash_not_plaintext(service):
    service.register("a@b.com", "password123")
    record = service._store.find_by_email("a@b.com")
    assert record["password_hash"].startswith("pbkdf2_sha256$")
    assert "password123" not in record["password_hash"]
