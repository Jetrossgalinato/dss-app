from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text

from app.core.config import settings
from app.desktop import run_migrations, sqlite_url


def test_sqlite_migrations_and_data_persist_across_connections(
    tmp_path: Path,
) -> None:
    database = tmp_path / "enrollment.sqlite3"
    database_url = sqlite_url(database)

    run_migrations(database_url)
    engine = create_engine(database_url)
    assert "enrollment_records" in inspect(engine).get_table_names()
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO enrollment_records
                    (academic_year, class_level, sex, enrollment_count)
                VALUES
                    ('2025-2026', 'Nursery', 'Female', 18)
                """
            )
        )
    engine.dispose()

    reopened = create_engine(database_url)
    with reopened.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM enrollment_records")) == 1
    reopened.dispose()


def test_desktop_api_token_is_required(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "api_token", "secret-token")

    unauthorized = client.get("/api/enrollments")
    authorized = client.get(
        "/api/enrollments",
        headers={"X-DSS-Token": "secret-token"},
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


def test_desktop_api_allows_cors_preflight(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "api_token", "secret-token")

    response = client.options(
        "/api/enrollments",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-DSS-Token",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://127.0.0.1:5173"
    )


def test_health_confirms_database_readiness(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ready"}
