import requests
from bs4 import BeautifulSoup
import hashlib
import re
from urllib.parse import urlparse
from typing import Dict, Any

class MinimalCrawler:
    def __init__(self, user_agent: str = "ScrapAI-Bot/2.0"):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
    def can_fetch(self, url: str) -> bool:
        """Simple robots check fallback"""
        return True
    
    def fetch_page(self, url: str) -> str:
        """Fetch page content synchronously"""
        try:
            response = self.session.get(url, timeout=12)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return ""
            
    def extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """Extract clean content from HTML"""
        if not html:
            return {'title': 'Failed', 'content': '', 'hash': '', 'url': url}
            
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove scripts and styles
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Get title
            title_tag = soup.find('title')
            title_text = title_tag.text.strip() if title_tag else url
            
            # Try to find main content
            content_element = soup.find('article') or soup.find('main') or soup.find('body')
            
            # Extract text
            if content_element:
                text = content_element.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)
            else:
                text = ""
                
            clean_text = f"{title_text}\n{text}".strip()
            content_hash = hashlib.sha256(clean_text.encode()).hexdigest() if clean_text else ''
            
            return {
                'url': url,
                'title': title_text,
                'content': clean_text,
                'hash': content_hash,
                'word_count': len(clean_text.split())
            }
        except Exception:
            return {'title': 'Error', 'content': '', 'hash': '', 'url': url}
