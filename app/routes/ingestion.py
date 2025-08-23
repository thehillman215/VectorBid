"""Ingestion routes for bid package uploads."""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

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
    pilot_id: Annotated[str, Form(description="Pilot identifier")],
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
            pilot_id=pilot_id,
        )

        # Process the file
        response = await ingestion_service.ingest_async(file_content, file.filename, request)

        if not response.success:
            raise HTTPException(status_code=400, detail=response.error)

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.post("/api/ingest/html")
async def ingest_bid_package_html(
    file: Annotated[UploadFile, File(description="Bid package file (PDF, CSV, TXT, JSONL)")],
    airline: Annotated[str, Form(description="Airline code (e.g., UAL)")],
    month: Annotated[str, Form(description="Bid month (e.g., 2025-09)")],
    base: Annotated[str, Form(description="Pilot base (e.g., SFO)")],
    fleet: Annotated[str, Form(description="Aircraft fleet (e.g., 737)")],
    seat: Annotated[str, Form(description="Pilot seat (FO or CA)")],
    pilot_id: Annotated[str, Form(description="Pilot identifier")],
) -> HTMLResponse:
    """
    HTMX version of ingest endpoint that returns HTML for display.
    """
    try:
        # Read file content
        file_content = await file.read()

        if not file_content:
            return HTMLResponse("""
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                <strong>Upload Failed:</strong> Empty file uploaded
            </div>
            """)

        # Create ingestion request
        request = IngestionRequest(
            airline=airline,
            month=month,
            base=base,
            fleet=fleet,
            seat=seat,
            pilot_id=pilot_id,
        )

        # Process the file
        response = await ingestion_service.ingest_async(file_content, file.filename, request)

        if not response.success:
            return HTMLResponse(f"""
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                <strong>Upload Failed:</strong> {response.error}
            </div>
            """)

        # Success response with HTML
        html_content = f"""
        <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            <h3 class="font-semibold mb-2">Upload Successful!</h3>
            <p><strong>File:</strong> {file.filename}</p>
            <p><strong>Trips:</strong> {response.summary.get('trips', 0)}</p>
            <p><strong>Pairings:</strong> {response.summary.get('pairings', 0)}</p>
            <p><strong>Credit Hours:</strong> {response.summary.get('credit_total', 0)}</p>
            <p><strong>Storage:</strong> {response.summary.get('storage', 'memory')}</p>"""
        
        if response.summary.get('database_error'):
            html_content += f'<p class="text-sm text-yellow-600 mt-2"><strong>Note:</strong> {response.summary.get("database_error", "")}</p>'
        
        html_content += """
        </div>
        """
        return HTMLResponse(html_content)

    except Exception as e:
        return HTMLResponse(f"""
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <strong>Upload Failed:</strong> Internal server error: {str(e)}
        </div>
        """)
