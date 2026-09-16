from io import BytesIO
import math

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enrollment import EnrollmentRecord
from app.schemas.enrollment import (
    DeleteResponse,
    EnrollmentListResponse,
    ImportSummary,
)
from app.services.enrollment_import import (
    MAX_UPLOAD_BYTES,
    EnrollmentImportError,
    parse_enrollment_csv,
    upsert_enrollment_rows,
)

router = APIRouter(prefix="/api/enrollments", tags=["enrollments"])
CSV_TEMPLATE = (
    "academic_year,class_level,sex,enrollment_count\n"
    "2024-2025,Nursery,Female,18\n"
    "2024-2025,Nursery,Male,16\n"
)


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
        return upsert_enrollment_rows(db, rows)
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
    class_level: str | None = Query(default=None, max_length=100),
    sex: str | None = Query(default=None, pattern="^(Male|Female)$"),
    db: Session = Depends(get_db),
) -> EnrollmentListResponse:
    filters = []
    if academic_year:
        filters.append(EnrollmentRecord.academic_year == academic_year)
    if class_level:
        filters.append(EnrollmentRecord.class_level.ilike(f"%{class_level.strip()}%"))
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
            EnrollmentRecord.class_level,
            EnrollmentRecord.sex,
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return EnrollmentListResponse(
        items=records,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


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
    return DeleteResponse(deleted=True, id=record_id)
