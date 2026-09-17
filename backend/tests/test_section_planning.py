import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enrollment import EnrollmentRecord
from app.services.section_planning import compute_section_recommendation


def seed_record(
    db: Session,
    academic_year: str,
    class_level: str,
    count: int,
) -> None:
    db.add(
        EnrollmentRecord(
            academic_year=academic_year,
            class_level=class_level,
            sex="Female",
            enrollment_count=count,
        )
    )


@pytest.mark.parametrize(
    ("enrollment", "maximum", "expected"),
    [
        (0, 25, (0, 0)),
        (1, 25, (1, 1)),
        (25, 25, (1, 25)),
        (26, 25, (2, 13)),
        (51, 25, (3, 17)),
    ],
)
def test_compute_section_recommendation_boundaries(
    enrollment: int,
    maximum: int,
    expected: tuple[int, int],
) -> None:
    assert compute_section_recommendation(enrollment, maximum) == expected


def test_compute_section_recommendation_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        compute_section_recommendation(-1, 25)
    with pytest.raises(ValueError, match="at least 1"):
        compute_section_recommendation(20, 0)


def test_endpoint_uses_default_limit_and_class_filter(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_record(db_session, "2022-2023", "Nursery", 20)
    seed_record(db_session, "2023-2024", "Nursery", 30)
    seed_record(db_session, "2022-2023", "Kindergarten", 10)
    seed_record(db_session, "2023-2024", "Kindergarten", 12)
    db_session.commit()

    response = client.post(
        "/api/sections/recommendations",
        json={"horizon": 2, "class_levels": ["Nursery"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["horizon"] == 2
    assert body["max_class_size"] == 25
    assert len(body["series"]) == 1
    series = body["series"][0]
    assert series["class_level"] == "Nursery"
    assert series["method"] == "linear_trend"
    assert series["recommendations"] == [
        {
            "academic_year": "2024-2025",
            "predicted_enrollment": 40,
            "max_class_size": 25,
            "recommended_sections": 2,
            "planned_class_size": 20,
        },
        {
            "academic_year": "2025-2026",
            "predicted_enrollment": 50,
            "max_class_size": 25,
            "recommended_sections": 2,
            "planned_class_size": 25,
        },
    ]


def test_endpoint_applies_custom_limit_to_multiple_classes(
    client: TestClient,
    db_session: Session,
) -> None:
    for class_level, counts in {
        "Nursery": (20, 30),
        "Kindergarten": (30, 40),
    }.items():
        seed_record(db_session, "2022-2023", class_level, counts[0])
        seed_record(db_session, "2023-2024", class_level, counts[1])
    db_session.commit()

    response = client.post(
        "/api/sections/recommendations",
        json={"horizon": 1, "max_class_size": 20},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["max_class_size"] == 20
    assert {series["class_level"] for series in body["series"]} == {
        "Nursery",
        "Kindergarten",
    }
    nursery = next(
        series for series in body["series"] if series["class_level"] == "Nursery"
    )
    assert nursery["recommendations"][0]["predicted_enrollment"] == 40
    assert nursery["recommendations"][0]["recommended_sections"] == 2


def test_endpoint_propagates_skipped_forecast_series(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_record(db_session, "2022-2023", "Nursery", 20)
    seed_record(db_session, "2023-2024", "Nursery", 25)
    seed_record(db_session, "2023-2024", "Toddler", 8)
    db_session.commit()

    response = client.post(
        "/api/sections/recommendations",
        json={"horizon": 1, "max_class_size": 15},
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["class_level"] for item in body["skipped"]] == ["Toddler"]
    assert "At least 2" in body["skipped"][0]["reason"]
    assert body["series"][0]["recommendations"][0]["max_class_size"] == 15


@pytest.mark.parametrize(
    "payload",
    [
        {"max_class_size": 0},
        {"max_class_size": 101},
        {"max_class_size": 10.5},
        {"horizon": 0},
        {"horizon": 6},
        {"class_levels": ["Nursery", "nursery"]},
    ],
)
def test_endpoint_rejects_invalid_requests(
    client: TestClient,
    payload: dict,
) -> None:
    assert client.post("/api/sections/recommendations", json=payload).status_code == 422


def test_endpoint_reports_unavailable_forecast_data(client: TestClient) -> None:
    response = client.post("/api/sections/recommendations", json={})

    assert response.status_code == 422
    assert (
        response.json()["detail"]["message"]
        == "No historical enrollment data is available."
    )
