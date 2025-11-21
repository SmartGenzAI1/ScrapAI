import aiohttp
import asyncio
from bs4 import BeautifulSoup
import hashlib
import re
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from backend.config import config
import time

class LightweightCrawler:
    def __init__(self):
        self.robots_parsers = {}
        self.session = None
        self.request_times = {}
        
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': config.crawler.user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
        
    def can_fetch(self, url: str) -> bool:
        """Check robots.txt"""
        if not config.crawler.respect_robots:
            return True
            
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if domain not in self.robots_parsers:
            self.robots_parsers[domain] = RobotFileParser()
            robots_url = f"{parsed.scheme}://{domain}/robots.txt"
            try:
                self.robots_parsers[domain].set_url(robots_url)
                self.robots_parsers[domain].read()
            except:
                return True
                
        return self.robots_parsers[domain].can_fetch(config.crawler.user_agent, url)
    
    async def respect_delay(self, domain: str):
        """Respect crawl delay for domain"""
        if domain in self.request_times:
            last_time = self.request_times[domain]
            elapsed = time.time() - last_time
            if elapsed < config.crawler.request_delay:
                await asyncio.sleep(config.crawler.request_delay - elapsed)
        self.request_times[domain] = time.time()
    
    async def fetch_page(self, url: str) -> str:
        """Fetch page content without JavaScript"""
        session = await self.get_session()
        domain = urlparse(url).netloc
        
        # Respect crawl delay
        await self.respect_delay(domain)
        
        try:
            async with session.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    content = await response.text()
                    return content
                else:
                    print(f"HTTP {response.status} for {url}")
                    return ""
        except asyncio.TimeoutError:
            print(f"Timeout fetching {url}")
            return ""
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
            
    def extract_content(self, html: str, url: str) -> dict:
        """Extract clean content from HTML"""
        if not html:
            return {'title': 'Failed to fetch', 'content': '', 'content_hash': ''}
            
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
                element.decompose()
            
            # Try multiple content selectors
            content_selectors = [
                'article',
                'main',
                '[role="main"]',
                '.content',
                '.post-content', 
                '.entry-content',
                '.article-content',
                '.post-body',
                '.story-content',
                '.page-content'
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
                    
            if not content_element:
                # Fallback: use body but remove common noise
                content_element = soup.find('body')
                if content_element:
                    for noise in content_element.select('.sidebar, .menu, .comments, .advertisement'):
                        noise.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else url
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ''
            
            # Extract text content
            if content_element:
                text = content_element.get_text(separator='\n', strip=True)
                text = self.clean_text(text)
            else:
                text = ""
            
            # Combine title, description and content
            full_content = f"{title_text}\n{description}\n{text}"
            full_content = self.clean_text(full_content)
            
            return {
                'title': title_text,
                'content': full_content,
                'html': html,
                'content_hash': hashlib.sha256(full_content.encode()).hexdigest() if full_content else '',
                'word_count': len(full_content.split())
            }
            
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return {'title': 'Error', 'content': '', 'content_hash': ''}
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
            
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove very short lines (likely noise)
        lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 20]
        
        return '\n'.join(lines)
        
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
