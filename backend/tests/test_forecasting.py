from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enrollment import EnrollmentRecord
from app.services.forecasting import EnrollmentForecastService


def seed_record(
    db: Session,
    academic_year: str,
    program: str,
    year_level: str,
    location: str,
    sex: str,
    count: int,
) -> None:
    db.add(
        EnrollmentRecord(
            academic_year=academic_year,
            program=program,
            year_level=year_level,
            sex=sex,
            location=location,
            enrollment_count=count,
        )
    )


def test_linear_forecast_aggregates_demographics_and_orders_history(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_record(db_session, "2023-2024", "BSIT", "1st Year", "Cebu City", "Male", 12)
    seed_record(db_session, "2021-2022", "BSIT", "1st Year", "Cebu City", "Female", 10)
    seed_record(db_session, "2022-2023", "BSIT", "1st Year", "Cebu City", "Male", 11)
    seed_record(db_session, "2021-2022", "BSIT", "1st Year", "Cebu City", "Male", 10)
    seed_record(db_session, "2022-2023", "BSIT", "1st Year", "Cebu City", "Female", 11)
    seed_record(db_session, "2023-2024", "BSIT", "1st Year", "Cebu City", "Female", 12)
    db_session.commit()

    response = client.post("/api/forecasts/generate", json={"horizon": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["horizon"] == 2
    assert body["skipped"] == []
    series = body["series"][0]
    assert series["program"] == "BSIT"
    assert series["year_level"] == "1st Year"
    assert series["location"] == "Cebu City"
    assert series["method"] == "linear_trend"
    assert series["observations_used"] == 3
    assert series["history"] == [
        {"academic_year": "2021-2022", "enrollment_count": 20},
        {"academic_year": "2022-2023", "enrollment_count": 22},
        {"academic_year": "2023-2024", "enrollment_count": 24},
    ]
    assert series["forecast"] == [
        {"academic_year": "2024-2025", "predicted_count": 26},
        {"academic_year": "2025-2026", "predicted_count": 28},
    ]


def test_gapped_history_uses_actual_years_and_linear_trend(
    client: TestClient,
    db_session: Session,
) -> None:
    for year, count in [
        ("2018-2019", 10),
        ("2020-2021", 14),
        ("2022-2023", 18),
        ("2024-2025", 22),
        ("2026-2027", 26),
    ]:
        seed_record(
            db_session,
            year,
            "BSCS",
            "2nd Year",
            "Mandaue City",
            "Female",
            count,
        )
    db_session.commit()

    response = client.post("/api/forecasts/generate", json={"horizon": 1})

    assert response.status_code == 200
    series = response.json()["series"][0]
    assert series["method"] == "linear_trend"
    assert series["forecast"] == [
        {"academic_year": "2027-2028", "predicted_count": 28}
    ]


def test_arima_is_selected_for_sufficient_contiguous_history(
    client: TestClient,
    db_session: Session,
) -> None:
    for year, count in enumerate([20, 22, 25, 27, 30, 33], start=2018):
        seed_record(
            db_session,
            f"{year}-{year + 1}",
            "BSBA",
            "3rd Year",
            "Cebu City",
            "Female",
            count,
        )
    db_session.commit()

    response = client.post("/api/forecasts/generate", json={"horizon": 3})

    assert response.status_code == 200
    series = response.json()["series"][0]
    assert series["method"] == "arima"
    assert len(series["forecast"]) == 3
    assert all(
        isinstance(point["predicted_count"], int)
        and point["predicted_count"] >= 0
        for point in series["forecast"]
    )


def test_arima_failure_falls_back_and_negative_results_are_clamped(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    for year, count in enumerate([40, 30, 20, 10, 0], start=2020):
        seed_record(
            db_session,
            f"{year}-{year + 1}",
            "BSIS",
            "1st Year",
            "Cebu City",
            "Male",
            count,
        )
    db_session.commit()

    def fail_arima(*_args, **_kwargs):
        raise RuntimeError("model failure")

    monkeypatch.setattr(EnrollmentForecastService, "_forecast_arima", fail_arima)
    response = client.post("/api/forecasts/generate", json={"horizon": 2})

    assert response.status_code == 200
    series = response.json()["series"][0]
    assert series["method"] == "linear_trend"
    assert series["forecast"][0]["predicted_count"] == 0
    assert series["forecast"][1]["predicted_count"] == 0


def test_location_filter_reports_insufficient_and_missing_series(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_record(db_session, "2022-2023", "BSIT", "1st Year", "Cebu City", "Female", 10)
    seed_record(db_session, "2023-2024", "BSIT", "1st Year", "Cebu City", "Female", 12)
    seed_record(db_session, "2023-2024", "BSIT", "1st Year", "Mandaue City", "Male", 8)
    db_session.commit()

    response = client.post(
        "/api/forecasts/generate",
        json={
            "horizon": 1,
            "programs": ["bsit"],
            "year_levels": ["1st Year"],
            "locations": ["Cebu City", "Mandaue City", "Unknown Town"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert [
        (series["program"], series["year_level"], series["location"])
        for series in body["series"]
    ] == [("BSIT", "1st Year", "Cebu City")]
    assert body["skipped"] == [
        {
            "program": "BSIT",
            "year_level": "1st Year",
            "location": "Mandaue City",
            "reason": "At least 2 historical academic years are required.",
        },
        {
            "program": "BSIT",
            "year_level": "1st Year",
            "location": "Unknown Town",
            "reason": "No historical enrollment data was found.",
        },
    ]


def test_forecast_accepts_freeform_program_filter(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_record(db_session, "2022-2023", "BSN", "1st Year", "Cebu City", "Female", 10)
    seed_record(db_session, "2023-2024", "BSN", "1st Year", "Cebu City", "Female", 12)
    seed_record(db_session, "2022-2023", "BSIT", "1st Year", "Cebu City", "Male", 20)
    seed_record(db_session, "2023-2024", "BSIT", "1st Year", "Cebu City", "Male", 22)
    db_session.commit()

    response = client.post(
        "/api/forecasts/generate",
        json={"horizon": 1, "programs": ["bsn"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["series"]) == 1
    assert body["series"][0]["program"] == "BSN"


def test_empty_data_insufficient_data_and_request_validation(
    client: TestClient,
    db_session: Session,
) -> None:
    empty = client.post("/api/forecasts/generate", json={})
    assert empty.status_code == 422
    assert (
        empty.json()["detail"]["message"]
        == "No historical enrollment data is available."
    )

    seed_record(db_session, "2023-2024", "BSIT", "1st Year", "Cebu City", "Female", 10)
    db_session.commit()
    insufficient = client.post("/api/forecasts/generate", json={})
    assert insufficient.status_code == 422
    skipped = insufficient.json()["detail"]["skipped"][0]
    assert skipped["program"] == "BSIT"
    assert skipped["location"] == "Cebu City"

    assert (
        client.post("/api/forecasts/generate", json={"horizon": 0}).status_code
        == 422
    )
    assert (
        client.post("/api/forecasts/generate", json={"horizon": 6}).status_code
        == 422
    )
    duplicate_programs = client.post(
        "/api/forecasts/generate",
        json={"programs": ["BSIT", "bsit"]},
    )
    assert duplicate_programs.status_code == 422
