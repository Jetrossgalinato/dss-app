from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.enrollments import router as enrollments_router
from app.api.forecasts import router as forecasts_router
from app.api.sections import router as sections_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(enrollments_router)
app.include_router(forecasts_router)
app.include_router(sections_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
