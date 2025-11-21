from .memory_client import MemoryClient

class DatabaseClient:
    def __init__(self):
        self.client = MemoryClient()
        
    async def add_to_queue(self, url: str):
        return await self.client.add_to_queue(url)
        
    async def get_next_queue_item(self):
        return await self.client.get_next_queue_item()
        
    async def save_page(self, data: dict):
        return await self.client.save_page(data)
        
    async def is_duplicate(self, content_hash: str):
        return await self.client.is_duplicate(content_hash)
        
    async def mark_queue_processed(self, queue_id: str, status: str):
        return await self.client.mark_queue_processed(queue_id, status)
        
    async def search_content(self, query: str, limit: int = 10):
        return await self.client.search_content(query, limit)
        
    async def get_pages(self, skip: int = 0, limit: int = 50):
        return await self.client.get_pages(skip, limit)
        
    async def get_stats(self):
        return await self.client.get_stats()
