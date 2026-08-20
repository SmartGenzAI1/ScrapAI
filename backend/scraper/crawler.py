import asyncio
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from .lightweight_crawler import LightweightCrawler
from backend.config import config
from backend.database.client import DatabaseClient

logger = logging.getLogger(__name__)


class SmartCrawler:
    """
    Unified High-Level Crawler Engine for ScrapAI.
    Coordinates URL crawling, content extraction, link discovery,
    and automatic database storage.
    """
    def __init__(self, db: Optional[DatabaseClient] = None):
        self.crawler = LightweightCrawler()
        self.db = db or DatabaseClient()

    def can_fetch(self, url: str) -> bool:
        return self.crawler.can_fetch(url)

    async def crawl_url(
        self,
        url: str,
        depth: int = 0,
        max_depth: int = 2,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Crawl a single URL, extract structured content, optionally save to database,
        and enqueue discovered child links if depth < max_depth.
        """
        logger.info(f"Crawling URL: {url} (depth {depth}/{max_depth})")
        fetch_res = await self.crawler.fetch_page(url)
        
        if fetch_res.get('status_code') != 200 or not fetch_res.get('html'):
            return {
                'success': False,
                'url': url,
                'status_code': fetch_res.get('status_code', 0),
                'error': fetch_res.get('error', 'Failed to retrieve page')
            }

        extracted = self.crawler.extract_content(fetch_res['html'], url)
        extracted['status_code'] = fetch_res['status_code']
        page_id = 0
        is_new = False

        if save_to_db and extracted.get('content_hash'):
            page_data = {
                'url': extracted['url'],
                'title': extracted['title'],
                'content': extracted['content'],
                'meta_description': extracted['meta_description'],
                'author': extracted['author'],
                'word_count': extracted['word_count'],
                'hash': extracted['content_hash'],
                'status_code': extracted['status_code']
            }
            page_id, is_new = await self.db.save_page(page_data)

        # Enqueue discovered links if recursive depth is allowed
        discovered_count = 0
        if depth < max_depth and extracted.get('links'):
            target_domain = urlparse(url).netloc
            for link in extracted['links'][:config.crawler.max_pages_per_domain]:
                link_domain = urlparse(link).netloc
                # Keep same domain or allowable scope
                if link_domain == target_domain:
                    added = await self.db.add_to_queue(
                        url=link,
                        priority=max(0, 5 - depth),
                        depth=depth + 1,
                        max_depth=max_depth,
                        parent_url=url
                    )
                    if added:
                        discovered_count += 1

        return {
            'success': True,
            'page_id': page_id,
            'is_new': is_new,
            'url': extracted['url'],
            'title': extracted['title'],
            'content': extracted['content'][:400],
            'word_count': extracted['word_count'],
            'hash': extracted['content_hash'],
            'links_found': len(extracted.get('links', [])),
            'links_queued': discovered_count
        }

    async def crawl_direct(self, url: str) -> Dict[str, Any]:
        """
        Immediately fetch and extract content for a URL.
        """
        return await self.crawl_url(url, depth=0, max_depth=0, save_to_db=True)

    async def discover_sitemap(self, domain_or_url: str) -> List[str]:
        """
        Discover and enqueue URLs from sitemap.xml
        """
        urls = await self.crawler.fetch_sitemap_urls(domain_or_url)
        queued = 0
        for u in urls:
            if await self.db.add_to_queue(u, priority=1, depth=0, max_depth=1):
                queued += 1
        return urls

    async def close(self):
        await self.crawler.close()
