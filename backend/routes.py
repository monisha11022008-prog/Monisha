import os

from fastapi import APIRouter, HTTPException

from backend.ai_core.gemini_generator import (
    GeminiDocumentGenerator,
)

from backend.schemas import (
    DocumentRequest,
    GenerateResponse,
)


router = APIRouter()


@router.get("/")
def root():
    return {
        "message": "LegalEase API is running",
        "service": "LegalEase AI",
    }


@router.get("/health")
def health():
    demo_mode = os.getenv(
        "DEMO_MODE",
        "true",
    ).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    return {
        "status": "ok",
        "gemini_configured": bool(
            os.getenv(
                "GEMINI_API_KEY",
                "",
            ).strip()
        ),
        "demo_mode": demo_mode,
    }


@router.post(
    "/generate",
    response_model=GenerateResponse,
)
def generate_document(
    request: DocumentRequest,
):
    try:
        generator = GeminiDocumentGenerator()

        document, demo_mode = (
            generator.generate_document(
                document_type=request.document_type,
                parties=request.parties,
                terms=request.terms,
                effective_date=request.effective_date,
            )
        )

        return GenerateResponse(
            document=document,
            demo_mode=demo_mode,
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Document generation failed: "
                f"{exc}"
            ),
        ) from exc