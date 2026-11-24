from io import BytesIO
import math

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.enrollment_dims import ALLOWED_YEAR_LEVELS
from app.models.enrollment import EnrollmentRecord
from app.schemas.enrollment import (
    BulkDeleteResponse,
    DeleteResponse,
    EnrollmentFilterOptions,
    EnrollmentListResponse,
    EnrollmentRecordResponse,
    EnrollmentUpsertRequest,
    EnrollmentUpsertResponse,
    ImportSummary,
)
from app.services.enrollment_import import (
    MAX_UPLOAD_BYTES,
    EnrollmentImportError,
    parse_enrollment_csv,
    upsert_enrollment_rows,
    validate_enrollment_fields,
)
from app.services.response_cache import (
    cache_key,
    enrollment_list_cache,
    filter_options_cache,
    get_or_set,
    invalidate_all,
)

router = APIRouter(prefix="/api/enrollments", tags=["enrollments"])
CSV_TEMPLATE = (
    "academic_year,program,year_level,sex,location,enrollment_count\n"
    "2024-2025,BSIT,1st Year,Female,Cebu City,42\n"
    "2024-2025,BSIT,1st Year,Male,Cebu City,38\n"
)


@router.post("", response_model=EnrollmentUpsertResponse)
def upsert_enrollment(
    payload: EnrollmentUpsertRequest,
    db: Session = Depends(get_db),
) -> EnrollmentUpsertResponse:
    try:
        row = validate_enrollment_fields(
            academic_year=payload.academic_year,
            program=payload.program,
            year_level=payload.year_level,
            sex=payload.sex,
            location=payload.location,
            enrollment_count=payload.enrollment_count,
        )
        summary = upsert_enrollment_rows(db, [row])
        record = db.scalars(
            select(EnrollmentRecord).where(
                EnrollmentRecord.academic_year == row.academic_year,
                EnrollmentRecord.program == row.program,
                EnrollmentRecord.year_level == row.year_level,
                EnrollmentRecord.sex == row.sex,
                EnrollmentRecord.location == row.location,
            )
        ).first()
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": "The enrollment record could not be loaded after save.",
                    "errors": [],
                },
            )
        invalidate_all()
        return EnrollmentUpsertResponse(
            created=summary.inserted == 1,
            record=EnrollmentRecordResponse.model_validate(record),
        )
    except EnrollmentImportError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": exc.message,
                "errors": [error.model_dump() for error in exc.errors],
            },
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "The enrollment record could not be saved.",
                "errors": [],
            },
        ) from exc


@router.post("/import", response_model=ImportSummary)
async def import_enrollments(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImportSummary:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={"message": "Only .csv files are accepted.", "errors": []},
        )

    try:
        rows = parse_enrollment_csv(await file.read(MAX_UPLOAD_BYTES + 1))
        summary = upsert_enrollment_rows(db, rows)
        invalidate_all()
        return summary
    except EnrollmentImportError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": exc.message,
                "errors": [error.model_dump() for error in exc.errors],
            },
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "The enrollment records could not be saved.",
                "errors": [],
            },
        ) from exc
    finally:
        await file.close()


@router.get("", response_model=EnrollmentListResponse)
def list_enrollments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    academic_year: str | None = Query(default=None, max_length=9),
    program: str | None = Query(default=None, max_length=50),
    year_level: str | None = Query(default=None, max_length=20),
    location: str | None = Query(default=None, max_length=150),
    sex: str | None = Query(default=None, pattern="^(Male|Female)$"),
    db: Session = Depends(get_db),
) -> EnrollmentListResponse:
    key = cache_key(
        "enrollment-list",
        page,
        page_size,
        academic_year or "",
        (program or "").strip().upper(),
        (year_level or "").strip(),
        (location or "").strip(),
        sex or "",
    )

    def compute() -> EnrollmentListResponse:
        filters = []
        if academic_year:
            filters.append(EnrollmentRecord.academic_year == academic_year)
        if program:
            filters.append(EnrollmentRecord.program == program.strip().upper())
        if year_level:
            filters.append(EnrollmentRecord.year_level.ilike(year_level.strip()))
        if location:
            filters.append(EnrollmentRecord.location.ilike(f"%{location.strip()}%"))
        if sex:
            filters.append(EnrollmentRecord.sex == sex)

        total = db.scalar(
            select(func.count()).select_from(EnrollmentRecord).where(*filters)
        ) or 0
        records = db.scalars(
            select(EnrollmentRecord)
            .where(*filters)
            .order_by(
                EnrollmentRecord.academic_year.desc(),
                EnrollmentRecord.program,
                EnrollmentRecord.year_level,
                EnrollmentRecord.location,
                EnrollmentRecord.sex,
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return EnrollmentListResponse(
            items=[
                EnrollmentRecordResponse.model_validate(record) for record in records
            ],
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total else 0,
        )

    return get_or_set(enrollment_list_cache, key, compute)


@router.get("/filter-options", response_model=EnrollmentFilterOptions)
def enrollment_filter_options(
    db: Session = Depends(get_db),
) -> EnrollmentFilterOptions:
    key = cache_key("filter-options")

    def compute() -> EnrollmentFilterOptions:
        programs = sorted(
            {
                value
                for value in db.scalars(
                    select(EnrollmentRecord.program).distinct()
                ).all()
                if value
            },
            key=str.casefold,
        )
        present_year_levels = {
            value
            for value in db.scalars(
                select(EnrollmentRecord.year_level).distinct()
            ).all()
            if value
        }
        year_levels = [
            level for level in ALLOWED_YEAR_LEVELS if level in present_year_levels
        ]
        locations = sorted(
            {
                value
                for value in db.scalars(
                    select(EnrollmentRecord.location).distinct()
                ).all()
                if value
            },
            key=str.casefold,
        )
        return EnrollmentFilterOptions(
            programs=programs,
            year_levels=year_levels,
            locations=locations,
        )

    return get_or_set(filter_options_cache, key, compute)


@router.delete("", response_model=BulkDeleteResponse)
def clear_enrollments(
    db: Session = Depends(get_db),
) -> BulkDeleteResponse:
    try:
        result = db.execute(delete(EnrollmentRecord))
        deleted_count = result.rowcount or 0
        db.commit()
        invalidate_all()
        return BulkDeleteResponse(deleted=True, deleted_count=deleted_count)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Historical enrollment records could not be cleared.",
        ) from exc


@router.get("/template")
def download_template() -> StreamingResponse:
    return StreamingResponse(
        BytesIO(CSV_TEMPLATE.encode("utf-8")),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="enrollment-template.csv"'
        },
    )


@router.delete("/{record_id}", response_model=DeleteResponse)
def delete_enrollment(
    record_id: int,
    db: Session = Depends(get_db),
) -> DeleteResponse:
    record = db.get(EnrollmentRecord, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment record not found.",
        )
    db.delete(record)
    db.commit()
    invalidate_all()
    return DeleteResponse(deleted=True, id=record_id)
