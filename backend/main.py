from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio

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

# Import database client
from backend.database.client import DatabaseClient
db_client = DatabaseClient()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve a simple frontend interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ScrapAI - Web Crawling & Semantic Search</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; }
            .section { margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input[type="text"], input[type="url"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            button { background-color: #3498db; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            button:hover { background-color: #2980b9; }
            button:disabled { background-color: #95a5a6; cursor: not-allowed; }
            .result { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #3498db; }
            .stats { display: flex; justify-content: space-around; text-align: center; margin: 20px 0; }
            .stat-item { flex: 1; }
            .stat-number { font-size: 2em; font-weight: bold; color: #2c3e50; }
            .stat-label { color: #7f8c8d; text-transform: uppercase; font-size: 0.9em; }
            #results-container { margin-top: 20px; }
            .loading { display: none; text-align: center; padding: 20px; color: #7f8c8d; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🕷️ ScrapAI</h1>
            <p style="text-align: center; color: #7f8c8d;">AI-Powered Distributed Web Crawling, Scraping, Embedding & Semantic Search Platform</p>
            
            <div class="stats" id="stats-container">
                <div class="stat-item">
                    <div class="stat-number" id="pages-count">0</div>
                    <div class="stat-label">Pages Indexed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="queue-count">0</div>
                    <div class="stat-label">In Queue</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="chunks-count">0</div>
                    <div class="stat-label">Text Chunks</div>
                </div>
            </div>
            
            <div class="section">
                <h2>🌐 Crawl a Website</h2>
                <div class="form-group">
                    <label for="url-input">Enter URL to crawl:</label>
                    <input type="url" id="url-input" placeholder="https://example.com" />
                </div>
                <button id="crawl-btn">Add to Crawl Queue</button>
                <div id="crawl-result" class="result" style="display: none;"></div>
                <div id="crawl-loading" class="loading">Adding to queue...</div>
            </div>
            
            <div class="section">
                <h2>🔍 Search Content</h2>
                <div class="form-group">
                    <label for="search-input">Search for content:</label>
                    <input type="text" id="search-input" placeholder="Enter search terms..." />
                </div>
                <button id="search-btn">Search</button>
                <div id="search-result" class="result" style="display: none;"></div>
                <div id="search-loading" class="loading">Searching...</div>
                <div id="results-container"></div>
            </div>
            
            <div class="section">
                <h2>⚡ Quick Actions</h2>
                <button id="test-page-btn">Add Test Page</button>
                <button id="refresh-stats-btn">Refresh Statistics</button>
                <div id="quick-result" class="result" style="display: none;"></div>
            </div>
        </div>

        <script>
            // Update statistics
            async function updateStats() {
                try {
                    const response = await fetch('/api/v1/stats');
                    const stats = await response.json();
                    document.getElementById('pages-count').textContent = stats.pages || 0;
                    document.getElementById('queue-count').textContent = stats.queued || 0;
                    document.getElementById('chunks-count').textContent = stats.chunks || 0;
                } catch (error) {
                    console.error('Error fetching stats:', error);
                }
            }
            
            // Crawl URL
            document.getElementById('crawl-btn').addEventListener('click', async () => {
                const urlInput = document.getElementById('url-input');
                const url = urlInput.value.trim();
                
                if (!url) {
                    alert('Please enter a URL');
                    return;
                }
                
                const crawlBtn = document.getElementById('crawl-btn');
                const crawlResult = document.getElementById('crawl-result');
                const crawlLoading = document.getElementById('crawl-loading');
                
                crawlBtn.disabled = true;
                crawlLoading.style.display = 'block';
                crawlResult.style.display = 'none';
                
                try {
                    const response = await fetch('/api/v1/crawl', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ urls: [url] })
                    });
                    
                    const result = await response.json();
                    crawlResult.textContent = result.message || 'URL added to queue';
                    crawlResult.style.display = 'block';
                    urlInput.value = '';
                    
                    // Update stats after a short delay
                    setTimeout(updateStats, 1000);
                } catch (error) {
                    crawlResult.textContent = 'Error: ' + error.message;
                    crawlResult.style.display = 'block';
                } finally {
                    crawlBtn.disabled = false;
                    crawlLoading.style.display = 'none';
                }
            });
            
            // Search content
            document.getElementById('search-btn').addEventListener('click', async () => {
                const searchInput = document.getElementById('search-input');
                const query = searchInput.value.trim();
                
                if (!query) {
                    alert('Please enter a search term');
                    return;
                }
                
                const searchBtn = document.getElementById('search-btn');
                const searchResult = document.getElementById('search-result');
                const searchLoading = document.getElementById('search-loading');
                const resultsContainer = document.getElementById('results-container');
                
                searchBtn.disabled = true;
                searchLoading.style.display = 'block';
                searchResult.style.display = 'none';
                resultsContainer.innerHTML = '';
                
                try {
                    const response = await fetch(`/api/v1/search?q=${encodeURIComponent(query)}`);
                    const results = await response.json();
                    
                    if (results.length === 0) {
                        searchResult.textContent = 'No results found';
                        searchResult.style.display = 'block';
                    } else {
                        searchResult.textContent = `Found ${results.length} result(s)`;
                        searchResult.style.display = 'block';
                        
                        resultsContainer.innerHTML = '<h3>Search Results:</h3>';
                        results.forEach((result, index) => {
                            const resultDiv = document.createElement('div');
                            resultDiv.className = 'result';
                            resultDiv.innerHTML = `
                                <strong>${index + 1}. ${result.title || 'No title'}</strong><br>
                                <small>${result.url}</small><br>
                                <p>${(result.content || '').substring(0, 200)}${(result.content || '').length > 200 ? '...' : ''}</p>
                            `;
                            resultsContainer.appendChild(resultDiv);
                        });
                    }
                } catch (error) {
                    searchResult.textContent = 'Error: ' + error.message;
                    searchResult.style.display = 'block';
                } finally {
                    searchBtn.disabled = false;
                    searchLoading.style.display = 'none';
                }
            });
            
            // Add test page
            document.getElementById('test-page-btn').addEventListener('click', async () => {
                const quickResult = document.getElementById('quick-result');
                const testPageBtn = document.getElementById('test-page-btn');
                
                testPageBtn.disabled = true;
                quickResult.style.display = 'none';
                
                try {
                    const response = await fetch('/api/v1/add-test-page', {
                        method: 'POST'
                    });
                    
                    const result = await response.json();
                    quickResult.textContent = result.message || 'Test page added';
                    quickResult.style.display = 'block';
                    
                    // Update stats
                    setTimeout(updateStats, 1000);
                } catch (error) {
                    quickResult.textContent = 'Error: ' + error.message;
                    quickResult.style.display = 'block';
                } finally {
                    testPageBtn.disabled = false;
                }
            });
            
            // Refresh stats
            document.getElementById('refresh-stats-btn').addEventListener('click', updateStats);
            
            // Enter key to submit forms
            document.getElementById('url-input').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') document.getElementById('crawl-btn').click();
            });
            
            document.getElementById('search-input').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') document.getElementById('search-btn').click();
            });
            
            // Initial stats load
            updateStats();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Status API endpoint (moved from root)
@app.get("/api/v1/status")
async def get_status():
    """Get API status"""
    return {"message": "ScrapAI API Running", "status": "online"}

# FIXED: Use the Pydantic model
@app.post("/api/v1/crawl")
async def crawl_urls(request: CrawlRequest):
    """Add URLs to crawl queue"""
    added_count = 0
    for url in request.urls:
        if await db_client.add_to_queue(url):
            added_count += 1
    stats = await db_client.get_stats()
    return {"message": f"Added {added_count} URLs to queue", "queued": stats["queued"]}

@app.get("/api/v1/stats")
async def get_stats():
    """Get basic stats"""
    return await db_client.get_stats()

@app.get("/api/v1/search")
async def search_content(q: str = "", limit: int = 10):
    """Search content"""
    results = await db_client.search_content(q, limit)
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
    page_id = await db_client.save_page(test_page)
    return {"message": "Test page added", "page_id": page_id}

@app.post("/api/v1/add-page")
async def add_page(page_data: dict):
    """Add a page directly (for testing)"""
    page_id = await db_client.save_page(page_data)
    return {"message": "Page added directly", "page_id": page_id}

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
        
        page_id = await db_client.save_page(page_data)
        return {"message": "Test crawl successful", "page_id": page_id}
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/v1/test-crawl-direct")
async def test_crawl_direct(url: str = "https://httpbin.org/html"):
    """Test crawling directly"""
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
        
        page_id = await db_client.save_page(page_data)
        return {"success": True, "page_id": page_id}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
