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
        """Process URLs from crawl queue"""
        while True:
            try:
                # Get next URL from queue
                queue_item = await self.db.get_next_queue_item()
                if not queue_item:
                    await asyncio.sleep(10)
                    continue
                    
                url = queue_item['url']
                
                # Check robots.txt
                if not self.crawler.can_fetch(url):
                    await self.db.mark_queue_failed(queue_item['id'], "Blocked by robots.txt")
                    continue
                    
                # Fetch content
                try:
                    # Try direct fetch first, use JS rendering if needed
                    html = await self.crawler.render_js_page(url)
                    content_data = self.crawler.extract_content(html, url)
                    
                    # Check for duplicates
                    if await self.db.is_duplicate(content_data['content_hash']):
                        await self.db.mark_queue_processed(queue_item['id'], "Duplicate")
                        continue
                        
                    # Save to database
                    page_data = {
                        'url': url,
                        'title': content_data['title'],
                        'content': content_data['content'],
                        'content_hash': content_data['content_hash'],
                        'raw_html_path': f"html/{content_data['content_hash']}.html"
                    }
                    
                    page_id = await self.db.save_page(page_data)
                    await self.db.mark_queue_processed(queue_item['id'], "Success")
                    
                    print(f"Successfully crawled: {url}")
                    
                except Exception as e:
                    await self.db.mark_queue_failed(queue_item['id'], str(e))
                    print(f"Error crawling {url}: {str(e)}")
                    
                # Rate limiting
                await asyncio.sleep(config.crawler.request_delay)
                
            except Exception as e:
                print(f"Worker error: {str(e)}")
                await asyncio.sleep(30)

if __name__ == "__main__":
    worker = CrawlerWorker()
    asyncio.run(worker.process_queue())
