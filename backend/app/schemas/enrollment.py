from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnrollmentRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    academic_year: str
    program: str
    year_level: str
    sex: str
    location: str
    enrollment_count: int
    created_at: datetime
    updated_at: datetime


class EnrollmentUpsertRequest(BaseModel):
    academic_year: str = Field(min_length=1, max_length=20)
    program: str = Field(min_length=1, max_length=50)
    year_level: str = Field(min_length=1, max_length=20)
    sex: str = Field(min_length=1, max_length=20)
    location: str = Field(min_length=1, max_length=150)
    enrollment_count: int = Field(ge=0)


class EnrollmentUpsertResponse(BaseModel):
    created: bool
    record: EnrollmentRecordResponse


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


class BulkDeleteResponse(BaseModel):
    deleted: bool
    deleted_count: int = Field(ge=0)


class EnrollmentFilterOptions(BaseModel):
    programs: list[str]
    year_levels: list[str]
    locations: list[str]
