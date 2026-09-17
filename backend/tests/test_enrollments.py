from fastapi.testclient import TestClient


def upload(client: TestClient, csv: str, filename: str = "enrollment.csv"):
    return client.post(
        "/api/enrollments/import",
        files={"file": (filename, csv.encode("utf-8"), "text/csv")},
    )


def test_import_list_and_upsert(client: TestClient) -> None:
    initial = upload(
        client,
        "academic_year,class_level,sex,enrollment_count\n"
        "2024-2025,Nursery,Female,18\n"
        "2024-2025,Nursery,Male,16\n",
    )
    assert initial.status_code == 200
    assert initial.json() == {"inserted": 2, "updated": 0, "total": 2}

    updated = upload(
        client,
        "academic_year,class_level,sex,enrollment_count\n"
        "2024-2025,Nursery,Female,20\n",
    )
    assert updated.status_code == 200
    assert updated.json() == {"inserted": 0, "updated": 1, "total": 1}

    response = client.get("/api/enrollments")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    female = next(item for item in body["items"] if item["sex"] == "Female")
    assert female["enrollment_count"] == 20


def test_missing_columns_returns_structured_errors(client: TestClient) -> None:
    response = upload(
        client,
        "academic_year,class_level,enrollment_count\n"
        "2024-2025,Nursery,18\n",
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["message"] == "The CSV is missing required columns."
    assert detail["errors"][0]["field"] == "sex"


def test_invalid_rows_are_reported_and_import_is_atomic(client: TestClient) -> None:
    response = upload(
        client,
        "academic_year,class_level,sex,enrollment_count\n"
        "2024-2025,Nursery,Female,18\n"
        "2024-2027,Kindergarten,Unknown,-1\n",
    )
    assert response.status_code == 422
    errors = response.json()["detail"]["errors"]
    assert {error["field"] for error in errors} == {
        "academic_year",
        "sex",
        "enrollment_count",
    }
    assert all(error["row"] == 3 for error in errors)
    assert client.get("/api/enrollments").json()["total"] == 0


def test_duplicate_rows_are_rejected(client: TestClient) -> None:
    response = upload(
        client,
        "academic_year,class_level,sex,enrollment_count\n"
        "2024-2025,Nursery,Female,18\n"
        "2024-2025,Nursery,female,20\n",
    )
    assert response.status_code == 422
    error = response.json()["detail"]["errors"][0]
    assert error["row"] == 3
    assert "Duplicates CSV row 2" in error["message"]


def test_filters_pagination_delete_and_not_found(client: TestClient) -> None:
    imported = upload(
        client,
        "academic_year,class_level,sex,enrollment_count\n"
        "2023-2024,Nursery,Female,12\n"
        "2024-2025,Nursery,Male,16\n"
        "2024-2025,Kindergarten,Female,22\n",
    )
    assert imported.status_code == 200

    filtered = client.get(
        "/api/enrollments",
        params={"academic_year": "2024-2025", "sex": "Female", "page_size": 1},
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["class_level"] == "Kindergarten"

    paged = client.get("/api/enrollments", params={"page_size": 2})
    assert paged.json()["pages"] == 2
    record_id = paged.json()["items"][0]["id"]

    deleted = client.delete(f"/api/enrollments/{record_id}")
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True, "id": record_id}
    assert client.delete(f"/api/enrollments/{record_id}").status_code == 404


def test_template_and_file_type_validation(client: TestClient) -> None:
    template = client.get("/api/enrollments/template")
    assert template.status_code == 200
    assert template.headers["content-type"].startswith("text/csv")
    assert template.text.startswith(
        "academic_year,class_level,sex,enrollment_count"
    )

    wrong_type = upload(client, "not,csv\n", filename="enrollment.txt")
    assert wrong_type.status_code == 415


def test_clear_all_enrollment_records(client: TestClient) -> None:
    imported = upload(
        client,
        "academic_year,class_level,sex,enrollment_count\n"
        "2023-2024,Nursery,Female,12\n"
        "2024-2025,Nursery,Male,16\n",
    )
    assert imported.status_code == 200

    cleared = client.delete("/api/enrollments")
    assert cleared.status_code == 200
    assert cleared.json() == {"deleted": True, "deleted_count": 2}
    assert client.get("/api/enrollments").json()["total"] == 0

    cleared_again = client.delete("/api/enrollments")
    assert cleared_again.status_code == 200
    assert cleared_again.json() == {"deleted": True, "deleted_count": 0}
