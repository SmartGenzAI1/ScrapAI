"""
Autonomous Crawler Worker for ScrapAI.
Pulls tasks from the crawl queue, executes scraping & link discovery,
and stores clean pages into the database.
"""

import asyncio
import logging
import os
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
from backend.scraper.crawler import SmartCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (CrawlerWorker) %(message)s'
)
logger = logging.getLogger(__name__)


class CrawlerWorker:
    def __init__(self, db: Optional[DatabaseClient] = None):
        self.db = db or DatabaseClient()
        self.crawler = SmartCrawler(db=self.db)
        self.running = True

    def stop(self):
        self.running = False

    async def run_once(self) -> int:
        """Process one pending queue item. Returns 1 if processed, 0 if idle."""
        item = await self.db.get_next_queue_item()
        if not item:
            return 0

        queue_id = item['id']
        url = item['url']
        depth = item.get('depth', 0)
        max_depth = item.get('max_depth', config.crawler.max_depth)

        logger.info(f"🕷️ Processing target: {url} (ID: {queue_id}, Depth: {depth}/{max_depth})")

        try:
            result = await self.crawler.crawl_url(
                url=url,
                depth=depth,
                max_depth=max_depth,
                save_to_db=True
            )

            if result.get('success'):
                await self.db.mark_queue_processed(queue_id, status='completed')
                logger.info(f"✅ Crawled & Saved: {url} | Words: {result.get('word_count')} | Discovered: {result.get('links_queued')} links")
                return 1
            else:
                err = result.get('error', 'Crawl failed')
                await self.db.mark_queue_processed(queue_id, status='failed', error=err)
                logger.warning(f"❌ Failed: {url} | Error: {err}")
                return 1
        except Exception as e:
            logger.error(f"❌ Exception crawling {url}: {e}", exc_info=True)
            await self.db.mark_queue_processed(queue_id, status='failed', error=str(e))
            return 1

    async def run_loop(self, poll_interval: float = 3.0):
        logger.info("🕷️ Crawler Worker started. Polling queue...")
        try:
            while self.running:
                processed = await self.run_once()
                if processed == 0:
                    await asyncio.sleep(poll_interval)
                else:
                    # Brief politeness delay between queue items
                    await asyncio.sleep(config.crawler.request_delay)
        finally:
            await self.crawler.close()
            logger.info("Crawler Worker shut down.")


if __name__ == "__main__":
    worker = CrawlerWorker()

    def sig_handler(sig, frame):
        logger.info("Received exit signal...")
        worker.stop()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    try:
        asyncio.run(worker.run_loop())
    except KeyboardInterrupt:
        pass
