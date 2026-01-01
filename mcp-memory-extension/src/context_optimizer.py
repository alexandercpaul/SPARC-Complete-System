"""
Context Optimizer for MCP Memory Extension
Optimizes retrieved context to fit within token budgets
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ContextOptimizer:
    """Optimizes context chunks for token budget"""

    def __init__(self, chars_per_token: float = 4.0):
        """
        Initialize Context Optimizer

        Args:
            chars_per_token: Estimated characters per token (default: 4.0)
        """
        self.chars_per_token = chars_per_token
        logger.info(f"ContextOptimizer initialized (chars_per_token={chars_per_token})")

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return int(len(text) / self.chars_per_token)

    def optimize(
        self,
        chunks: List[Dict[str, Any]],
        max_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        Optimize chunks to fit within token budget

        Prioritizes:
        1. Higher relevance scores
        2. More recent content
        3. Diversity of sources

        Args:
            chunks: List of chunk dicts with 'text', 'score', 'metadata'
            max_tokens: Maximum token budget

        Returns:
            Optimized list of chunks that fit within budget
        """
        if not chunks:
            return []

        # Sort by relevance score (descending)
        sorted_chunks = sorted(chunks, key=lambda x: x.get('score', 0), reverse=True)

        # Select chunks that fit within budget
        selected = []
        total_tokens = 0

        for chunk in sorted_chunks:
            chunk_tokens = self.estimate_tokens(chunk['text'])

            if total_tokens + chunk_tokens <= max_tokens:
                selected.append(chunk)
                total_tokens += chunk_tokens
            else:
                # Try to fit a partial chunk if there's space
                remaining_tokens = max_tokens - total_tokens
                if remaining_tokens > 50:  # Only if meaningful space left
                    # Truncate chunk to fit
                    truncated_chars = int(remaining_tokens * self.chars_per_token)
                    truncated_text = chunk['text'][:truncated_chars] + "..."

                    truncated_chunk = {
                        **chunk,
                        'text': truncated_text,
                        'metadata': {
                            **chunk.get('metadata', {}),
                            'truncated': True
                        }
                    }
                    selected.append(truncated_chunk)
                    total_tokens = max_tokens

                break  # Budget exhausted

        logger.info(
            f"Optimized {len(chunks)} chunks to {len(selected)} chunks "
            f"({total_tokens}/{max_tokens} tokens)"
        )

        return selected

    def format_for_prompt(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format optimized chunks for inclusion in prompt

        Args:
            chunks: List of chunk dicts

        Returns:
            Formatted context string
        """
        if not chunks:
            return ""

        # Group by source type
        by_source = {}
        for chunk in chunks:
            source_type = chunk.get('metadata', {}).get('source_type', 'unknown')
            if source_type not in by_source:
                by_source[source_type] = []
            by_source[source_type].append(chunk)

        # Format sections
        sections = []

        for source_type, source_chunks in by_source.items():
            section_lines = [f"\n## {source_type.upper()} CONTEXT\n"]

            for i, chunk in enumerate(source_chunks, 1):
                metadata = chunk.get('metadata', {})
                source_name = metadata.get('source_name', 'unknown')
                timestamp = metadata.get('timestamp', 'unknown')
                score = chunk.get('score', 0)

                section_lines.append(
                    f"\n### [{i}] {source_name} (relevance: {score:.2f}, {timestamp})\n"
                )
                section_lines.append(chunk['text'])
                section_lines.append("\n")

            sections.append('\n'.join(section_lines))

        return '\n'.join(sections)
