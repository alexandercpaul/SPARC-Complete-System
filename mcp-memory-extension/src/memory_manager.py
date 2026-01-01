"""
Memory Manager for MCP Memory Extension
Handles chunking, metadata, and coordination with vector store
"""
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages memory ingestion and retrieval"""

    def __init__(self, vector_store, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize Memory Manager

        Args:
            vector_store: VectorStore instance
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
        """
        self.vector_store = vector_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"MemoryManager initialized (chunk_size={chunk_size}, overlap={chunk_overlap})")

    def _chunk_text(self, text: str) -> List[str]:
        """
        Chunk text into manageable pieces

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        # Simple chunking: split by paragraphs first, then by size
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            # If paragraph is larger than chunk_size, split it
            if len(para) > self.chunk_size:
                # Add current chunk if exists
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # Split large paragraph
                words = para.split()
                for word in words:
                    if len(current_chunk) + len(word) + 1 > self.chunk_size:
                        chunks.append(current_chunk.strip())
                        # Keep overlap
                        overlap_words = current_chunk.split()[-self.chunk_overlap:]
                        current_chunk = ' '.join(overlap_words) + ' ' + word
                    else:
                        current_chunk += ' ' + word
            else:
                # Add paragraph to current chunk
                if len(current_chunk) + len(para) + 2 > self.chunk_size:
                    chunks.append(current_chunk.strip())
                    current_chunk = para
                else:
                    current_chunk += '\n\n' + para if current_chunk else para

        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]

    def _generate_chunk_id(self, text: str, source: str, index: int) -> str:
        """Generate unique ID for chunk"""
        content = f"{source}:{index}:{text[:100]}"
        return hashlib.md5(content.encode()).hexdigest()

    def _redact_secrets(self, text: str) -> str:
        """
        Redact potential secrets from text

        Args:
            text: Text to redact

        Returns:
            Redacted text
        """
        # Redact patterns that look like API keys, passwords, etc.
        patterns = [
            (r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})', '[REDACTED_API_KEY]'),
            (r'password["\']?\s*[:=]\s*["\']?([^\s"\']{8,})', '[REDACTED_PASSWORD]'),
            (r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})', '[REDACTED_TOKEN]'),
            (r'secret["\']?\s*[:=]\s*["\']?([^\s"\']{8,})', '[REDACTED_SECRET]'),
        ]

        redacted_text = text
        for pattern, replacement in patterns:
            redacted_text = re.sub(pattern, replacement, redacted_text, flags=re.IGNORECASE)

        return redacted_text

    async def ingest(
        self,
        content: str,
        source_type: str,
        source_name: str,
        session_id: str,
        user_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Ingest content into memory

        Args:
            content: Content to ingest
            source_type: Type of source (conversation, file, etc.)
            source_name: Name of source
            session_id: Session identifier
            user_id: User identifier
            metadata: Additional metadata

        Returns:
            List of chunk IDs
        """
        try:
            # Redact secrets
            safe_content = self._redact_secrets(content)

            # Chunk the content
            chunks = self._chunk_text(safe_content)

            # Prepare metadata for each chunk
            timestamp = datetime.utcnow().isoformat()
            chunk_ids = []
            chunk_metadatas = []

            for i, chunk in enumerate(chunks):
                chunk_id = self._generate_chunk_id(chunk, source_name, i)
                chunk_ids.append(chunk_id)

                chunk_metadata = {
                    "source_type": source_type,
                    "source_name": source_name,
                    "session_id": session_id,
                    "user_id": user_id,
                    "timestamp": timestamp,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    **(metadata or {})
                }
                chunk_metadatas.append(chunk_metadata)

            # Add to vector store
            stored_ids = await self.vector_store.add_chunks(
                chunks=chunks,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )

            logger.info(
                f"Ingested {len(chunks)} chunks from {source_type}/{source_name} "
                f"(session={session_id}, user={user_id})"
            )

            return stored_ids

        except Exception as e:
            logger.error(f"Error ingesting content: {str(e)}", exc_info=True)
            raise

    async def retrieve(
        self,
        query: str,
        session_id: str,
        user_id: str = "default",
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memory chunks

        Args:
            query: Query text
            session_id: Session identifier
            user_id: User identifier
            top_k: Number of results
            filter_metadata: Additional filters

        Returns:
            List of relevant chunks with metadata and scores
        """
        try:
            # Build filter to ensure user/session isolation
            filters = {
                "session_id": session_id,
                "user_id": user_id,
                **(filter_metadata or {})
            }

            # Query vector store
            results = await self.vector_store.query(
                query_text=query,
                top_k=top_k,
                filter_metadata=filters
            )

            logger.info(
                f"Retrieved {len(results)} chunks for query "
                f"(session={session_id}, user={user_id})"
            )

            return results

        except Exception as e:
            logger.error(f"Error retrieving content: {str(e)}", exc_info=True)
            raise

    async def clear(
        self,
        session_id: Optional[str] = None,
        user_id: str = "default"
    ) -> int:
        """
        Clear memory for session/user

        Args:
            session_id: Session to clear (if None, clears all for user)
            user_id: User identifier

        Returns:
            Number of chunks cleared
        """
        try:
            filters = {"user_id": user_id}
            if session_id:
                filters["session_id"] = session_id

            count = await self.vector_store.delete(filter_metadata=filters)

            logger.info(
                f"Cleared memory (session={session_id}, user={user_id}, count={count})"
            )

            return count

        except Exception as e:
            logger.error(f"Error clearing memory: {str(e)}", exc_info=True)
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            vector_stats = await self.vector_store.get_stats()

            return {
                **vector_stats,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            }

        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}", exc_info=True)
            return {}
