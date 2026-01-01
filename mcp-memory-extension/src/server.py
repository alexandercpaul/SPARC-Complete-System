"""
MCP Memory Extension Server Core
Provides semantic memory and context management for Claude Code
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
import uvicorn

from vector_store import VectorStore
from memory_manager import MemoryManager
from context_optimizer import ContextOptimizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="MCP Memory Extension",
    description="Semantic memory and context management for Claude Code",
    version="1.0.0"
)

# Initialize components
vector_store = VectorStore()
memory_manager = MemoryManager(vector_store)
context_optimizer = ContextOptimizer()

# Data models
class IngestRequest(BaseModel):
    """Request to ingest context into memory"""
    content: str = Field(..., description="Content to store")
    source_type: str = Field(..., description="Type: conversation, file, etc")
    source_name: str = Field(..., description="Source identifier")
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(default="default", description="User identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class RetrieveRequest(BaseModel):
    """Request to retrieve relevant context"""
    query: str = Field(..., description="Query text")
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(default="default", description="User identifier")
    top_k: int = Field(default=5, description="Number of results")
    filter_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    max_tokens: Optional[int] = Field(default=4000, description="Max token budget")

class ContextChunk(BaseModel):
    """Retrieved context chunk"""
    text: str
    source_type: str
    source_name: str
    timestamp: str
    relevance_score: float
    metadata: Dict[str, Any]

class RetrieveResponse(BaseModel):
    """Response with retrieved context"""
    chunks: List[ContextChunk]
    total_tokens: int
    query_time_ms: float

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mcp-memory-extension",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/v1/ingest")
async def ingest_context(request: IngestRequest, api_key: str = Header(None)):
    """
    Ingest context into memory store
    This endpoint chunks, embeds, and stores the content
    """
    try:
        logger.info(f"Ingesting content: {request.source_type}/{request.source_name}")

        # Validate API key (simple check for now)
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")

        # Ingest the content
        chunk_ids = await memory_manager.ingest(
            content=request.content,
            source_type=request.source_type,
            source_name=request.source_name,
            session_id=request.session_id,
            user_id=request.user_id,
            metadata=request.metadata or {}
        )

        return {
            "status": "success",
            "chunks_stored": len(chunk_ids),
            "chunk_ids": chunk_ids,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/v1/retrieve", response_model=RetrieveResponse)
async def retrieve_context(request: RetrieveRequest, api_key: str = Header(None)):
    """
    Retrieve relevant context from memory store
    Performs semantic search and optimizes context for token budget
    """
    try:
        start_time = asyncio.get_event_loop().time()
        logger.info(f"Retrieving context for query: {request.query[:100]}...")

        # Validate API key
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")

        # Retrieve relevant chunks
        results = await memory_manager.retrieve(
            query=request.query,
            session_id=request.session_id,
            user_id=request.user_id,
            top_k=request.top_k,
            filter_metadata=request.filter_metadata or {}
        )

        # Optimize for token budget if specified
        if request.max_tokens:
            optimized_results = context_optimizer.optimize(
                chunks=results,
                max_tokens=request.max_tokens
            )
        else:
            optimized_results = results

        # Calculate query time
        query_time = (asyncio.get_event_loop().time() - start_time) * 1000

        # Format response
        chunks = [
            ContextChunk(
                text=chunk["text"],
                source_type=chunk["metadata"]["source_type"],
                source_name=chunk["metadata"]["source_name"],
                timestamp=chunk["metadata"]["timestamp"],
                relevance_score=chunk["score"],
                metadata=chunk["metadata"]
            )
            for chunk in optimized_results
        ]

        total_tokens = sum(
            context_optimizer.estimate_tokens(chunk.text)
            for chunk in chunks
        )

        logger.info(f"Retrieved {len(chunks)} chunks in {query_time:.2f}ms")

        return RetrieveResponse(
            chunks=chunks,
            total_tokens=total_tokens,
            query_time_ms=round(query_time, 2)
        )

    except Exception as e:
        logger.error(f"Retrieval error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

@app.post("/v1/clear")
async def clear_memory(
    session_id: Optional[str] = None,
    user_id: str = "default",
    api_key: str = Header(None)
):
    """Clear memory for a specific session or user"""
    try:
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")

        count = await memory_manager.clear(session_id=session_id, user_id=user_id)

        return {
            "status": "success",
            "chunks_cleared": count,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Clear error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")

@app.get("/v1/stats")
async def get_stats(api_key: str = Header(None)):
    """Get memory store statistics"""
    try:
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")

        stats = await memory_manager.get_stats()

        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Stats error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

def start_server(host: str = "127.0.0.1", port: int = 3000):
    """Start the MCP Memory Extension server"""
    logger.info(f"Starting MCP Memory Extension server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    start_server()
