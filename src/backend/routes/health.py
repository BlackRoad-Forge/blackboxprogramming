"""Health check endpoint.

This route provides a simple way for clients and monitoring systems to
confirm that the backend service is running and responsive. It
returns a JSON object with a ``status`` field set to ``"ok"``.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Health check", response_model=dict)
async def health_check() -> dict:
    """Return the health status of the service.

    Always responds with ``{"status": "ok"}`` when the service is up.
    """
    return {"status": "ok"}
