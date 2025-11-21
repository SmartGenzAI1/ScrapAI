from fastapi import APIRouter, HTTPException
from typing import List
from backend.database.models import ScrapedPage, CrawlQueue
from backend.database.client import DatabaseClient

router = APIRouter()
db = DatabaseClient()

@router.post("/crawl")
async def add_to_crawl_queue(urls: List[str]):
    """Add URLs to crawl queue"""
    try:
        for url in urls:
            await db.add_to_queue(url)
        return {"message": f"Added {len(urls)} URLs to queue"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_content(query: str, limit: int = 10):
    """Search crawled content"""
    try:
        results = await db.search_content(query, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pages")
async def get_pages(skip: int = 0, limit: int = 50):
    """Get paginated crawled pages"""
    try:
        pages = await db.get_pages(skip, limit)
        return pages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/pages/{page_id}")
async def delete_page(page_id: str):
    """Delete a crawled page"""
    try:
        await db.delete_page(page_id)
        return {"message": "Page deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# Add to backend/api/routes.py

@router.get("/stats")
async def get_stats():
    """Get scraping statistics"""
    try:
        stats = await db.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
