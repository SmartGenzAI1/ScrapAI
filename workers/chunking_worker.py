"""
Chunking Worker for ScrapAI.
Monitors newly stored pages and slices text into sentence-bounded chunks for embedding.
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
from backend.utils.chunker import TextChunker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (ChunkingWorker) %(message)s'
)
logger = logging.getLogger(__name__)


class ChunkingWorker:
    def __init__(self, db: Optional[DatabaseClient] = None):
        self.db = db or DatabaseClient()
        self.chunker = TextChunker(
            chunk_size=config.chunking.chunk_size,
            overlap=config.chunking.overlap
        )
        self.running = True

    def stop(self):
        self.running = False

    async def run_once(self) -> int:
        """Process one batch of pages needing chunking. Returns count of chunks created."""
        pages = await self.db.get_pages_needing_chunking(limit=config.chunking.batch_size)
        if not pages:
            return 0

        total_chunks = 0
        for page in pages:
            page_id = page['id']
            content = page.get('content', '').strip()
            if not content:
                continue

            try:
                if config.chunking.method == "fixed":
                    chunks = self.chunker.chunk_by_fixed_size(content)
                else:
                    chunks = self.chunker.chunk_by_sentences(content)

                if not chunks:
                    # If content is short, create a single chunk
                    chunks = [self.chunker.chunk_by_sentences(content + ".")[0]] if content else []

                for i, chunk in enumerate(chunks):
                    chunk_id = await self.db.save_chunk(
                        page_id=page_id,
                        chunk_text=chunk.text,
                        chunk_index=i,
                        token_count=len(chunk.text.split())
                    )
                    if chunk_id:
                        total_chunks += 1

                logger.info(f"✂️ Chunked page {page_id} ({page.get('url', '')}) -> {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"❌ Error chunking page {page_id}: {e}", exc_info=True)

        return total_chunks

    async def run_loop(self, poll_interval: float = 4.0):
        logger.info("✂️ Chunking Worker started. Monitoring pages...")
        while self.running:
            try:
                count = await self.run_once()
                if count == 0:
                    await asyncio.sleep(poll_interval)
                else:
                    await asyncio.sleep(1.0)
            except Exception as e:
                logger.error(f"Chunking Worker loop error: {e}")
                await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    worker = ChunkingWorker()

    def sig_handler(sig, frame):
        logger.info("Stopping Chunking Worker...")
        worker.stop()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    try:
        asyncio.run(worker.run_loop())
    except KeyboardInterrupt:
        pass