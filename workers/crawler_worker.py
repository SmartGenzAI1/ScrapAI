import requests
import time
import hashlib
from bs4 import BeautifulSoup
import re

API_URL = "https://scrapai-2.onrender.com"

class SimpleCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ScrapAI-Bot/1.0)',
        })
    
    def fetch_page(self, url):
        try:
            response = self.session.get(url, timeout=10)
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
    
    def extract_content(self, html, url):
        if not html:
            return {'title': '', 'content': '', 'hash': ''}
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove scripts
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get title
            title = soup.find('title')
            title_text = title.text.strip() if title else url
            
            # Get body content
            body = soup.find('body')
            text = body.get_text() if body else ""
            
            # Clean text
            text = re.sub(r'\s+', ' ', text)
            lines = [line.strip() for line in text.split('.') if len(line.strip()) > 10]
            clean_text = '. '.join(lines)
            
            return {
                'title': title_text,
                'content': clean_text,
                'hash': hashlib.sha256(clean_text.encode()).hexdigest() if clean_text else ''
            }
        except Exception as e:
            print(f"Error extracting content: {e}")
            return {'title': '', 'content': '', 'hash': ''}

def process_queue():
    print("🕷️ Crawler worker started...")
    crawler = SimpleCrawler()
    
    while True:
        try:
            # Get stats to see if there are URLs to process
            stats_response = requests.get(f"{API_URL}/api/v1/stats")
            stats = stats_response.json()
            
            print(f"📊 Current stats: {stats}")
            
            # For now, let's test with a hardcoded URL
            test_urls = [
                "https://httpbin.org/html",
                "https://example.com",
                "https://httpbin.org/json"
            ]
            
            for url in test_urls:
                print(f"🔗 Testing crawl: {url}")
                
                html = crawler.fetch_page(url)
                if html:
                    content = crawler.extract_content(html, url)
                    
                    if content['content']:
                        # Add the page directly using your API
                        page_data = {
                            'url': url,
                            'title': content['title'],
                            'content': content['content'],
                            'hash': content['hash']
                        }
                        
                        # Try to add via API
                        try:
                            response = requests.post(f"{API_URL}/api/v1/crawl", 
                                                   json={"urls": [url]})
                            print(f"✅ Queued: {url} - {response.status_code}")
                            
                            # Also add the page content directly for testing
                            add_response = requests.post(f"{API_URL}/api/v1/add-test-page")
                            print(f"✅ Added test page: {add_response.status_code}")
                            
                        except Exception as e:
                            print(f"❌ API Error: {e}")
            
            time.sleep(30)  # Wait 30 seconds between checks
                
        except Exception as e:
            print(f"❌ Worker error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    process_queue()
