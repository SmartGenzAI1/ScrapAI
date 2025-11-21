from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Remove these problematic imports:
# from backend.api.routes import router
# from backend.database.client import DatabaseClient

# Create routes directly in main.py instead:
app = FastAPI(title="ScrapAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage
queue = []
pages = []

@app.get("/")
async def root():
    return {"message": "ScrapAI API Running", "status": "online"}

@app.post("/api/v1/crawl")
async def crawl_urls(urls: list):
    """Add URLs to crawl queue"""
    for url in urls:
        if url not in queue:
            queue.append({"url": url, "status": "queued"})
    return {"message": f"Added {len(urls)} URLs to queue", "queued": len(queue)}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
