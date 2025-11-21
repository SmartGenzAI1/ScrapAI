import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import hashlib

class MemoryClient:
    def __init__(self):
        self.crawl_queue = []
        self.scraped_pages = []
        self.embeddings = []
        self.queue_processed = 0
        
    async def add_to_queue(self, url: str):
        """Add URL to in-memory queue"""
        if url not in [item['url'] for item in self.crawl_queue]:
            self.crawl_queue.append({
                'id': len(self.crawl_queue) + 1,
                'url': url,
                'domain': self._extract_domain(url),
                'status': 'queued',
                'scheduled_at': datetime.now()
            })
            return True
        return False
        
    async def get_next_queue_item(self):
        """Get next URL from queue"""
        for item in self.crawl_queue:
            if item['status'] == 'queued':
                item['status'] = 'processing'
                return item
        return None
        
    async def save_page(self, data: dict):
        """Save scraped page to memory"""
        page_id = len(self.scraped_pages) + 1
        page_data = {
            'id': page_id,
            'url': data['url'],
            'title': data.get('title', ''),
            'content': data.get('content', ''),
            'content_hash': data.get('content_hash', ''),
            'crawl_time': datetime.now()
        }
        self.scraped_pages.append(page_data)
        return page_id
        
    async def is_duplicate(self, content_hash: str):
        """Check for duplicate content"""
        return any(page['content_hash'] == content_hash for page in self.scraped_pages)
        
    async def mark_queue_processed(self, queue_id: str, status: str):
        """Update queue status"""
        for item in self.crawl_queue:
            if str(item['id']) == str(queue_id):
                item['status'] = status
                self.queue_processed += 1
                break
        
    async def search_content(self, query: str, limit: int = 10):
        """Simple in-memory search"""
        results = []
        for page in self.scraped_pages:
            if (query.lower() in page.get('title', '').lower() or 
                query.lower() in page.get('content', '').lower()):
                results.append(page)
            if len(results) >= limit:
                break
        return results
        
    async def get_pages(self, skip: int = 0, limit: int = 50):
        """Get paginated pages"""
        return self.scraped_pages[skip:skip + limit]
        
    async def get_stats(self):
        """Get basic stats"""
        return {
            'queued_urls': len([item for item in self.crawl_queue if item['status'] == 'queued']),
            'processed_urls': self.queue_processed,
            'scraped_pages': len(self.scraped_pages),
            'total_urls': len(self.crawl_queue)
        }
        
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        return urlparse(url).netloc
