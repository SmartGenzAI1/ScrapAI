from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="ScrapAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add this Pydantic model for request validation
class CrawlRequest(BaseModel):
    urls: List[str]

# Simple in-memory storage
queue = []
pages = []

@app.get("/")
async def root():
    return {"message": "ScrapAI API Running", "status": "online"}

# FIXED: Use the Pydantic model
@app.post("/api/v1/crawl")
async def crawl_urls(request: CrawlRequest):
    """Add URLs to crawl queue"""
    for url in request.urls:  # Now using request.urls
        if url not in [item["url"] for item in queue]:
            queue.append({"url": url, "status": "queued"})
    return {"message": f"Added {len(request.urls)} URLs to queue", "queued": len(queue)}

@app.get("/api/v1/stats")
async def get_stats():
    """Get basic stats"""
    return {
        "queued": len([item for item in queue if item["status"] == "queued"]),
        "pages": len(pages),
        "total": len(queue)
    }

@app.get("/api/v1/search")
async def search_content(q: str = ""):
    """Simple search"""
    results = []
    for page in pages:
        if q.lower() in page.get("content", "").lower():
            results.append(page)
    return results

# ADD THIS: Simple endpoint to add a single page for testing
@app.post("/api/v1/add-test-page")
async def add_test_page():
    """Add a test page to see if search works"""
    test_page = {
        "url": "https://example.com",
        "title": "Example Domain",
        "content": "This domain is for use in illustrative examples in documents.",
        "hash": "test123"
    }
    pages.append(test_page)
    return {"message": "Test page added", "page": test_page}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# Add this endpoint to your existing main.py
@app.post("/api/v1/add-page")
async def add_page(page_data: dict):
    """Add a page directly (for testing)"""
    pages.append(page_data)
    return {"message": "Page added directly", "page": page_data}

@app.get("/api/v1/test-crawl")
async def test_crawl(url: str = "https://httpbin.org/html"):
    """Test crawling a URL directly"""
    import requests
    from bs4 import BeautifulSoup
    import hashlib
    import re
    
    try:
        # Fetch the page
        response = requests.get(url, timeout=10)
        html = response.text
        
        # Extract content
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        
        title = soup.find('title')
        title_text = title.text.strip() if title else url
        
        body = soup.find('body')
        text = body.get_text() if body else ""
        text = re.sub(r'\s+', ' ', text)
        
        page_data = {
            'url': url,
            'title': title_text,
            'content': text[:500],  # First 500 chars
            'hash': hashlib.sha256(text.encode()).hexdigest()
        }
        
        pages.append(page_data)
        return {"message": "Test crawl successful", "page": page_data}
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/v1/test-crawl-direct")
async def test_crawl_direct(url: str = "https://httpbin.org/html"):
    """Test crawling directly - TEMPORARY"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import hashlib
        
        response = requests.get(url, timeout=10)
        html = response.text
        
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        
        title = soup.find('title')
        title_text = title.text.strip() if title else "No Title"
        
        # Get meaningful content
        body = soup.find('body')
        if body:
            # Try to find article content
            article = body.find('article') or body.find('main') or body
            text = article.get_text(separator=' ', strip=True)
        else:
            text = "No content found"
        
        # Clean text
        import re
        text = re.sub(r'\s+', ' ', text)
        
        page_data = {
            'url': url,
            'title': title_text,
            'content': text[:1000],  # First 1000 chars
            'hash': hashlib.sha256(text.encode()).hexdigest()
        }
        
        pages.append(page_data)
        return {"success": True, "page": page_data}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
