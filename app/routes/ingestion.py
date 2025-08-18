"""Ingestion routes for bid package uploads."""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models import IngestionRequest, IngestionResponse
from app.services.ingestion import ingestion_service

router = APIRouter()


@router.post("/api/ingest", response_model=IngestionResponse)
async def ingest_bid_package(
    file: Annotated[UploadFile, File(description="Bid package file (PDF, CSV, TXT, JSONL)")],
    airline: Annotated[str, Form(description="Airline code (e.g., UAL)")],
    month: Annotated[str, Form(description="Bid month (e.g., 2025-09)")],
    base: Annotated[str, Form(description="Pilot base (e.g., SFO)")],
    fleet: Annotated[str, Form(description="Aircraft fleet (e.g., 737)")],
    seat: Annotated[str, Form(description="Pilot seat (FO or CA)")],
    pilot_id: Annotated[str, Form(description="Pilot identifier")]
) -> IngestionResponse:
    """
    Ingest a bid package file and return parsed summary.

    Supports PDF, CSV, TXT, and JSONL formats.
    Returns summary with trip count, legs, date span, and credit total.
    """
    try:
        # Read file content
        file_content = await file.read()

        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Create ingestion request
        request = IngestionRequest(
            airline=airline,
            month=month,
            base=base,
            fleet=fleet,
            seat=seat,
            pilot_id=pilot_id
        )

        # Process the file
        response = ingestion_service.ingest(file_content, file.filename, request)

        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e
