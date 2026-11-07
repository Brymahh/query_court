from fastapi import FastAPI
from pydantic import BaseModel

from app.settings import Settings


class HealthResponse(BaseModel):
    """Response returned by the health endpoint.

    Attributes
    ----------
    status:
        Current application health status.
    """

    status: str


settings = Settings()
app = FastAPI(title=settings.app_name)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return the service health status.

    Returns
    -------
    HealthResponse
        A response indicating that the application is running.
    """

    return HealthResponse(status="ok")
