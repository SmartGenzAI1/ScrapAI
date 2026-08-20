"""
Embedding Worker for ScrapAI.
Generates dense vector representations for unindexed chunks using LocalSemanticEngine.
Zero external API key dependencies required.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.config import config
from backend.database.client import DatabaseClient
from backend.search.semantic_engine import semantic_engine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (EmbeddingWorker) %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingWorker:
    def __init__(self, db: Optional[DatabaseClient] = None):
        self.db = db or DatabaseClient()
        self.engine = semantic_engine
        self.running = True

    def stop(self):
        self.running = False

    async def run_once(self) -> int:
        """Process one batch of chunks needing vector embeddings. Returns count generated."""
        chunks = await self.db.get_chunks_without_embeddings(limit=config.embedding.batch_size)
        if not chunks:
            return 0

        texts = [c['chunk_text'] for c in chunks if c.get('chunk_text')]
        if not texts:
            return 0

        try:
            # Generate embeddings via LocalSemanticEngine (zero-API local or optional neural model)
            vectors = self.engine.encode(texts)
            model_name = "sentence-transformers" if self.engine.neural_model else "local-tfidf-semantic"

            saved_count = 0
            for i, chunk in enumerate(chunks):
                if i < len(vectors):
                    emb_id = await self.db.save_embedding(
                        chunk_id=chunk['id'],
                        vector=vectors[i],
                        model_name=model_name
                    )
                    if emb_id:
                        saved_count += 1

            # Mark associated parent pages as embedded if all their chunks are processed
            seen_page_ids = set(c['page_id'] for c in chunks)
            for pid in seen_page_ids:
                await self.db.mark_embedding_generated(pid)

            logger.info(f"🧠 Generated & indexed {saved_count} vector embeddings (Model: {model_name})")
            return saved_count
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {e}", exc_info=True)
            return 0

    async def run_loop(self, poll_interval: float = 4.0):
        logger.info("🧠 Embedding Worker started. Indexing vector representations...")
        while self.running:
            try:
                count = await self.run_once()
                if count == 0:
                    await asyncio.sleep(poll_interval)
                else:
                    await asyncio.sleep(1.0)
            except Exception as e:
                logger.error(f"Embedding Worker loop error: {e}")
                await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    worker = EmbeddingWorker()

    def sig_handler(sig, frame):
        logger.info("Stopping Embedding Worker...")
        worker.stop()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    try:
        asyncio.run(worker.run_loop())
    except KeyboardInterrupt:
        pass
