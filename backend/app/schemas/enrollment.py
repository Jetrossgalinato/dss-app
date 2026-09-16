from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnrollmentRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    academic_year: str
    class_level: str
    sex: str
    enrollment_count: int
    created_at: datetime
    updated_at: datetime


class EnrollmentListResponse(BaseModel):
    items: list[EnrollmentRecordResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ImportRowError(BaseModel):
    row: int | None = None
    field: str | None = None
    message: str


class ImportSummary(BaseModel):
    inserted: int = Field(ge=0)
    updated: int = Field(ge=0)
    total: int = Field(ge=0)


class ImportErrorResponse(BaseModel):
    message: str
    errors: list[ImportRowError]


class DeleteResponse(BaseModel):
    deleted: bool
    id: int
