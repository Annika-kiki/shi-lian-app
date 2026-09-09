import pytest

from backend.services.auth import InvalidSession, create_session_token, verify_session_token


def test_signed_session_round_trip():
    token = create_session_token(42, "account-nonce", "unit-test-secret", 60)
    assert verify_session_token(token, "unit-test-secret") == (42, "account-nonce")


def test_signed_session_rejects_wrong_secret():
    token = create_session_token(42, "account-nonce", "correct-secret", 60)
    with pytest.raises(InvalidSession):
        verify_session_token(token, "wrong-secret")


def test_signed_session_rejects_expired_token():
    token = create_session_token(42, "account-nonce", "unit-test-secret", 1)
    with pytest.raises(InvalidSession):
        verify_session_token(token, "unit-test-secret", now=10**12)


@pytest.mark.parametrize("token", ["", ".", "%%%...", "bm90LWpzb24.signature"])
def test_signed_session_rejects_malformed_tokens(token):
    with pytest.raises(InvalidSession):
        verify_session_token(token, "unit-test-secret")
