import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import attendance, finance, overview, people, projects
from app.config.settings import get_settings
from app.db.session import engine
from app.services.values import DomainError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=get_settings().log_level)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    application = FastAPI(title="Work Management", version="0.2.0", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Dev-Auth"],
    )

    @application.middleware("http")
    async def private_responses(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @application.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Kiritilgan ma'lumotni tekshiring: summa, sana va majburiy maydonlar."
            },
        )

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error("API operation failed: %s %s", request.method, request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=500, content={"detail": "Amal bajarilmadi. Qayta urinib ko'ring."}
        )

    for router in (
        overview.router,
        people.router,
        attendance.router,
        projects.router,
        finance.router,
    ):
        application.include_router(router, prefix="/api/v1")
    application.add_api_route("/health", health, methods=["GET"])
    return application


async def health() -> dict[str, str]:
    return {"status": "ok"}


app = create_app()
