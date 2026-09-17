from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enrollment import EnrollmentRecord


def seed(
    db: Session,
    year: str,
    level: str,
    male: int,
    female: int,
) -> None:
    db.add_all(
        [
            EnrollmentRecord(
                academic_year=year,
                class_level=level,
                sex="Male",
                enrollment_count=male,
            ),
            EnrollmentRecord(
                academic_year=year,
                class_level=level,
                sex="Female",
                enrollment_count=female,
            ),
        ]
    )


def test_dashboard_composes_history_forecast_sections_and_summary(
    client: TestClient,
    db_session: Session,
) -> None:
    seed(db_session, "2021-2022", "Nursery", 8, 12)
    seed(db_session, "2022-2023", "Nursery", 10, 12)
    seed(db_session, "2023-2024", "Nursery", 12, 14)
    db_session.commit()

    response = client.post(
        "/api/reports/dashboard",
        json={"horizon": 2, "max_class_size": 10},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["available_class_levels"] == ["Nursery"]
    assert body["historical"] == [
        {
            "academic_year": "2021-2022",
            "class_level": "Nursery",
            "male": 8,
            "female": 12,
            "total": 20,
        },
        {
            "academic_year": "2022-2023",
            "class_level": "Nursery",
            "male": 10,
            "female": 12,
            "total": 22,
        },
        {
            "academic_year": "2023-2024",
            "class_level": "Nursery",
            "male": 12,
            "female": 14,
            "total": 26,
        },
    ]
    assert body["summary"] == {
        "latest_academic_year": "2023-2024",
        "latest_enrollment": 26,
        "year_over_year_change_percent": 18.18,
        "next_academic_year": "2024-2025",
        "next_year_forecast": 29,
        "next_year_recommended_sections": 3,
    }
    series = body["series"][0]
    assert series["class_level"] == "Nursery"
    assert series["method"] == "linear_trend"
    assert series["projections"] == [
        {
            "academic_year": "2024-2025",
            "predicted_enrollment": 29,
            "recommended_sections": 3,
            "planned_class_size": 10,
        },
        {
            "academic_year": "2025-2026",
            "predicted_enrollment": 32,
            "recommended_sections": 4,
            "planned_class_size": 8,
        },
    ]


def test_dashboard_filters_class_but_keeps_filter_options(
    client: TestClient,
    db_session: Session,
) -> None:
    for year, nursery, kinder in [
        ("2022-2023", 20, 30),
        ("2023-2024", 22, 33),
    ]:
        seed(db_session, year, "Nursery", nursery, 0)
        seed(db_session, year, "Kindergarten", kinder, 0)
    db_session.commit()

    response = client.post(
        "/api/reports/dashboard",
        json={"horizon": 1, "class_levels": ["nursery"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["available_class_levels"] == ["Kindergarten", "Nursery"]
    assert [item["class_level"] for item in body["historical"]] == [
        "Nursery",
        "Nursery",
    ]
    assert [item["class_level"] for item in body["series"]] == ["Nursery"]


def test_dashboard_propagates_skipped_series(
    client: TestClient,
    db_session: Session,
) -> None:
    seed(db_session, "2022-2023", "Nursery", 10, 10)
    seed(db_session, "2023-2024", "Nursery", 11, 11)
    seed(db_session, "2023-2024", "Toddler", 4, 5)
    db_session.commit()

    response = client.post("/api/reports/dashboard", json={})

    assert response.status_code == 200
    assert response.json()["skipped"] == [
        {
            "class_level": "Toddler",
            "reason": "At least 2 historical academic years are required.",
        }
    ]


def test_dashboard_empty_data_and_validation(client: TestClient) -> None:
    empty = client.post("/api/reports/dashboard", json={})
    assert empty.status_code == 422
    assert (
        empty.json()["detail"]["message"]
        == "No historical enrollment data is available."
    )

    assert (
        client.post(
            "/api/reports/dashboard",
            json={"horizon": 0, "max_class_size": 25},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/reports/dashboard",
            json={"horizon": 3, "max_class_size": 101},
        ).status_code
        == 422
    )
