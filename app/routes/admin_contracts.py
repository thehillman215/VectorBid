"""
Admin Contract Management Routes

Admin-only endpoints for managing airline contracts.
"""

import logging
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from app.services.contract_extractor_v2 import ContractExtractorV2
from app.services.llm_service import LLMService
from app.services.vector_store import VectorStoreService
from app.auth.dependencies import require_admin_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/contracts", tags=["admin-contracts"])

# Security
security = HTTPBearer()

# Initialize services
llm_service = LLMService(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
)

vector_store = VectorStoreService(
    store_type=os.getenv("VECTOR_STORE_TYPE", "memory"),
    llm_service=llm_service,
)

contract_extractor = ContractExtractorV2(
    llm_service=llm_service,
    vector_store=vector_store,
)


class ContractMetadata(BaseModel):
    """Contract metadata for management"""
    airline: str = Field(..., pattern="^[A-Z]{2,4}$", description="Airline code (e.g., UAL, DAL)")
    effective_date: date = Field(..., description="Contract effective date")
    expiration_date: date = Field(..., description="Contract expiration date")
    is_active: bool = Field(default=False, description="Whether this is the active contract")
    notes: Optional[str] = Field(None, description="Admin notes about this contract")


class ContractUploadRequest(BaseModel):
    """Request for contract upload"""
    airline: str
    effective_date: date
    expiration_date: date
    is_active: bool = False
    auto_process: bool = True
    notes: Optional[str] = None


class ContractListResponse(BaseModel):
    """Response for contract listing"""
    id: str
    airline: str
    effective_date: date
    expiration_date: date
    is_active: bool
    upload_date: datetime
    status: str
    rules_count: int
    processing_cost: Optional[float]
    uploaded_by: str


class ContractStatusUpdate(BaseModel):
    """Request to update contract status"""
    is_active: bool
    notes: Optional[str] = None


@router.post("/upload", dependencies=[Depends(require_admin_role)])
async def upload_contract(
    file: UploadFile = File(...),
    airline: str = Form(..., pattern="^[A-Z]{2,4}$"),
    effective_date: date = Form(...),
    expiration_date: date = Form(...),
    is_active: bool = Form(False),
    auto_process: bool = Form(True),
    notes: Optional[str] = Form(None),
    current_user: dict = Depends(require_admin_role),
):
    """
    Upload a new airline contract (Admin only).
    
    This endpoint:
    1. Validates admin permissions
    2. Stores contract with proper metadata
    3. Optionally processes rules extraction immediately
    4. Manages active contract designation
    
    Args:
        file: PDF contract file
        airline: Airline code (e.g., UAL, DAL)
        effective_date: Contract start date
        expiration_date: Contract end date
        is_active: Whether this becomes the active contract
        auto_process: Automatically extract rules after upload
        notes: Admin notes about the contract
        current_user: Authenticated admin user
    
    Returns:
        Contract upload status and metadata
    """
    
    try:
        # Validate file
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
        
        # Validate dates
        if effective_date >= expiration_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Effective date must be before expiration date"
            )
        
        # Generate version from dates
        version = f"{effective_date.year}.{effective_date.month:02d}"
        
        # Check for existing active contract
        if is_active:
            await _deactivate_existing_contracts(airline)
        
        # Save contract file
        contract_dir = Path("contracts") / airline
        contract_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{airline}_contract_{version}.pdf"
        file_path = contract_dir / filename
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Store in database
        from app.db.database import AsyncSessionLocal
        from app.db.models import PilotContract
        import uuid
        
        async with AsyncSessionLocal() as session:
            contract_id = uuid.uuid4()
            
            contract = PilotContract(
                id=contract_id,
                airline=airline,
                contract_version=version,
                title=f"{airline} Contract {effective_date.year}-{expiration_date.year}",
                file_name=filename,
                file_size=len(content),
                file_content=content,
                mime_type="application/pdf",
                uploaded_by=uuid.UUID(current_user["id"]),
                status="uploaded",
                parsing_status="pending" if auto_process else "manual",
                contract_type="collective_bargaining",
                description=notes,
                metadata={
                    "effective_date": effective_date.isoformat(),
                    "expiration_date": expiration_date.isoformat(),
                    "is_active": is_active,
                    "uploaded_by_email": current_user["email"],
                    "uploaded_at": datetime.now().isoformat(),
                }
            )
            
            session.add(contract)
            await session.commit()
            
            logger.info(
                f"Admin {current_user['email']} uploaded contract {airline} v{version}, "
                f"active={is_active}, effective={effective_date}"
            )
            
            # Process contract if requested
            processing_result = None
            if auto_process:
                try:
                    processing_result = await contract_extractor.process_contract(
                        pdf_path=file_path,
                        airline=airline,
                        version=version,
                        auto_approve=False,  # Always require admin approval
                    )
                    
                    # Update contract status
                    contract.parsing_status = "completed"
                    contract.parsed_data = {
                        "rules_extracted": processing_result.get("rules_extracted", 0),
                        "processing_time": processing_result.get("processing_time_seconds", 0),
                        "llm_cost": processing_result.get("llm_costs", {}).get("total_cost", 0),
                    }
                    await session.commit()
                    
                except Exception as e:
                    logger.error(f"Auto-processing failed: {e}")
                    contract.parsing_status = "failed"
                    contract.error_message = str(e)
                    await session.commit()
            
            return {
                "contract_id": str(contract_id),
                "airline": airline,
                "version": version,
                "effective_date": effective_date.isoformat(),
                "expiration_date": expiration_date.isoformat(),
                "is_active": is_active,
                "status": "uploaded",
                "processing_status": contract.parsing_status,
                "processing_result": processing_result,
                "message": f"Contract uploaded successfully by {current_user['email']}",
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Contract upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/list", dependencies=[Depends(require_admin_role)])
async def list_contracts(
    airline: Optional[str] = Query(None, pattern="^[A-Z]{2,4}$"),
    active_only: bool = Query(False),
    current_user: dict = Depends(require_admin_role),
) -> List[ContractListResponse]:
    """
    List all contracts (Admin only).
    
    Args:
        airline: Optional filter by airline
        active_only: Only show active contracts
        current_user: Authenticated admin user
    
    Returns:
        List of contracts with metadata
    """
    
    from app.db.database import AsyncSessionLocal
    from app.db.models import PilotContract, User
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    
    async with AsyncSessionLocal() as session:
        query = select(PilotContract).options(joinedload(PilotContract.uploaded_by))
        
        if airline:
            query = query.where(PilotContract.airline == airline)
        
        result = await session.execute(query)
        contracts = result.unique().scalars().all()
        
        response = []
        for contract in contracts:
            metadata = contract.metadata or {}
            
            # Filter by active status if requested
            if active_only and not metadata.get("is_active", False):
                continue
            
            # Get uploader info
            uploader_query = select(User).where(User.id == contract.uploaded_by)
            uploader_result = await session.execute(uploader_query)
            uploader = uploader_result.scalar_one_or_none()
            
            response.append(ContractListResponse(
                id=str(contract.id),
                airline=contract.airline,
                effective_date=date.fromisoformat(metadata.get("effective_date", "2025-01-01")),
                expiration_date=date.fromisoformat(metadata.get("expiration_date", "2026-01-01")),
                is_active=metadata.get("is_active", False),
                upload_date=contract.created_at,
                status=contract.status,
                rules_count=contract.parsed_data.get("rules_extracted", 0) if contract.parsed_data else 0,
                processing_cost=contract.parsed_data.get("llm_cost") if contract.parsed_data else None,
                uploaded_by=uploader.email if uploader else "Unknown",
            ))
        
        return response


@router.patch("/{contract_id}/status", dependencies=[Depends(require_admin_role)])
async def update_contract_status(
    contract_id: str,
    update: ContractStatusUpdate,
    current_user: dict = Depends(require_admin_role),
):
    """
    Update contract status (Admin only).
    
    Args:
        contract_id: Contract UUID
        update: Status update request
        current_user: Authenticated admin user
    
    Returns:
        Updated contract status
    """
    
    from app.db.database import AsyncSessionLocal
    from app.db.models import PilotContract
    from sqlalchemy import select
    import uuid
    
    async with AsyncSessionLocal() as session:
        query = select(PilotContract).where(PilotContract.id == uuid.UUID(contract_id))
        result = await session.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        # Update active status
        if update.is_active:
            # Deactivate other contracts for this airline
            await _deactivate_existing_contracts(contract.airline, exclude_id=contract_id)
        
        # Update metadata
        metadata = contract.metadata or {}
        metadata["is_active"] = update.is_active
        metadata["last_updated_by"] = current_user["email"]
        metadata["last_updated_at"] = datetime.now().isoformat()
        
        if update.notes:
            metadata["admin_notes"] = update.notes
        
        contract.metadata = metadata
        await session.commit()
        
        logger.info(
            f"Admin {current_user['email']} updated contract {contract_id}: "
            f"active={update.is_active}"
        )
        
        return {
            "contract_id": contract_id,
            "airline": contract.airline,
            "version": contract.contract_version,
            "is_active": update.is_active,
            "updated_by": current_user["email"],
            "updated_at": datetime.now().isoformat(),
        }


@router.post("/{contract_id}/process", dependencies=[Depends(require_admin_role)])
async def process_contract(
    contract_id: str,
    current_user: dict = Depends(require_admin_role),
):
    """
    Manually trigger contract processing (Admin only).
    
    Args:
        contract_id: Contract UUID
        current_user: Authenticated admin user
    
    Returns:
        Processing status and results
    """
    
    from app.db.database import AsyncSessionLocal
    from app.db.models import PilotContract
    from sqlalchemy import select
    import uuid
    
    async with AsyncSessionLocal() as session:
        query = select(PilotContract).where(PilotContract.id == uuid.UUID(contract_id))
        result = await session.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        # Check if already processed
        if contract.parsing_status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract already processed"
            )
        
        # Get file path
        contract_dir = Path("contracts") / contract.airline
        file_path = contract_dir / contract.file_name
        
        if not file_path.exists():
            # Recreate from database
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(contract.file_content)
        
        try:
            # Process contract
            processing_result = await contract_extractor.process_contract(
                pdf_path=file_path,
                airline=contract.airline,
                version=contract.contract_version,
                auto_approve=False,
            )
            
            # Update contract
            contract.parsing_status = "completed"
            contract.status = "pending_approval"
            contract.parsed_data = {
                "rules_extracted": processing_result.get("rules_extracted", 0),
                "processing_time": processing_result.get("processing_time_seconds", 0),
                "llm_cost": processing_result.get("llm_costs", {}).get("total_cost", 0),
                "processed_by": current_user["email"],
                "processed_at": datetime.now().isoformat(),
            }
            await session.commit()
            
            logger.info(
                f"Admin {current_user['email']} processed contract {contract_id}: "
                f"{processing_result.get('rules_extracted', 0)} rules extracted"
            )
            
            return {
                "contract_id": contract_id,
                "status": "success",
                "rules_extracted": processing_result.get("rules_extracted", 0),
                "processing_time": processing_result.get("processing_time_seconds", 0),
                "cost": processing_result.get("llm_costs", {}).get("total_cost", 0),
                "message": f"Contract processed successfully by {current_user['email']}",
            }
            
        except Exception as e:
            # Update failure status
            contract.parsing_status = "failed"
            contract.error_message = str(e)
            await session.commit()
            
            logger.error(f"Contract processing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Processing failed: {str(e)}"
            )


@router.delete("/{contract_id}", dependencies=[Depends(require_admin_role)])
async def delete_contract(
    contract_id: str,
    current_user: dict = Depends(require_admin_role),
):
    """
    Delete a contract (Admin only).
    
    Args:
        contract_id: Contract UUID
        current_user: Authenticated admin user
    
    Returns:
        Deletion confirmation
    """
    
    from app.db.database import AsyncSessionLocal
    from app.db.models import PilotContract
    from sqlalchemy import select
    import uuid
    
    async with AsyncSessionLocal() as session:
        query = select(PilotContract).where(PilotContract.id == uuid.UUID(contract_id))
        result = await session.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        # Check if active
        metadata = contract.metadata or {}
        if metadata.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete active contract. Deactivate it first."
            )
        
        # Remove from vector store
        await vector_store.delete_contract(contract.airline, contract.contract_version)
        
        # Delete from database
        await session.delete(contract)
        await session.commit()
        
        logger.info(
            f"Admin {current_user['email']} deleted contract {contract_id} "
            f"({contract.airline} v{contract.contract_version})"
        )
        
        return {
            "contract_id": contract_id,
            "status": "deleted",
            "deleted_by": current_user["email"],
            "deleted_at": datetime.now().isoformat(),
        }


async def _deactivate_existing_contracts(
    airline: str,
    exclude_id: Optional[str] = None
):
    """
    Deactivate all existing contracts for an airline.
    
    Args:
        airline: Airline code
        exclude_id: Contract ID to exclude from deactivation
    """
    
    from app.db.database import AsyncSessionLocal
    from app.db.models import PilotContract
    from sqlalchemy import select
    import uuid
    
    async with AsyncSessionLocal() as session:
        query = select(PilotContract).where(PilotContract.airline == airline)
        
        if exclude_id:
            query = query.where(PilotContract.id != uuid.UUID(exclude_id))
        
        result = await session.execute(query)
        contracts = result.scalars().all()
        
        for contract in contracts:
            metadata = contract.metadata or {}
            if metadata.get("is_active", False):
                metadata["is_active"] = False
                metadata["deactivated_at"] = datetime.now().isoformat()
                contract.metadata = metadata
        
        await session.commit()