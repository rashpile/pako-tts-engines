"""OpenAPI specification handler."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/openapi.json")
async def get_openapi_spec(request: Request) -> JSONResponse:
    """Get the OpenAPI specification.

    Args:
        request: The incoming request.

    Returns:
        OpenAPI specification as JSON.
    """
    # Get the OpenAPI schema from the app
    openapi_schema = request.app.openapi()
    return JSONResponse(content=openapi_schema)
