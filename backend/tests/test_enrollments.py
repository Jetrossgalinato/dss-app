from fastapi.testclient import TestClient


def upload(client: TestClient, csv: str, filename: str = "enrollment.csv"):
    return client.post(
        "/api/enrollments/import",
        files={"file": (filename, csv.encode("utf-8"), "text/csv")},
    )


def test_import_list_and_upsert(client: TestClient) -> None:
    initial = upload(
        client,
        "academic_year,program,year_level,sex,location,enrollment_count\n"
        "2024-2025,BSIT,1st Year,Female,Cebu City,42\n"
        "2024-2025,BSIT,1st Year,Male,Cebu City,38\n",
    )
    assert initial.status_code == 200
    assert initial.json() == {"inserted": 2, "updated": 0, "total": 2}

    updated = upload(
        client,
        "academic_year,program,year_level,sex,location,enrollment_count\n"
        "2024-2025,BSIT,1st Year,Female,Cebu City,45\n",
    )
    assert updated.status_code == 200
    assert updated.json() == {"inserted": 0, "updated": 1, "total": 1}

    response = client.get("/api/enrollments")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    female = next(item for item in body["items"] if item["sex"] == "Female")
    assert female["enrollment_count"] == 45
    assert female["program"] == "BSIT"
    assert female["year_level"] == "1st Year"
    assert female["location"] == "Cebu City"


def test_missing_columns_returns_structured_errors(client: TestClient) -> None:
    response = upload(
        client,
        "academic_year,program,year_level,location,enrollment_count\n"
        "2024-2025,BSIT,1st Year,Cebu City,18\n",
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["message"] == "The CSV is missing required columns."
    assert detail["errors"][0]["field"] == "sex"


def test_invalid_rows_are_reported_and_import_is_atomic(client: TestClient) -> None:
    response = upload(
        client,
        "academic_year,program,year_level,sex,location,enrollment_count\n"
        "2024-2025,BSIT,1st Year,Female,Cebu City,18\n"
        "2024-2027,BSN,Nursery,Unknown,,-1\n",
    )
    assert response.status_code == 422
    errors = response.json()["detail"]["errors"]
    assert {error["field"] for error in errors} >= {
        "academic_year",
        "year_level",
        "sex",
        "location",
        "enrollment_count",
    }
    assert all(error["row"] == 3 for error in errors)
    assert client.get("/api/enrollments").json()["total"] == 0


def test_freeform_program_is_uppercased_and_filter_options_update(
    client: TestClient,
) -> None:
    imported = upload(
        client,
        "academic_year,program,year_level,sex,location,enrollment_count\n"
        "2023-2024,bsn,1st Year,Female,Cebu City,10\n"
        "2024-2025,BSN,1st Year,Female,Cebu City,12\n"
        "2024-2025,BSIT,2nd Year,Male,Mandaue City,20\n",
    )
    assert imported.status_code == 200

    records = client.get("/api/enrollments", params={"program": "BSN"})
    assert records.status_code == 200
    assert records.json()["total"] == 2
    assert all(item["program"] == "BSN" for item in records.json()["items"])

    options = client.get("/api/enrollments/filter-options")
    assert options.status_code == 200
    body = options.json()
    assert body["programs"] == ["BSIT", "BSN"]
    assert body["year_levels"] == ["1st Year", "2nd Year"]
    assert body["locations"] == ["Cebu City", "Mandaue City"]

    blank_program = upload(
        client,
        "academic_year,program,year_level,sex,location,enrollment_count\n"
        "2024-2025,,1st Year,Female,Cebu City,10\n",
    )
    assert blank_program.status_code == 422
    assert blank_program.json()["detail"]["errors"][0]["field"] == "program"


def test_duplicate_rows_are_rejected(client: TestClient) -> None:
    response = upload(
        client,
        "academic_year,program,year_level,sex,location,enrollment_count\n"
        "2024-2025,BSIT,1st Year,Female,Cebu City,18\n"
        "2024-2025,bsit,1st year,female,cebu city,20\n",
    )
    assert response.status_code == 422
    error = response.json()["detail"]["errors"][0]
    assert error["row"] == 3
    assert "Duplicates CSV row 2" in error["message"]


def test_location_normalization_and_filters(client: TestClient) -> None:
    imported = upload(
        client,
        "academic_year,program,year_level,sex,location,enrollment_count\n"
        "2023-2024,BSBA,2nd Year,Female,mandaue city,12\n"
        "2024-2025,BSIT,1st Year,Male,Cebu City,16\n"
        "2024-2025,BSCS,3rd Year,Female,Cebu City,22\n",
    )
    assert imported.status_code == 200

    filtered = client.get(
        "/api/enrollments",
        params={
            "academic_year": "2024-2025",
            "program": "BSCS",
            "sex": "Female",
            "page_size": 1,
        },
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    item = filtered.json()["items"][0]
    assert item["program"] == "BSCS"
    assert item["year_level"] == "3rd Year"
    assert item["location"] == "Cebu City"

    by_location = client.get("/api/enrollments", params={"location": "Mandaue"})
    assert by_location.status_code == 200
    assert by_location.json()["total"] == 1
    assert by_location.json()["items"][0]["location"] == "Mandaue City"

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
        "academic_year,program,year_level,sex,location,enrollment_count"
    )

    wrong_type = upload(client, "not,csv\n", filename="enrollment.txt")
    assert wrong_type.status_code == 415


def test_clear_all_enrollment_records(client: TestClient) -> None:
    imported = upload(
        client,
        "academic_year,program,year_level,sex,location,enrollment_count\n"
        "2023-2024,BSIT,1st Year,Female,Cebu City,12\n"
        "2024-2025,BSIT,1st Year,Male,Cebu City,16\n",
    )
    assert imported.status_code == 200

    cleared = client.delete("/api/enrollments")
    assert cleared.status_code == 200
    assert cleared.json() == {"deleted": True, "deleted_count": 2}
    assert client.get("/api/enrollments").json()["total"] == 0

    cleared_again = client.delete("/api/enrollments")
    assert cleared_again.status_code == 200
    assert cleared_again.json() == {"deleted": True, "deleted_count": 0}


def test_manual_upsert_insert_and_update(client: TestClient) -> None:
    created = client.post(
        "/api/enrollments",
        json={
            "academic_year": "2024-2025",
            "program": "bsit",
            "year_level": "1st Year",
            "sex": "Female",
            "location": "Cebu City",
            "enrollment_count": 40,
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["created"] is True
    assert body["record"]["program"] == "BSIT"
    assert body["record"]["enrollment_count"] == 40

    updated = client.post(
        "/api/enrollments",
        json={
            "academic_year": "2024-2025",
            "program": "BSIT",
            "year_level": "1st Year",
            "sex": "Female",
            "location": "Cebu City",
            "enrollment_count": 44,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["created"] is False
    assert updated.json()["record"]["enrollment_count"] == 44
    assert client.get("/api/enrollments").json()["total"] == 1


def test_manual_upsert_rejects_invalid_fields(client: TestClient) -> None:
    response = client.post(
        "/api/enrollments",
        json={
            "academic_year": "2024-2026",
            "program": "BSIT",
            "year_level": "Nursery",
            "sex": "Unknown",
            "location": "Cebu City",
            "enrollment_count": 10,
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["message"] == "The enrollment record is invalid."
    assert {error["field"] for error in detail["errors"]} >= {
        "academic_year",
        "year_level",
        "sex",
    }
