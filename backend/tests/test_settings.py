from dataclasses import replace

import pytest

from backend.config.settings import database_url_from_env, settings, validate_production_settings


def test_cloud_mysql_environment_builds_encoded_sqlalchemy_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("MYSQL_ADDRESS", "10.17.102.105:3306")
    monkeypatch.setenv("MYSQL_USERNAME", "shi_lian_app")
    monkeypatch.setenv("MYSQL_PASSWORD", "special@pass:/word")
    monkeypatch.setenv("MYSQL_DATABASE", "shi_lian")
    assert database_url_from_env() == (
        "mysql+pymysql://shi_lian_app:special%40pass%3A%2Fword@"
        "10.17.102.105:3306/shi_lian?charset=utf8mb4"
    )


def test_incomplete_cloud_mysql_environment_fails_closed_to_local_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("MYSQL_ADDRESS", "10.17.102.105:3306")
    monkeypatch.setenv("MYSQL_USERNAME", "shi_lian_app")
    monkeypatch.delenv("MYSQL_PASSWORD", raising=False)
    assert database_url_from_env() == "sqlite:///./shi_lian.db"


def test_development_defaults_are_allowed():
    validate_production_settings(replace(settings, app_env="development"))


def test_production_rejects_development_defaults():
    unsafe = replace(
        settings,
        app_env="production",
        database_url="sqlite:///./shi_lian.db",
        cors_origins="*",
        allowed_hosts="*",
        wechat_app_id="",
        wechat_app_secret="",
        session_secret="development-only-change-me",
    )
    with pytest.raises(RuntimeError, match="Unsafe deployed configuration"):
        validate_production_settings(unsafe)


def test_staging_rejects_development_defaults():
    unsafe = replace(settings, app_env="staging")
    with pytest.raises(RuntimeError, match="Unsafe deployed configuration"):
        validate_production_settings(unsafe)


def test_production_accepts_complete_configuration():
    safe = replace(
        settings,
        app_env="production",
        database_url="mysql+pymysql://app:password@db.internal/app?charset=utf8mb4",
        cors_origins="https://api.example.com",
        allowed_hosts="api.example.com",
        wechat_app_id="wx26dfe00bf5f3258b",
        wechat_app_secret="configured-outside-git-secret",
        session_secret="a-unique-session-secret-with-32-plus-characters",
    )
    validate_production_settings(safe)


def test_production_accepts_cloud_header_auth_without_app_secret():
    safe = replace(
        settings,
        app_env="production",
        auth_mode="cloud_headers",
        database_url="mysql+pymysql://app:password@db.internal/app?charset=utf8mb4",
        cors_origins="https://api.example.com",
        allowed_hosts="api.example.com",
        wechat_app_id="wx26dfe00bf5f3258b",
        wechat_app_secret="",
        wechat_cloud_env_id="prod-d4g1s6f9gaef2c320",
        session_secret="a-unique-session-secret-with-32-plus-characters",
    )
    validate_production_settings(safe)


@pytest.mark.parametrize("app_env", ["prodution", "", "test"])
def test_rejects_unknown_environment_names(app_env):
    with pytest.raises(RuntimeError, match="Invalid APP_ENV"):
        validate_production_settings(replace(settings, app_env=app_env))


def test_rejects_unknown_auth_mode():
    with pytest.raises(RuntimeError, match="Invalid AUTH_MODE"):
        validate_production_settings(replace(settings, auth_mode="trust_everything"))


@pytest.mark.parametrize(
    ("field", "invalid_value", "message"),
    [
        ("db_pool_size", 0, "DB_POOL_SIZE"),
        ("db_max_overflow", -1, "DB_MAX_OVERFLOW"),
        ("db_pool_timeout_seconds", 0, "DB_POOL_TIMEOUT_SECONDS"),
        ("db_pool_recycle_seconds", 10, "DB_POOL_RECYCLE_SECONDS"),
    ],
)
def test_rejects_unsafe_database_pool_limits(field, invalid_value, message):
    with pytest.raises(RuntimeError, match=message):
        validate_production_settings(replace(settings, **{field: invalid_value}))


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("database_url", ""),
        ("database_url", "postgresql://app:password@db/app"),
        ("cors_origins", ""),
        ("cors_origins", " * "),
        ("cors_origins", "http://api.example.com"),
        ("cors_origins", "https://api.example.com/path"),
        ("allowed_hosts", ""),
        ("allowed_hosts", " * "),
        ("allowed_hosts", "*.example.com"),
        ("allowed_hosts", "https://api.example.com"),
        ("wechat_app_id", "wx-test"),
        ("wechat_app_secret", "short"),
    ],
)
def test_deployed_configuration_rejects_malformed_values(field, invalid_value):
    safe = replace(
        settings,
        app_env="production",
        database_url="mysql+pymysql://app:password@db.internal/app?charset=utf8mb4",
        cors_origins="https://api.example.com",
        allowed_hosts="api.example.com",
        wechat_app_id="wx26dfe00bf5f3258b",
        wechat_app_secret="configured-outside-git-secret",
        session_secret="a-unique-session-secret-with-32-plus-characters",
    )
    with pytest.raises(RuntimeError, match="Unsafe deployed configuration"):
        validate_production_settings(replace(safe, **{field: invalid_value}))
