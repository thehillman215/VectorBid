"""
Contract Extraction Service V2

Enhanced extraction pipeline using dual-model architecture and vector storage.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import PyPDF2
import yaml
from pydantic import BaseModel, Field

from .llm_service import LLMModel, LLMService
from .vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class ContractExtractorV2:
    """
    Enhanced contract extraction service with:
    - Dual-model architecture (heavy for extraction, fast for runtime)
    - Vector storage for semantic search
    - Full context preservation
    """
    
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        vector_store: Optional[VectorStoreService] = None,
        cache_dir: Optional[Path] = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.vector_store = vector_store or VectorStoreService(store_type="memory")
        self.cache_dir = cache_dir or Path("/tmp/contract_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_contract(
        self,
        pdf_path: Path,
        airline: str,
        version: str,
        auto_approve: bool = False,
    ) -> Dict[str, Any]:
        """
        Complete contract processing pipeline.
        
        Args:
            pdf_path: Path to contract PDF
            airline: Airline code
            version: Contract version
            auto_approve: Skip manual approval if confidence is high
        
        Returns:
            Processing result with statistics
        """
        
        logger.info(f"Starting contract processing for {airline} v{version}")
        start_time = datetime.now()
        
        try:
            # Step 1: Extract text from PDF
            logger.info("Extracting text from PDF...")
            contract_text = await self._extract_pdf_text(pdf_path)
            
            # Step 2: Extract rules using heavy model (Opus/GPT-4o)
            logger.info("Extracting rules with Claude 3 Opus...")
            extraction_result = await self.llm_service.extract_contract_rules(
                contract_text=contract_text,
                airline=airline,
                contract_version=version,
                model=LLMModel.CLAUDE_3_OPUS,  # Heavy model for accuracy
            )
            
            rules = extraction_result.get("rules", [])
            logger.info(f"Extracted {len(rules)} rules")
            
            # Step 3: Validate and enhance rules
            logger.info("Validating rules with GPT-4 Turbo...")
            validated_rules = await self.llm_service.validate_rules(
                rules=rules,
                model=LLMModel.GPT_4_TURBO,  # Fast model for validation
            )
            
            # Step 4: Generate embeddings and store in vector database
            logger.info("Indexing rules in vector store...")
            indexed = await self.vector_store.index_contract_rules(
                rules=validated_rules,
                airline=airline,
                contract_version=version,
            )
            
            # Step 5: Save to database and cache
            await self._save_contract_to_db(
                airline=airline,
                version=version,
                rules=validated_rules,
                pdf_path=pdf_path,
                contract_text=contract_text,
            )
            
            # Step 6: Generate YAML rule pack
            rule_pack_path = await self._generate_rule_pack(
                airline=airline,
                version=version,
                rules=validated_rules,
            )
            
            # Calculate processing time and costs
            processing_time = (datetime.now() - start_time).total_seconds()
            usage_stats = self.llm_service.get_usage_stats()
            
            result = {
                "status": "success",
                "airline": airline,
                "version": version,
                "rules_extracted": len(validated_rules),
                "processing_time_seconds": processing_time,
                "llm_costs": {
                    "total_cost": usage_stats["total_cost"],
                    "input_tokens": usage_stats["total_input_tokens"],
                    "output_tokens": usage_stats["total_output_tokens"],
                },
                "rule_pack_path": str(rule_pack_path),
                "vector_store_indexed": indexed,
                "requires_approval": not auto_approve and self._needs_approval(validated_rules),
            }
            
            logger.info(
                f"Contract processing complete: {len(validated_rules)} rules, "
                f"${usage_stats['total_cost']:.2f} cost, {processing_time:.1f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Contract processing failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "airline": airline,
                "version": version,
            }
    
    async def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF file"""
        
        text_parts = []
        
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
            
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                
                # Add page markers for reference
                text_parts.append(f"\n\n=== PAGE {page_num} of {total_pages} ===\n")
                text_parts.append(page_text)
        
        full_text = "".join(text_parts)
        logger.info(f"Extracted {len(full_text)} characters from {total_pages} pages")
        
        return full_text
    
    async def _save_contract_to_db(
        self,
        airline: str,
        version: str,
        rules: List[Dict[str, Any]],
        pdf_path: Path,
        contract_text: str,
    ):
        """Save contract and rules to database"""
        
        from app.db.database import AsyncSessionLocal
        from app.db.models import PilotContract, ContractRule
        from sqlalchemy import text
        import uuid
        
        async with AsyncSessionLocal() as session:
            try:
                # Read PDF content
                with open(pdf_path, "rb") as f:
                    pdf_content = f.read()
                
                # Create contract record
                contract_id = uuid.uuid4()
                
                contract = PilotContract(
                    id=contract_id,
                    airline=airline,
                    contract_version=version,
                    title=f"{airline} Contract v{version}",
                    file_name=pdf_path.name,
                    file_size=len(pdf_content),
                    file_content=pdf_content,
                    mime_type="application/pdf",
                    uploaded_by=uuid.uuid4(),  # Would be actual user ID
                    status="processed",
                    parsing_status="completed",
                    parsed_data={
                        "total_pages": len(PyPDF2.PdfReader(pdf_path.open("rb")).pages),
                        "total_rules": len(rules),
                        "extraction_date": datetime.now().isoformat(),
                    },
                )
                
                session.add(contract)
                
                # Create rule records
                for rule in rules:
                    rule_record = ContractRule(
                        id=uuid.uuid4(),
                        contract_id=contract_id,
                        rule_id=rule.get("rule_id"),
                        category=rule.get("category", "unknown"),
                        subcategory=rule.get("subcategory"),
                        description=rule.get("description", ""),
                        rule_text=rule.get("original_text", ""),
                        parameters=rule.get("parameters", {}),
                    )
                    session.add(rule_record)
                
                await session.commit()
                logger.info(f"Saved contract and {len(rules)} rules to database")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to save to database: {e}")
                raise
    
    async def _generate_rule_pack(
        self,
        airline: str,
        version: str,
        rules: List[Dict[str, Any]],
    ) -> Path:
        """Generate YAML rule pack from extracted rules"""
        
        # Initialize rule pack structure
        rule_pack = {
            "version": version,
            "airline": airline,
            "id": f"{airline}-{version.replace('.', '-')}",
            "generated_at": datetime.now().isoformat(),
            "far117": {"hard": [], "soft": []},
            "union": {"hard": [], "soft": []},
            "operational": {"hard": [], "soft": []},
            "scheduling": {"hard": [], "soft": []},
            "rest": {"hard": [], "soft": []},
            "compensation": {"hard": [], "soft": []},
            "training": {"hard": [], "soft": []},
        }
        
        # Organize rules by category
        for rule in rules:
            category = rule.get("category", "operational")
            if category not in rule_pack:
                rule_pack[category] = {"hard": [], "soft": []}
            
            rule_entry = {
                "id": rule.get("rule_id"),
                "desc": rule.get("description", ""),
                "clause": f"{airline}-CBA#{rule.get('source_section', 'unknown')}",
            }
            
            if rule.get("is_hard_constraint", False):
                rule_entry["check"] = rule.get("dsl_expression", "True")
                if rule.get("validation_notes"):
                    rule_entry["notes"] = rule["validation_notes"]
                rule_pack[category]["hard"].append(rule_entry)
            else:
                rule_entry["weight"] = rule.get("weight", 0.5)
                rule_entry["score"] = rule.get("dsl_expression", "0.5")
                rule_pack[category]["soft"].append(rule_entry)
        
        # Save to file
        output_dir = Path("rule_packs") / airline
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"{version}.yml"
        
        with open(output_path, "w") as f:
            yaml.dump(rule_pack, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Generated rule pack at {output_path}")
        return output_path
    
    def _needs_approval(self, rules: List[Dict[str, Any]]) -> bool:
        """Check if rules need manual approval"""
        
        for rule in rules:
            # Require approval if any rule has low confidence or validation issues
            if rule.get("confidence_score", 0) < 0.8:
                return True
            if rule.get("validation_notes"):
                return True
            if rule.get("requires_review", False):
                return True
        
        return False
    
    async def search_contract_rules(
        self,
        query: str,
        airline: str,
        version: str,
        top_k: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Search for specific rules in a contract.
        
        Args:
            query: Search query
            airline: Airline code
            version: Contract version
            top_k: Number of results
        
        Returns:
            List of matching rules with similarity scores
        """
        
        results = await self.vector_store.search_rules(
            query=query,
            airline=airline,
            contract_version=version,
            top_k=top_k,
        )
        
        # Format results
        formatted_results = []
        for rule_vector, score in results:
            formatted_results.append({
                "rule_id": rule_vector.rule_id,
                "description": rule_vector.description,
                "original_text": rule_vector.original_text,
                "category": rule_vector.category,
                "is_hard_constraint": rule_vector.is_hard_constraint,
                "dsl_expression": rule_vector.dsl_expression,
                "similarity_score": score,
                "source_section": rule_vector.source_section,
                "source_pages": rule_vector.source_pages,
            })
        
        return formatted_results
    
    async def get_all_contract_rules(
        self,
        airline: str,
        version: str,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all rules for a contract, optionally filtered by category.
        
        Args:
            airline: Airline code  
            version: Contract version
            category: Optional category filter
        
        Returns:
            List of all matching rules
        """
        
        rules = await self.vector_store.get_all_rules(
            airline=airline,
            contract_version=version,
            category=category,
        )
        
        # Format results
        formatted_rules = []
        for rule in rules:
            formatted_rules.append({
                "rule_id": rule.rule_id,
                "description": rule.description,
                "original_text": rule.original_text,
                "category": rule.category,
                "subcategory": rule.subcategory,
                "is_hard_constraint": rule.is_hard_constraint,
                "dsl_expression": rule.dsl_expression,
                "parameters": rule.parameters,
                "source_section": rule.source_section,
                "source_pages": rule.source_pages,
                "related_rules": rule.related_rules,
            })
        
        return formatted_rules