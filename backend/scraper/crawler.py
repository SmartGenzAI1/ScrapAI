from .lightweight_crawler import LightweightCrawler
from backend.config import config
from backend.database.client import DatabaseClient

class SmartCrawler:
    def __init__(self):
        self.crawler = LightweightCrawler()
        self.db = DatabaseClient()
        
    def can_fetch(self, url: str) -> bool:
        return self.crawler.can_fetch(url)
    
    async def render_js_page(self, url: str) -> str:
        """Use simple fetch - no JavaScript rendering"""
        return await self.crawler.fetch_page(url)
            
    def extract_content(self, html: str, url: str) -> dict:
        return self.crawler.extract_content(html, url)
        
    async def close(self):
        await self.crawler.close()
