"""AI suggestion endpoint.

This module exposes an HTTP API to generate code suggestions based on
user input. The current implementation delegates to a simple
heuristic service defined in ``src.backend.services.ai``. In a real
deployment this service could interface with a large language model
or other AI provider.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.ai import suggest_code


class SuggestionRequest(BaseModel):
    """Request payload for a code suggestion."""

    code: str


class SuggestionResponse(BaseModel):
    """Response payload containing the suggestion."""

    suggestion: str


router = APIRouter()


@router.post(
    "/suggest",
    summary="Generate a code suggestion",
    response_model=SuggestionResponse,
)
async def generate_suggestion(payload: SuggestionRequest) -> SuggestionResponse:
    """Generate a code suggestion based on the provided snippet.

    This endpoint is a thin wrapper around the ``suggest_code`` function.

    :param payload: The request body containing the source code snippet.
    :returns: A suggestion string wrapped in a ``SuggestionResponse``.
    """
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail="Code snippet cannot be empty")
    suggestion = suggest_code(payload.code)
    return SuggestionResponse(suggestion=suggestion)
