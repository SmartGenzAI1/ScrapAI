from typing import Optional, List, Dict, Any, Tuple
from .sql_client import SQLClient

class DatabaseClient:
    def __init__(self, database_url: Optional[str] = None):
        self.client = SQLClient(database_url=database_url)
        
    async def add_to_queue(
        self,
        url: str,
        priority: int = 0,
        depth: int = 0,
        max_depth: int = 2,
        parent_url: Optional[str] = None
    ) -> bool:
        return await self.client.add_to_queue(url, priority, depth, max_depth, parent_url)
        
    async def get_next_queue_item(self) -> Optional[Dict[str, Any]]:
        return await self.client.get_next_queue_item()
        
    async def mark_queue_processed(self, queue_id: int, status: str, error: Optional[str] = None) -> bool:
        return await self.client.mark_queue_processed(int(queue_id), status, error)

    async def get_queue_items(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        return await self.client.get_queue_items(status, limit)

    async def clear_queue(self) -> int:
        return await self.client.clear_queue()
        
    async def save_page(self, data: dict) -> Tuple[int, bool]:
        return await self.client.save_page(data)

    async def get_page_by_id(self, page_id: int) -> Optional[Dict[str, Any]]:
        return await self.client.get_page_by_id(page_id)

    async def delete_page(self, page_id: int) -> bool:
        return await self.client.delete_page(page_id)
        
    async def is_duplicate(self, content_hash: str) -> bool:
        return await self.client.is_duplicate(content_hash)
        
    async def search_content(self, query: str, limit: int = 10, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        return await self.client.search_content(query, limit, domain)

    async def query_and_answer(self, query: str, limit: int = 10) -> Dict[str, Any]:
        return await self.client.query_and_answer(query, limit)
        
    async def get_pages(self, skip: int = 0, limit: int = 50, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        return await self.client.get_pages(skip, limit, domain)
        
    async def get_stats(self) -> Dict[str, Any]:
        return await self.client.get_stats()

    async def get_domains(self) -> List[Dict[str, Any]]:
        return await self.client.get_domains()
        
    async def save_chunk(self, page_id: int, chunk_text: str, chunk_index: int, token_count: int = 0) -> int:
        return await self.client.save_chunk(page_id, chunk_text, chunk_index, token_count)
        
    async def save_embedding(self, chunk_id: int, vector: list, model_name: str = "local-tfidf-semantic") -> int:
        return await self.client.save_embedding(chunk_id, vector, model_name)
        
    async def get_pages_without_embeddings(self, limit: int = 10) -> List[Dict[str, Any]]:
        return await self.client.get_pages_without_embeddings(limit)
        
    async def mark_embedding_generated(self, page_id: int) -> bool:
        return await self.client.mark_embedding_generated(page_id)
        
    async def get_pages_needing_chunking(self, limit: int = 20) -> List[Dict[str, Any]]:
        return await self.client.get_pages_needing_chunking(limit)
        
    async def get_chunks_without_embeddings(self, limit: int = 50) -> List[Dict[str, Any]]:
        return await self.client.get_chunks_without_embeddings(limit)
        
    async def mark_chunk_embedded(self, chunk_id: int) -> bool:
        return await self.client.mark_chunk_embedded(chunk_id)

    async def reset_all(self) -> bool:
        return await self.client.reset_all()
