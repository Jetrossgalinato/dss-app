from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enrollment import EnrollmentRecord
from app.services.forecasting import EnrollmentForecastService
from app.services.reporting import DashboardReportService
from app.services.response_cache import (
    bump_data_version,
    dashboard_cache,
    data_version,
    enrollment_list_cache,
    forecast_cache,
    reset_for_tests,
)


def seed_pair(db: Session, year: str, count: int) -> None:
    db.add_all(
        [
            EnrollmentRecord(
                academic_year=year,
                program="BSIT",
                year_level="1st Year",
                sex="Female",
                location="Cebu City",
                enrollment_count=count,
            ),
            EnrollmentRecord(
                academic_year=year,
                program="BSIT",
                year_level="1st Year",
                sex="Male",
                location="Cebu City",
                enrollment_count=count,
            ),
        ]
    )


def upload(client: TestClient, csv: str):
    return client.post(
        "/api/enrollments/import",
        files={"file": ("enrollment.csv", csv.encode("utf-8"), "text/csv")},
    )


def test_dashboard_reuses_cache_until_enrollment_mutates(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_pair(db_session, "2022-2023", 10)
    seed_pair(db_session, "2023-2024", 12)
    db_session.commit()

    payload = {"horizon": 1, "max_class_size": 25}
    original = DashboardReportService.generate
    calls = {"count": 0}

    def counting_generate(self, db, request):
        calls["count"] += 1
        return original(self, db, request)

    with patch.object(DashboardReportService, "generate", counting_generate):
        first = client.post("/api/reports/dashboard", json=payload)
        second = client.post("/api/reports/dashboard", json=payload)
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["summary"] == second.json()["summary"]
        assert calls["count"] == 1
        assert len(dashboard_cache) == 1

    version_before = data_version()
    deleted_id = client.get("/api/enrollments").json()["items"][0]["id"]
    assert client.delete(f"/api/enrollments/{deleted_id}").status_code == 200
    assert data_version() == version_before + 1

    calls["count"] = 0
    with patch.object(DashboardReportService, "generate", counting_generate):
        third = client.post("/api/reports/dashboard", json=payload)
        assert third.status_code == 200
        assert calls["count"] == 1


def test_forecast_cache_cleared_after_import(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_pair(db_session, "2022-2023", 10)
    seed_pair(db_session, "2023-2024", 12)
    db_session.commit()

    payload = {"horizon": 1}
    original = EnrollmentForecastService.generate
    calls = {"count": 0}

    def counting_generate(self, db, request):
        calls["count"] += 1
        return original(self, db, request)

    with patch.object(EnrollmentForecastService, "generate", counting_generate):
        assert client.post("/api/forecasts/generate", json=payload).status_code == 200
        assert client.post("/api/forecasts/generate", json=payload).status_code == 200
        assert calls["count"] == 1
        assert len(forecast_cache) == 1

    imported = upload(
        client,
        "academic_year,program,year_level,sex,location,enrollment_count\n"
        "2024-2025,BSIT,1st Year,Female,Cebu City,14\n"
        "2024-2025,BSIT,1st Year,Male,Cebu City,14\n",
    )
    assert imported.status_code == 200
    assert len(forecast_cache) == 0

    calls["count"] = 0
    with patch.object(EnrollmentForecastService, "generate", counting_generate):
        assert client.post("/api/forecasts/generate", json=payload).status_code == 200
        assert calls["count"] == 1


def test_reset_for_tests_clears_version_and_entries() -> None:
    bump_data_version()
    enrollment_list_cache.set(("x",), {"ok": True})
    assert data_version() > 0
    assert len(enrollment_list_cache) == 1
    reset_for_tests()
    assert data_version() == 0
    assert len(enrollment_list_cache) == 0
