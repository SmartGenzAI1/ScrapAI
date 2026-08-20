"""
Unified Pipeline Manager for ScrapAI.
Coordinates Crawler, Chunking, and Embedding workers in a single background process.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.database.client import DatabaseClient
from workers.crawler_worker import CrawlerWorker
from workers.chunking_worker import ChunkingWorker
from workers.embedding_worker import EmbeddingWorker

logger = logging.getLogger(__name__)


class PipelineManager:
    def __init__(self, db: Optional[DatabaseClient] = None):
        self.db = db or DatabaseClient()
        self.crawler_worker = CrawlerWorker(db=self.db)
        self.chunking_worker = ChunkingWorker(db=self.db)
        self.embedding_worker = EmbeddingWorker(db=self.db)
        self.running = True

    def stop(self):
        self.running = False
        self.crawler_worker.stop()
        self.chunking_worker.stop()
        self.embedding_worker.stop()

    async def step_pipeline(self) -> dict:
        """Run one iteration of each worker in the pipeline sequentially or concurrently"""
        crawled = await self.crawler_worker.run_once()
        chunked = await self.chunking_worker.run_once()
        embedded = await self.embedding_worker.run_once()
        return {
            'crawled': crawled,
            'chunked': chunked,
            'embedded': embedded
        }

    async def run_pipeline_loop(self, poll_interval: float = 3.0):
        logger.info("🚀 ScrapAI Unified Pipeline Manager Active.")
        while self.running:
            try:
                activity = await self.step_pipeline()
                if activity['crawled'] == 0 and activity['chunked'] == 0 and activity['embedded'] == 0:
                    await asyncio.sleep(poll_interval)
                else:
                    await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Pipeline loop error: {e}")
                await asyncio.sleep(poll_interval)


# Global supervisor instance
pipeline_manager = PipelineManager()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(pipeline_manager.run_pipeline_loop())
