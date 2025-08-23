"""
Vector Store Service

Manages embeddings and semantic search for contract rules.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RuleVector(BaseModel):
    """Represents a vectorized contract rule"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    rule_id: str
    airline: str
    contract_version: str
    
    # Content
    original_text: str
    description: str
    category: str
    subcategory: Optional[str] = None
    
    # Rule logic
    is_hard_constraint: bool
    dsl_expression: Optional[str] = None
    parameters: Dict[str, Any] = {}
    
    # Metadata
    source_section: Optional[str] = None
    source_pages: List[int] = []
    related_rules: List[str] = []
    
    # Vector data
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0


class VectorStore:
    """
    Abstract base class for vector stores.
    Implementations can use Pinecone, Weaviate, Qdrant, or PostgreSQL with pgvector.
    """
    
    async def upsert(self, vectors: List[RuleVector]) -> bool:
        """Insert or update vectors"""
        raise NotImplementedError
    
    async def search(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        top_k: int = 100,
    ) -> List[Tuple[RuleVector, float]]:
        """Search for similar vectors"""
        raise NotImplementedError
    
    async def delete(self, rule_ids: List[str]) -> bool:
        """Delete vectors by rule ID"""
        raise NotImplementedError
    
    async def get_by_filter(self, filters: Dict[str, Any]) -> List[RuleVector]:
        """Get all vectors matching filters"""
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    """
    In-memory vector store for development and testing.
    For production, use Pinecone, Weaviate, or Qdrant.
    """
    
    def __init__(self):
        self.vectors: Dict[str, RuleVector] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
    
    async def upsert(self, vectors: List[RuleVector]) -> bool:
        """Insert or update vectors in memory"""
        try:
            for vector in vectors:
                self.vectors[vector.rule_id] = vector
                if vector.embedding:
                    self.embeddings[vector.rule_id] = np.array(vector.embedding)
            
            logger.info(f"Upserted {len(vectors)} vectors to in-memory store")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            return False
    
    async def search(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        top_k: int = 100,
    ) -> List[Tuple[RuleVector, float]]:
        """Search for similar vectors using cosine similarity"""
        
        query_vec = np.array(query_embedding)
        results = []
        
        for rule_id, vector in self.vectors.items():
            # Apply filters
            if filters:
                if "airline" in filters and vector.airline != filters["airline"]:
                    continue
                if "contract_version" in filters and vector.contract_version != filters["contract_version"]:
                    continue
                if "category" in filters and vector.category != filters["category"]:
                    continue
            
            # Calculate similarity if embedding exists
            if rule_id in self.embeddings:
                embedding = self.embeddings[rule_id]
                
                # Cosine similarity
                similarity = np.dot(query_vec, embedding) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(embedding)
                )
                
                results.append((vector, float(similarity)))
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Update access tracking
        for vector, _ in results[:top_k]:
            vector.last_accessed = datetime.now()
            vector.access_count += 1
        
        return results[:top_k]
    
    async def delete(self, rule_ids: List[str]) -> bool:
        """Delete vectors by rule ID"""
        try:
            for rule_id in rule_ids:
                self.vectors.pop(rule_id, None)
                self.embeddings.pop(rule_id, None)
            
            logger.info(f"Deleted {len(rule_ids)} vectors from in-memory store")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return False
    
    async def get_by_filter(self, filters: Dict[str, Any]) -> List[RuleVector]:
        """Get all vectors matching filters"""
        results = []
        
        for vector in self.vectors.values():
            if self._matches_filters(vector, filters):
                results.append(vector)
        
        return results
    
    def _matches_filters(self, vector: RuleVector, filters: Dict[str, Any]) -> bool:
        """Check if vector matches all filters"""
        if not filters:
            return True
        
        for key, value in filters.items():
            if key == "airline" and vector.airline != value:
                return False
            elif key == "contract_version" and vector.contract_version != value:
                return False
            elif key == "category" and vector.category != value:
                return False
            elif key == "is_hard_constraint" and vector.is_hard_constraint != value:
                return False
        
        return True


class PineconeVectorStore(VectorStore):
    """
    Pinecone vector store implementation for production use.
    """
    
    def __init__(self, api_key: str, environment: str, index_name: str):
        import pinecone
        
        pinecone.init(api_key=api_key, environment=environment)
        
        # Create index if it doesn't exist
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=index_name,
                dimension=1536,  # OpenAI ada-002 dimension
                metric="cosine",
                metadata_config={
                    "indexed": ["airline", "contract_version", "category"]
                }
            )
        
        self.index = pinecone.Index(index_name)
    
    async def upsert(self, vectors: List[RuleVector]) -> bool:
        """Insert or update vectors in Pinecone"""
        try:
            # Prepare vectors for Pinecone
            pinecone_vectors = []
            
            for vector in vectors:
                if not vector.embedding:
                    continue
                
                metadata = {
                    "rule_id": vector.rule_id,
                    "airline": vector.airline,
                    "contract_version": vector.contract_version,
                    "category": vector.category,
                    "subcategory": vector.subcategory or "",
                    "description": vector.description,
                    "original_text": vector.original_text[:1000],  # Truncate for metadata limits
                    "is_hard_constraint": vector.is_hard_constraint,
                    "dsl_expression": vector.dsl_expression or "",
                    "source_section": vector.source_section or "",
                    "source_pages": json.dumps(vector.source_pages),
                    "related_rules": json.dumps(vector.related_rules),
                    "parameters": json.dumps(vector.parameters),
                }
                
                pinecone_vectors.append({
                    "id": vector.id,
                    "values": vector.embedding,
                    "metadata": metadata,
                })
            
            # Batch upsert
            batch_size = 100
            for i in range(0, len(pinecone_vectors), batch_size):
                batch = pinecone_vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            logger.info(f"Upserted {len(pinecone_vectors)} vectors to Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert to Pinecone: {e}")
            return False
    
    async def search(
        self,
        query_embedding: List[float],
        filters: Dict[str, Any],
        top_k: int = 100,
    ) -> List[Tuple[RuleVector, float]]:
        """Search Pinecone for similar vectors"""
        
        # Build filter query
        pinecone_filter = {}
        if "airline" in filters:
            pinecone_filter["airline"] = filters["airline"]
        if "contract_version" in filters:
            pinecone_filter["contract_version"] = filters["contract_version"]
        if "category" in filters:
            pinecone_filter["category"] = filters["category"]
        if "is_hard_constraint" in filters:
            pinecone_filter["is_hard_constraint"] = filters["is_hard_constraint"]
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            filter=pinecone_filter if pinecone_filter else None,
            top_k=top_k,
            include_metadata=True,
        )
        
        # Convert results to RuleVector objects
        output = []
        for match in results.matches:
            metadata = match.metadata
            
            vector = RuleVector(
                id=match.id,
                rule_id=metadata["rule_id"],
                airline=metadata["airline"],
                contract_version=metadata["contract_version"],
                category=metadata["category"],
                subcategory=metadata.get("subcategory") or None,
                description=metadata["description"],
                original_text=metadata["original_text"],
                is_hard_constraint=metadata["is_hard_constraint"],
                dsl_expression=metadata.get("dsl_expression") or None,
                source_section=metadata.get("source_section") or None,
                source_pages=json.loads(metadata.get("source_pages", "[]")),
                related_rules=json.loads(metadata.get("related_rules", "[]")),
                parameters=json.loads(metadata.get("parameters", "{}")),
            )
            
            output.append((vector, match.score))
        
        return output
    
    async def delete(self, rule_ids: List[str]) -> bool:
        """Delete vectors from Pinecone by rule ID"""
        try:
            # Need to first query to get the vector IDs
            for rule_id in rule_ids:
                # Query by metadata
                results = self.index.query(
                    vector=[0] * 1536,  # Dummy vector
                    filter={"rule_id": rule_id},
                    top_k=100,
                )
                
                # Delete by IDs
                ids_to_delete = [match.id for match in results.matches]
                if ids_to_delete:
                    self.index.delete(ids=ids_to_delete)
            
            logger.info(f"Deleted vectors for {len(rule_ids)} rule IDs from Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete from Pinecone: {e}")
            return False
    
    async def get_by_filter(self, filters: Dict[str, Any]) -> List[RuleVector]:
        """Get all vectors matching filters from Pinecone"""
        
        # Pinecone doesn't support getting all by filter without a query vector
        # So we use a dummy query with high top_k
        dummy_vector = [0] * 1536
        results = await self.search(dummy_vector, filters, top_k=10000)
        
        return [vector for vector, _ in results]


class VectorStoreService:
    """
    Main service for managing contract rule vectors.
    """
    
    def __init__(
        self,
        store_type: str = "memory",
        llm_service=None,
        **store_config
    ):
        """
        Initialize vector store service.
        
        Args:
            store_type: Type of vector store ("memory", "pinecone", "weaviate", "qdrant")
            llm_service: LLM service for generating embeddings
            **store_config: Configuration for the specific store type
        """
        self.llm_service = llm_service
        
        # Initialize appropriate store
        if store_type == "memory":
            self.store = InMemoryVectorStore()
        elif store_type == "pinecone":
            self.store = PineconeVectorStore(**store_config)
        else:
            raise ValueError(f"Unknown store type: {store_type}")
        
        self.stats = {
            "total_vectors": 0,
            "searches_performed": 0,
            "average_search_results": 0.0,
        }
    
    async def index_contract_rules(
        self,
        rules: List[Dict[str, Any]],
        airline: str,
        contract_version: str,
    ) -> bool:
        """
        Index contract rules with embeddings.
        
        Args:
            rules: List of extracted rules
            airline: Airline code
            contract_version: Contract version
        
        Returns:
            Success status
        """
        try:
            # Prepare texts for embedding
            texts_to_embed = []
            for rule in rules:
                # Combine relevant fields for embedding
                text = f"{rule.get('description', '')} {rule.get('original_text', '')}"
                texts_to_embed.append(text)
            
            # Generate embeddings
            if self.llm_service:
                embeddings = await self.llm_service.generate_embeddings(texts_to_embed)
            else:
                # Use dummy embeddings for testing
                embeddings = [np.random.randn(1536).tolist() for _ in texts_to_embed]
            
            # Create RuleVector objects
            vectors = []
            for rule, embedding in zip(rules, embeddings):
                vector = RuleVector(
                    rule_id=rule["rule_id"],
                    airline=airline,
                    contract_version=contract_version,
                    original_text=rule.get("original_text", ""),
                    description=rule.get("description", ""),
                    category=rule.get("category", "unknown"),
                    subcategory=rule.get("subcategory"),
                    is_hard_constraint=rule.get("is_hard_constraint", False),
                    dsl_expression=rule.get("dsl_expression"),
                    parameters=rule.get("parameters", {}),
                    source_section=rule.get("source_section"),
                    source_pages=rule.get("source_pages", []),
                    related_rules=rule.get("related_rules", []),
                    embedding=embedding,
                    embedding_model="text-embedding-ada-002",
                )
                vectors.append(vector)
            
            # Store vectors
            success = await self.store.upsert(vectors)
            
            if success:
                self.stats["total_vectors"] += len(vectors)
                logger.info(f"Indexed {len(vectors)} rules for {airline} v{contract_version}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to index contract rules: {e}")
            return False
    
    async def search_rules(
        self,
        query: str,
        airline: str,
        contract_version: str,
        category: Optional[str] = None,
        top_k: int = 100,
    ) -> List[Tuple[RuleVector, float]]:
        """
        Search for relevant rules using semantic similarity.
        
        Args:
            query: Search query text
            airline: Filter by airline
            contract_version: Filter by contract version
            category: Optional category filter
            top_k: Number of results to return
        
        Returns:
            List of (rule, similarity_score) tuples
        """
        try:
            # Generate query embedding
            if self.llm_service:
                query_embedding = (await self.llm_service.generate_embeddings([query]))[0]
            else:
                # Use dummy embedding for testing
                query_embedding = np.random.randn(1536).tolist()
            
            # Build filters
            filters = {
                "airline": airline,
                "contract_version": contract_version,
            }
            if category:
                filters["category"] = category
            
            # Search
            results = await self.store.search(query_embedding, filters, top_k)
            
            # Update stats
            self.stats["searches_performed"] += 1
            self.stats["average_search_results"] = (
                (self.stats["average_search_results"] * (self.stats["searches_performed"] - 1) + len(results))
                / self.stats["searches_performed"]
            )
            
            logger.info(f"Found {len(results)} rules for query: {query[:50]}...")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search rules: {e}")
            return []
    
    async def get_all_rules(
        self,
        airline: str,
        contract_version: str,
        category: Optional[str] = None,
    ) -> List[RuleVector]:
        """
        Get all rules for a specific contract.
        
        Args:
            airline: Airline code
            contract_version: Contract version
            category: Optional category filter
        
        Returns:
            List of all matching rules
        """
        filters = {
            "airline": airline,
            "contract_version": contract_version,
        }
        if category:
            filters["category"] = category
        
        return await self.store.get_by_filter(filters)
    
    async def delete_contract(self, airline: str, contract_version: str) -> bool:
        """
        Delete all rules for a specific contract.
        
        Args:
            airline: Airline code
            contract_version: Contract version to delete
        
        Returns:
            Success status
        """
        try:
            # Get all rules for this contract
            rules = await self.get_all_rules(airline, contract_version)
            rule_ids = [rule.rule_id for rule in rules]
            
            # Delete them
            success = await self.store.delete(rule_ids)
            
            if success:
                self.stats["total_vectors"] -= len(rule_ids)
                logger.info(f"Deleted {len(rule_ids)} rules for {airline} v{contract_version}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete contract: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return self.stats