from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.enrollments import router as enrollments_router
from app.api.forecasts import router as forecasts_router
from app.api.reports import router as reports_router
from app.api.sections import router as sections_router
from app.core.config import settings
from app.db.session import get_db

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_origin_regex=r"^http://(127\.0\.0\.1|localhost):\d+$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["Content-Type", "X-DSS-Token"],
)


@app.middleware("http")
async def require_desktop_token(request: Request, call_next):
    if (
        settings.api_token
        and request.url.path.startswith("/api/")
        and request.method != "OPTIONS"
        and request.headers.get("X-DSS-Token") != settings.api_token
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid desktop API token."},
        )
    return await call_next(request)


app.include_router(enrollments_router)
app.include_router(forecasts_router)
app.include_router(reports_router)
app.include_router(sections_router)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ready"}
