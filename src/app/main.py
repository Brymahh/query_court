from fastapi import FastAPI
from pydantic import BaseModel

from app.api import create_review_router
from app.dependencies import build_event_source
from app.settings import Settings
from app.streaming import ReviewEventSource


class HealthResponse(BaseModel):
    """Response returned by the health endpoint.

    Attributes
    ----------
    status:
        Current application health status.
    """

    status: str


settings = Settings()


def create_app(
    event_source: ReviewEventSource | None = None,
) -> FastAPI:
    """Create the FastAPI application.

    Parameters
    ----------
    event_source:
        Optional workflow event source.

    Returns
    -------
    FastAPI
        Configured application instance.
    """
    app = FastAPI(title=settings.app_name)
    app.include_router(create_review_router(event_source))

    @app.get("/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        """Return the service health status.

        Returns
        -------
        HealthResponse
            A response indicating that the application is running.
        """
        return HealthResponse(status="ok")

    return app


app = create_app(event_source=build_event_source(settings))
