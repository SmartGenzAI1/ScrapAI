import requests
from bs4 import BeautifulSoup
import hashlib
import re
from urllib.parse import urlparse
import time

class MinimalCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ScrapAI-Bot/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
    def can_fetch(self, url: str) -> bool:
        """Simple robots.txt check"""
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            response = self.session.get(robots_url, timeout=5)
            if response.status_code == 200:
                # Simple check - allow all for now
                return True
        except:
            pass
        return True
    
    def fetch_page(self, url: str) -> str:
        """Fetch page content"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
            
    def extract_content(self, html: str, url: str) -> dict:
        """Extract content from HTML"""
        if not html:
            return {'title': 'Failed', 'content': '', 'hash': ''}
            
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove scripts and styles
            for element in soup(['script', 'style']):
                element.decompose()
            
            # Get title
            title = soup.find('title')
            title_text = title.text.strip() if title else url
            
            # Try to find main content
            content_selectors = ['article', 'main', '.content', '.post-content']
            content_element = None
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
                    
            if not content_element:
                content_element = soup.find('body')
            
            # Extract text
            if content_element:
                text = content_element.get_text(separator='\n', strip=True)
                text = re.sub(r'\n\s*\n', '\n\n', text)
            else:
                text = ""
                
            # Clean text
            lines = [line for line in text.split('\n') if len(line.strip()) > 20]
            clean_text = '\n'.join(lines)
            
            return {
                'title': title_text,
                'content': clean_text,
                'hash': hashlib.sha256(clean_text.encode()).hexdigest() if clean_text else ''
            }
            
        except Exception as e:
            print(f"Error parsing {url}: {e}")
            return {'title': 'Error', 'content': '', 'hash': ''}
