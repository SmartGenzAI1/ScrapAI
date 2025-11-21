import scrapy
from scrapy.crawler import CrawlerProcess
from playwright.async_api import async_playwright
import asyncio
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import hashlib
from backend.config import config
from backend.database.client import DatabaseClient

class SmartCrawler:
    def __init__(self):
        self.db = DatabaseClient()
        self.robots_parsers = {}
        
    def can_fetch(self, url: str) -> bool:
        if not config.crawler.respect_robots:
            return True
            
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain not in self.robots_parsers:
            self.robots_parsers[domain] = RobotFileParser()
            self.robots_parsers[domain].set_url(f"{domain}/robots.txt")
            try:
                self.robots_parsers[domain].read()
            except:
                return True
                
        return self.robots_parsers[domain].can_fetch(config.crawler.user_agent, url)
    
    async def render_js_page(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=config.crawler.js_timeout)
            content = await page.content()
            await browser.close()
            return content
            
    def extract_content(self, html: str, url: str) -> dict:
        # Use readability-like extraction
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Try to find main content
        content_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.content',
            '.post-content',
            '.entry-content'
        ]
        
        content_element = None
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                break
                
        if not content_element:
            content_element = soup.find('body')
            
        # Extract text
        text = content_element.get_text(separator='\n', strip=True)
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize whitespace
        
        # Extract metadata
        title = soup.find('title')
        title = title.get_text() if title else url
        
        return {
            'title': title,
            'content': text,
            'html': html,
            'content_hash': hashlib.sha256(text.encode()).hexdigest()
        }
