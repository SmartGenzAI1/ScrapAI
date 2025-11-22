import requests
import time
import hashlib
from bs4 import BeautifulSoup
import re

class SimpleCrawler:
    def __init__(self, api_url):
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ScrapAI-Bot/1.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
    
    def fetch_page(self, url):
        try:
            response = self.session.get(url, timeout=10)
            return response.text
        except:
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
            lines = [line.strip() for line in text.split('.') if len(line.strip()) > 20]
            clean_text = '. '.join(lines)
            
            return {
                'title': title_text,
                'content': clean_text,
                'hash': hashlib.sha256(clean_text.encode()).hexdigest() if clean_text else ''
            }
        except:
            return {'title': '', 'content': '', 'hash': ''}
    
    def process_queue(self):
        print("🕷️ Crawler worker started...")
        
        while True:
            try:
                # Check if there are URLs to process
                stats_response = requests.get(f"{self.api_url}/api/v1/stats")
                stats = stats_response.json()
                
                if stats.get('queued', 0) > 0:
                    print(f"📥 Found {stats['queued']} URLs in queue")
                    
                    # For now, let's just crawl a test URL directly
                    test_url = "https://httpbin.org/html"
                    print(f"🔗 Crawling: {test_url}")
                    
                    html = self.fetch_page(test_url)
                    if html:
                        content = self.extract_content(html, test_url)
                        
                        if content['content']:
                            # Add the page directly
                            page_data = {
                                'url': test_url,
                                'title': content['title'],
                                'content': content['content'],
                                'hash': content['hash']
                            }
                            
                            # We need to add this page to the storage
                            # For now, let's use the add-test-page endpoint
                            response = requests.post(f"{self.api_url}/api/v1/add-page", json=page_data)
                            print(f"✅ Added page: {content['title']}")
                    
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"❌ Worker error: {e}")
                time.sleep(30)

if __name__ == "__main__":
    API_URL = "https://scrapai-2.onrender.com"  # Your API URL
    crawler = SimpleCrawler(API_URL)
    crawler.process_queue()
