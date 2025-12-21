"""TTS synthesis handler."""

from fastapi import APIRouter, Response
from fastapi.responses import Response as FastAPIResponse

from app.models.request import SynthesisRequest
from app.services.queue import get_request_queue
from app.services.synthesis import get_synthesis_service

router = APIRouter()


@router.post("/tts", response_class=Response)
async def synthesize(request: SynthesisRequest) -> FastAPIResponse:
    """Synthesize text to speech.

    Args:
        request: Synthesis request with text and options.

    Returns:
        Audio response with WAV data.
    """
    queue = get_request_queue()
    service = get_synthesis_service()

    # Submit to queue and wait for result
    result = await queue.submit(service.synthesize, request)

    # Determine content type
    content_type = "audio/wav"
    if request.output_format.value == "mp3":
        content_type = "audio/mpeg"

    # Build response with metadata headers
    return Response(
        content=result.audio_data,
        media_type=content_type,
        headers={
            "X-Model-Id": result.metadata.model_id,
            "X-Language": result.metadata.language,
            "X-Duration-Ms": str(result.metadata.duration_ms),
            "X-Sample-Rate": str(result.metadata.sample_rate),
        },
    )
