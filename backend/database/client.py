import os
from supabase import create_client
from backend.database.models import ScrapedPage, CrawlQueue
from backend.config import config

class DatabaseClient:
    def __init__(self):
        self.client = create_client(config.database.url, config.database.key)
        
    async def add_to_queue(self, url: str):
        return self.client.table('crawl_queue').insert({'url': url}).execute()
        
    async def get_next_queue_item(self):
        result = self.client.table('crawl_queue')\
            .select('*')\
            .eq('status', 'queued')\
            .order('scheduled_at')\
            .limit(1)\
            .execute()
        return result.data[0] if result.data else None
        
    async def save_page(self, data: dict):
        return self.client.table('scraped_pages').insert(data).execute()
        
    async def is_duplicate(self, content_hash: str):
        result = self.client.table('scraped_pages')\
            .select('id')\
            .eq('content_hash', content_hash)\
            .execute()
        return len(result.data) > 0
        
    async def mark_queue_processed(self, queue_id: str, status: str):
        return self.client.table('crawl_queue')\
            .update({'status': status})\
            .eq('id', queue_id)\
            .execute()
        # backend/database/client.py - MISSING
class DatabaseClient:
    async def add_to_queue(self, url): pass
    async def get_next_queue_item(self): pass
    async def save_page(self, data): pass
    async def search_content(self, query): pass
    # All database operations are undefined
