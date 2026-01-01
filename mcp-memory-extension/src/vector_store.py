"""
Vector Storage Layer for MCP Memory Extension
Simple in-memory implementation with numpy for semantic search
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorStore:
    """Simple in-memory vector storage with numpy"""

    def __init__(self, persist_directory: Optional[str] = None, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize vector store

        Args:
            persist_directory: Directory to persist data (default: ~/.mcp-memory)
            model_name: Sentence transformer model name
        """
        if persist_directory is None:
            persist_directory = str(Path.home() / ".mcp-memory")

        self.persist_dir = Path(persist_directory)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.data_file = self.persist_dir / "vector_store.pkl"

        logger.info(f"Initializing VectorStore at {persist_directory}")
        logger.info(f"Loading embedding model: {model_name}")

        # Load sentence transformer model
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

        # Storage
        self.documents = []  # List of document texts
        self.embeddings = None  # numpy array of embeddings
        self.metadatas = []  # List of metadata dicts
        self.ids = []  # List of document IDs

        # Load from disk if exists
        self._load()

        logger.info(f"VectorStore initialized with {len(self.documents)} existing documents")

    def _load(self):
        """Load data from disk"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents', [])
                    self.embeddings = data.get('embeddings')
                    self.metadatas = data.get('metadatas', [])
                    self.ids = data.get('ids', [])
                logger.info(f"Loaded {len(self.documents)} documents from disk")
            except Exception as e:
                logger.warning(f"Failed to load data: {e}")

    def _save(self):
        """Save data to disk"""
        try:
            data = {
                'documents': self.documents,
                'embeddings': self.embeddings,
                'metadatas': self.metadatas,
                'ids': self.ids
            }
            with open(self.data_file, 'wb') as f:
                pickle.dump(data, f)
            logger.debug("Saved vector store to disk")
        except Exception as e:
            logger.error(f"Failed to save data: {e}")

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between query and all documents"""
        # Normalize
        a_norm = a / (np.linalg.norm(a) + 1e-10)
        b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)

        # Compute similarity
        return np.dot(b_norm, a_norm)

    async def add_chunks(
        self,
        chunks: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> List[str]:
        """
        Add text chunks to vector store

        Args:
            chunks: List of text chunks
            metadatas: List of metadata dicts
            ids: List of unique IDs

        Returns:
            List of stored chunk IDs
        """
        try:
            # Generate embeddings
            new_embeddings = self.model.encode(chunks, convert_to_numpy=True)

            # Add to storage
            if self.embeddings is None:
                self.embeddings = new_embeddings
            else:
                self.embeddings = np.vstack([self.embeddings, new_embeddings])

            self.documents.extend(chunks)
            self.metadatas.extend(metadatas)
            self.ids.extend(ids)

            # Save to disk
            self._save()

            logger.info(f"Added {len(chunks)} chunks to vector store")
            return ids

        except Exception as e:
            logger.error(f"Error adding chunks: {str(e)}", exc_info=True)
            raise

    async def query(
        self,
        query_text: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query vector store for similar chunks

        Args:
            query_text: Query text
            top_k: Number of results to return
            filter_metadata: Metadata filters

        Returns:
            List of results with text, metadata, and scores
        """
        try:
            if len(self.documents) == 0:
                return []

            # Generate query embedding
            query_embedding = self.model.encode([query_text], convert_to_numpy=True)[0]

            # Apply metadata filters
            valid_indices = []
            for i, metadata in enumerate(self.metadatas):
                if filter_metadata:
                    # Check if all filter criteria match
                    match = all(
                        metadata.get(k) == v
                        for k, v in filter_metadata.items()
                    )
                    if match:
                        valid_indices.append(i)
                else:
                    valid_indices.append(i)

            if not valid_indices:
                return []

            # Compute similarities for valid documents
            filtered_embeddings = self.embeddings[valid_indices]
            similarities = self._cosine_similarity(query_embedding, filtered_embeddings)

            # Get top-k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            # Format results
            results = []
            for idx in top_indices:
                original_idx = valid_indices[idx]
                results.append({
                    'text': self.documents[original_idx],
                    'metadata': self.metadatas[original_idx],
                    'score': float(similarities[idx]),
                    'id': self.ids[original_idx]
                })

            logger.info(f"Query returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error querying vector store: {str(e)}", exc_info=True)
            raise

    async def delete(
        self,
        filter_metadata: Optional[Dict[str, Any]] = None,
        ids: Optional[List[str]] = None
    ) -> int:
        """
        Delete chunks from vector store

        Args:
            filter_metadata: Metadata filters
            ids: Specific IDs to delete

        Returns:
            Number of chunks deleted
        """
        try:
            indices_to_delete = []

            if ids:
                # Delete by IDs
                for i, doc_id in enumerate(self.ids):
                    if doc_id in ids:
                        indices_to_delete.append(i)
            elif filter_metadata:
                # Delete by metadata filter
                for i, metadata in enumerate(self.metadatas):
                    match = all(
                        metadata.get(k) == v
                        for k, v in filter_metadata.items()
                    )
                    if match:
                        indices_to_delete.append(i)
            else:
                # Delete all
                count = len(self.documents)
                self.documents = []
                self.embeddings = None
                self.metadatas = []
                self.ids = []
                self._save()
                return count

            # Delete indices
            if indices_to_delete:
                indices_to_keep = [i for i in range(len(self.documents)) if i not in indices_to_delete]

                self.documents = [self.documents[i] for i in indices_to_keep]
                self.metadatas = [self.metadatas[i] for i in indices_to_keep]
                self.ids = [self.ids[i] for i in indices_to_keep]

                if self.embeddings is not None and len(indices_to_keep) > 0:
                    self.embeddings = self.embeddings[indices_to_keep]
                elif len(indices_to_keep) == 0:
                    self.embeddings = None

                self._save()

            count = len(indices_to_delete)
            logger.info(f"Deleted {count} chunks from vector store")
            return count

        except Exception as e:
            logger.error(f"Error deleting chunks: {str(e)}", exc_info=True)
            raise

    async def count(self) -> int:
        """Get total number of chunks in store"""
        return len(self.documents)

    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            "total_chunks": len(self.documents),
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dim": self.embedding_dim,
            "storage_type": "in-memory (numpy)"
        }
