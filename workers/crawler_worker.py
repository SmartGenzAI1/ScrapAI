import asyncio
import time
from backend.scraper.crawler import SmartCrawler
from backend.database.client import DatabaseClient
from backend.config import config

class CrawlerWorker:
    def __init__(self):
        self.crawler = SmartCrawler()
        self.db = DatabaseClient()
        
    async def process_queue(self):
        """Simple queue processor"""
        print("🕷️ Crawler worker started...")
        
        while True:
            try:
                # Get next URL from queue
                queue_item = await self.db.get_next_queue_item()
                if not queue_item:
                    print("⏳ No URLs in queue, waiting...")
                    await asyncio.sleep(10)
                    continue
                    
                url = queue_item['url']
                print(f"🔗 Processing: {url}")
                
                # Check robots.txt
                if not self.crawler.can_fetch(url):
                    print(f"🚫 Blocked by robots.txt: {url}")
                    await self.db.mark_queue_failed(queue_item['id'], "Blocked by robots.txt")
                    continue
                    
                # Fetch content
                html = await self.crawler.render_js_page(url)
                
                if not html:
                    print(f"❌ Failed to fetch: {url}")
                    await self.db.mark_queue_failed(queue_item['id'], "Failed to fetch content")
                    continue
                    
                # Extract content
                content_data = self.crawler.extract_content(html, url)
                
                # Skip if no meaningful content
                if not content_data.get('content') or len(content_data['content'].split()) < 10:
                    print(f"📄 No meaningful content: {url}")
                    await self.db.mark_queue_failed(queue_item['id'], "No meaningful content")
                    continue
                
                # Check for duplicates
                if await self.db.is_duplicate(content_data['content_hash']):
                    print(f"♻️ Duplicate content: {url}")
                    await self.db.mark_queue_processed(queue_item['id'], "Duplicate")
                    continue
                    
                # Save to database
                page_data = {
                    'url': url,
                    'title': content_data['title'],
                    'content': content_data['content'],
                    'content_hash': content_data['content_hash']
                }
                
                page_id = await self.db.save_page(page_data)
                await self.db.mark_queue_processed(queue_item['id'], "Success")
                
                print(f"✅ Successfully scraped: {url} ({len(content_data['content'])} chars)")
                
                # Be polite - rate limiting
                await asyncio.sleep(config.crawler.request_delay)
                
            except Exception as e:
                print(f"💥 Worker error: {str(e)}")
                await asyncio.sleep(30)

if __name__ == "__main__":
    worker = CrawlerWorker()
    asyncio.run(worker.process_queue())
