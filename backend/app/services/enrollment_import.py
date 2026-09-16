from dataclasses import dataclass
from io import BytesIO
import re

import pandas as pd
from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from app.models.enrollment import EnrollmentRecord
from app.schemas.enrollment import ImportRowError, ImportSummary

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
REQUIRED_COLUMNS = {
    "academic_year",
    "class_level",
    "sex",
    "enrollment_count",
}
ACADEMIC_YEAR_PATTERN = re.compile(r"^(\d{4})-(\d{4})$")


class EnrollmentImportError(ValueError):
    def __init__(self, message: str, errors: list[ImportRowError]) -> None:
        super().__init__(message)
        self.message = message
        self.errors = errors


@dataclass(frozen=True)
class ValidatedEnrollmentRow:
    academic_year: str
    class_level: str
    sex: str
    enrollment_count: int

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.academic_year, self.class_level, self.sex)


def _normalized_header(value: object) -> str:
    return str(value).lstrip("\ufeff").strip().lower().replace(" ", "_")


def parse_enrollment_csv(file_bytes: bytes) -> list[ValidatedEnrollmentRow]:
    if not file_bytes:
        raise EnrollmentImportError(
            "The uploaded CSV is empty.",
            [ImportRowError(message="Upload a CSV containing at least one data row.")],
        )
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise EnrollmentImportError(
            "The uploaded CSV is too large.",
            [ImportRowError(message="The maximum file size is 5 MB.")],
        )

    try:
        frame = pd.read_csv(
            BytesIO(file_bytes),
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
    except UnicodeDecodeError as exc:
        raise EnrollmentImportError(
            "The CSV must use UTF-8 encoding.",
            [ImportRowError(message="Save the file as UTF-8 and try again.")],
        ) from exc
    except pd.errors.EmptyDataError as exc:
        raise EnrollmentImportError(
            "The uploaded CSV is empty.",
            [ImportRowError(message="The file does not contain a header row.")],
        ) from exc
    except pd.errors.ParserError as exc:
        raise EnrollmentImportError(
            "The CSV could not be parsed.",
            [ImportRowError(message=str(exc))],
        ) from exc

    frame.columns = [_normalized_header(column) for column in frame.columns]
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise EnrollmentImportError(
            "The CSV is missing required columns.",
            [
                ImportRowError(field=column, message=f"Missing column: {column}")
                for column in missing
            ],
        )
    if frame.empty:
        raise EnrollmentImportError(
            "The CSV has no data rows.",
            [ImportRowError(message="Add at least one enrollment row.")],
        )

    errors: list[ImportRowError] = []
    validated: list[ValidatedEnrollmentRow] = []
    seen: dict[tuple[str, str, str], int] = {}

    for index, source in frame.iterrows():
        csv_row = int(index) + 2
        academic_year = str(source["academic_year"]).strip()
        class_level = str(source["class_level"]).strip()
        raw_sex = str(source["sex"]).strip()
        raw_count = str(source["enrollment_count"]).strip()

        year_match = ACADEMIC_YEAR_PATTERN.fullmatch(academic_year)
        if not year_match or int(year_match.group(2)) != int(year_match.group(1)) + 1:
            errors.append(
                ImportRowError(
                    row=csv_row,
                    field="academic_year",
                    message="Use consecutive years in YYYY-YYYY format.",
                )
            )
        if not class_level:
            errors.append(
                ImportRowError(
                    row=csv_row,
                    field="class_level",
                    message="Class level is required.",
                )
            )
        elif len(class_level) > 100:
            errors.append(
                ImportRowError(
                    row=csv_row,
                    field="class_level",
                    message="Class level must be 100 characters or fewer.",
                )
            )

        sex = {"male": "Male", "female": "Female"}.get(raw_sex.casefold())
        if sex is None:
            errors.append(
                ImportRowError(
                    row=csv_row,
                    field="sex",
                    message="Sex must be Male or Female.",
                )
            )

        count: int | None = None
        if not re.fullmatch(r"\d+", raw_count):
            errors.append(
                ImportRowError(
                    row=csv_row,
                    field="enrollment_count",
                    message="Enrollment count must be a non-negative integer.",
                )
            )
        else:
            count = int(raw_count)

        if year_match and class_level and sex is not None and count is not None:
            row = ValidatedEnrollmentRow(
                academic_year=academic_year,
                class_level=class_level,
                sex=sex,
                enrollment_count=count,
            )
            if row.key in seen:
                errors.append(
                    ImportRowError(
                        row=csv_row,
                        message=f"Duplicates CSV row {seen[row.key]}.",
                    )
                )
            else:
                seen[row.key] = csv_row
                validated.append(row)

    if errors:
        raise EnrollmentImportError(
            "The CSV contains invalid rows. No records were imported.",
            errors,
        )
    return validated


def upsert_enrollment_rows(
    db: Session,
    rows: list[ValidatedEnrollmentRow],
) -> ImportSummary:
    keys = [row.key for row in rows]
    existing_records = db.scalars(
        select(EnrollmentRecord).where(
            tuple_(
                EnrollmentRecord.academic_year,
                EnrollmentRecord.class_level,
                EnrollmentRecord.sex,
            ).in_(keys)
        )
    ).all()
    existing = {
        (record.academic_year, record.class_level, record.sex): record
        for record in existing_records
    }

    inserted = 0
    updated = 0
    new_records: list[EnrollmentRecord] = []
    for row in rows:
        record = existing.get(row.key)
        if record is None:
            new_records.append(
                EnrollmentRecord(
                    academic_year=row.academic_year,
                    class_level=row.class_level,
                    sex=row.sex,
                    enrollment_count=row.enrollment_count,
                )
            )
            inserted += 1
        else:
            record.enrollment_count = row.enrollment_count
            updated += 1

    db.add_all(new_records)
    db.commit()
    return ImportSummary(inserted=inserted, updated=updated, total=len(rows))
