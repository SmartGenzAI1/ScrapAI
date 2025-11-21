import asyncio
import time
from backend.scraper.minimal_crawler import MinimalCrawler
from backend.database.client import DatabaseClient
from backend.config import config

class CrawlerWorker:
    def __init__(self):
        self.crawler = MinimalCrawler()
        self.db = DatabaseClient()
        
    async def process_queue(self):
        print("🚀 Minimal crawler started...")
        
        while True:
            try:
                queue_item = await self.db.get_next_queue_item()
                if not queue_item:
                    await asyncio.sleep(10)
                    continue
                    
                url = queue_item['url']
                print(f"📡 Crawling: {url}")
                
                # Fetch content
                html = self.crawler.fetch_page(url)
                
                if not html:
                    await self.db.mark_queue_failed(queue_item['id'], "Failed to fetch")
                    continue
                    
                # Extract content
                content_data = self.crawler.extract_content(html, url)
                
                if not content_data.get('content'):
                    await self.db.mark_queue_failed(queue_item['id'], "No content")
                    continue
                    
                # Save page
                page_data = {
                    'url': url,
                    'title': content_data['title'],
                    'content': content_data['content'],
                    'hash': content_data['hash']
                }
                
                await self.db.save_page(page_data)
                await self.db.mark_queue_processed(queue_item['id'], "Success")
                
                print(f"✅ Saved: {url}")
                
                # Rate limit
                time.sleep(config.crawler.request_delay)
                
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    worker = CrawlerWorker()
    asyncio.run(worker.process_queue())
