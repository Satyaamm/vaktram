"""
Sentence-transformers embeddings for semantic search over transcripts.
"""

import logging
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "all-MiniLM-L6-v2"


class Embedder:
    """Generates text embeddings using sentence-transformers."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._model = None

    def initialize(self) -> None:
        """Load the sentence-transformers model."""
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", self.model_name)
        self._model = SentenceTransformer(self.model_name)
        logger.info("Embedding model loaded (dim=%d)", self._model.get_sentence_embedding_dimension())

    def embed(self, text: str) -> List[float]:
        """Generate an embedding vector for a single text string."""
        if self._model is None:
            raise RuntimeError("Embedder not initialized. Call initialize() first.")
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        if self._model is None:
            raise RuntimeError("Embedder not initialized. Call initialize() first.")
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        if self._model is None:
            raise RuntimeError("Embedder not initialized.")
        return self._model.get_sentence_embedding_dimension()
