"""
FlashRank Local Cross-Encoder Re-Ranking Engine.
Provides ultra-low latency (~5-15ms) neural cross-attention re-ranking
running 100% locally via ONNX Runtime with zero external API dependencies.
"""

import os
import logging
import threading
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Check if FlashRank is available in the environment
HAS_FLASHRANK = False
try:
    from flashrank import Ranker, RerankRequest
    HAS_FLASHRANK = True
except ImportError:
    HAS_FLASHRANK = False


class FlashRankReranker:
    """
    High-performance local neural cross-encoder re-ranker using FlashRank and ONNX.
    Calculates deep cross-attention scores between query and document passages
    to re-order first-stage hybrid search candidates.
    """
    def __init__(
        self,
        model_name: str = "ms-marco-TinyBERT-L-2-v2",
        cache_dir: Optional[str] = None,
        score_weight: float = 0.70
    ):
        self.model_name = model_name
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), "..", "..", ".cache", "flashrank")
        self.score_weight = max(0.0, min(1.0, score_weight))
        self._ranker = None
        self._lock = threading.Lock()
        self._init_error = None

    def _ensure_model_loaded(self) -> bool:
        """Lazy load model on first usage with thread safety"""
        if not HAS_FLASHRANK:
            return False

        if self._ranker is not None:
            return True

        with self._lock:
            if self._ranker is not None:
                return True
            try:
                os.makedirs(self.cache_dir, exist_ok=True)
                self._ranker = Ranker(
                    model_name=self.model_name,
                    cache_dir=self.cache_dir
                )
                logger.info(f"FlashRank Ranker initialized successfully with model '{self.model_name}'")
                return True
            except Exception as e:
                self._init_error = str(e)
                logger.warning(f"Failed to initialize FlashRank model '{self.model_name}': {e}. Falling back to standard hybrid ranking.")
                return False

    def is_available(self) -> bool:
        """Check if FlashRank is installed and ready"""
        return HAS_FLASHRANK and self._ensure_model_loaded()

    def get_info(self) -> Dict[str, Any]:
        """Get information about the FlashRank engine"""
        return {
            "available": HAS_FLASHRANK,
            "loaded": self._ranker is not None,
            "model_name": self.model_name,
            "cache_dir": self.cache_dir,
            "score_weight": self.score_weight,
            "error": self._init_error
        }

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: Optional[int] = None,
        blend_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Re-rank a list of candidate documents/chunks against a search query.

        Args:
            query: The user's search query.
            candidates: List of candidate dicts containing text in 'chunk_text', 'content', 'snippet', or 'text'.
            top_n: Optional limit on the number of returned re-ranked items.
            blend_scores: If True, blends initial hybrid score (1 - score_weight) with FlashRank score (score_weight).
                          If False, sets score directly to FlashRank cross-encoder score.

        Returns:
            List of candidate dictionaries ordered by relevance, with 'flashrank_score' and updated 'score'.
        """
        if not candidates or not query or not query.strip():
            return candidates

        clean_query = query.strip()
        candidates_to_rerank = candidates[:top_n] if top_n else candidates

        if not self._ensure_model_loaded():
            logger.debug("FlashRank not available; returning candidates in original order.")
            return candidates_to_rerank

        try:
            # Build passage payloads for FlashRank
            passages = []
            for idx, item in enumerate(candidates_to_rerank):
                # Extract best available text representation
                text = (
                    item.get("chunk_text") or
                    item.get("content") or
                    item.get("snippet") or
                    item.get("text") or
                    item.get("title") or
                    ""
                )
                # Keep text bounded to avoid memory blowup on giant docs
                text_slice = text[:2000] if len(text) > 2000 else text
                passages.append({
                    "id": idx,
                    "text": text_slice
                })

            req = RerankRequest(query=clean_query, passages=passages)
            flashrank_results = self._ranker.rerank(req)

            # Map FlashRank scores back to candidate dicts
            reranked_items = []
            for res in flashrank_results:
                original_idx = res["id"]
                orig_item = dict(candidates_to_rerank[original_idx])
                fr_score = float(res.get("score", 0.0))

                # Normalize score to float precision [0.0, 1.0]
                fr_score_clean = round(max(0.0, min(1.0, fr_score)), 4)
                orig_item["flashrank_score"] = fr_score_clean

                initial_score = float(orig_item.get("score", 0.5))
                if blend_scores:
                    blended = (1.0 - self.score_weight) * initial_score + self.score_weight * fr_score_clean
                    orig_item["score"] = round(blended, 4)
                else:
                    orig_item["score"] = fr_score_clean

                orig_item["reranked"] = True
                reranked_items.append(orig_item)

            # Sort by new composite/FlashRank score descending
            reranked_items.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            return reranked_items

        except Exception as e:
            logger.error(f"Error during FlashRank re-ranking: {e}. Reverting to original order.", exc_info=True)
            return candidates_to_rerank


# Global singleton instance
_reranker_instance = None
_reranker_lock = threading.Lock()


def get_reranker(
    model_name: Optional[str] = None,
    cache_dir: Optional[str] = None,
    score_weight: Optional[float] = None
) -> FlashRankReranker:
    """Get or initialize global FlashRank reranker instance"""
    global _reranker_instance
    if _reranker_instance is None:
        with _reranker_lock:
            if _reranker_instance is None:
                _reranker_instance = FlashRankReranker(
                    model_name=model_name or "ms-marco-TinyBERT-L-2-v2",
                    cache_dir=cache_dir,
                    score_weight=score_weight if score_weight is not None else 0.70
                )
    return _reranker_instance
