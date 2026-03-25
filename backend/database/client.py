from .sql_client import SQLClient

class DatabaseClient:
    def __init__(self):
        self.client = SQLClient()
        # Create tables on initialization
        self.client.create_tables()
        
    async def add_to_queue(self, url: str):
        return await self.client.add_to_queue(url)
        
    async def get_next_queue_item(self):
        return await self.client.get_next_queue_item()
        
    async def save_page(self, data: dict):
        return await self.client.save_page(data)
        
    async def is_duplicate(self, content_hash: str):
        return await self.client.is_duplicate(content_hash)
        
    async def mark_queue_processed(self, queue_id: str, status: str):
        return await self.client.mark_queue_processed(int(queue_id), status)
        
    async def search_content(self, query: str, limit: int = 10):
        return await self.client.search_content(query, limit)
        
    async def get_pages(self, skip: int = 0, limit: int = 50):
        return await self.client.get_pages(skip, limit)
        
    async def get_stats(self):
        return await self.client.get_stats()
        
    # Additional methods for the enhanced functionality
    async def save_chunk(self, page_id: int, chunk_text: str, chunk_index: int) -> int:
        return await self.client.save_chunk(page_id, chunk_text, chunk_index)
        
    async def save_embedding(self, chunk_id: int, vector: list) -> int:
        return await self.client.save_embedding(chunk_id, vector)
        
    async def get_pages_without_embeddings(self, limit: int = 10) -> list:
        return await self.client.get_pages_without_embeddings(limit)
        
    async def mark_embedding_generated(self, page_id: int) -> bool:
        return await self.client.mark_embedding_generated(page_id)
        
    async def get_pages_needing_chunking(self, limit: int = 10) -> list:
        """Get pages that have content but no chunks"""
        return await self.client.get_pages_needing_chunking(limit)
        
    async def get_chunks_without_embeddings(self, limit: int = 10) -> list:
        """Get chunks that don't have embeddings yet"""
        return await self.client.get_chunks_without_embeddings(limit)
        
    async def mark_chunk_embedded(self, chunk_id: int) -> bool:
        """Mark chunk as having embeddings generated"""
        return await self.client.mark_chunk_embedded(chunk_id)
