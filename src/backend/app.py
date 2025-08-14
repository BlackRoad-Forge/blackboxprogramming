from fastapi import FastAPI

from .routes import health, suggestions
from .settings import settings

app = FastAPI(title=settings.app_name)

# Include API routers with prefixes
app.include_router(health.router, prefix="/api")
app.include_router(suggestions.router, prefix="/api")


def main() -> None:
    """Launch the FastAPI application using uvicorn."""
    import uvicorn
    uvicorn.run("src.backend.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
