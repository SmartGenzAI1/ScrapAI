import csv
import io
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from backend.database.client import DatabaseClient
from backend.scraper.crawler import SmartCrawler
from workers.pipeline_manager import pipeline_manager

router = APIRouter(prefix="/api/v1")
db = DatabaseClient()
crawler = SmartCrawler(db=db)


# ---------------- Pydantic Request Models ----------------

class CrawlRequest(BaseModel):
    urls: List[str] = Field(..., description="List of URLs to crawl and index")
    priority: int = Field(0, description="Crawl priority (higher values crawled first)")
    depth: int = Field(0, description="Initial crawl depth")
    max_depth: int = Field(2, description="Maximum link traversal depth (0 for single page)")

class DirectCrawlRequest(BaseModel):
    url: str = Field(..., description="Single URL to crawl immediately")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    limit: int = Field(10, description="Maximum number of results to return")
    domain: Optional[str] = Field(None, description="Optional domain filter")

class AnswerRequest(BaseModel):
    query: str = Field(..., description="User question or inquiry")
    limit: int = Field(10, description="Maximum candidate chunks to consider")

class AddPageRequest(BaseModel):
    url: str
    title: Optional[str] = None
    content: str
    meta_description: Optional[str] = None
    author: Optional[str] = None
    hash: Optional[str] = None


# ---------------- API Endpoints ----------------

@router.get("/status")
@router.get("/health")
async def get_status():
    """System health check & operational status"""
    return {
        "status": "online",
        "service": "ScrapAI Platform",
        "version": "2.0-HT",
        "features": {
            "zero_api_semantic_search": True,
            "hybrid_ranking": True,
            "extractive_qa_reasoning": True,
            "autonomous_crawler": True
        }
    }


@router.get("/stats")
async def get_stats():
    """Get system-wide telemetry and performance metrics"""
    try:
        stats = await db.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawl")
async def add_to_crawl_queue(request: CrawlRequest):
    """Add one or more URLs to the ingestion queue"""
    try:
        added_count = 0
        for url in request.urls:
            url_clean = url.strip()
            if not url_clean:
                continue
            if await db.add_to_queue(
                url=url_clean,
                priority=request.priority,
                depth=request.depth,
                max_depth=request.max_depth
            ):
                added_count += 1
                
        stats = await db.get_stats()
        return {
            "success": True,
            "message": f"Added {added_count} URLs to queue ({len(request.urls) - added_count} skipped/duplicates)",
            "added_count": added_count,
            "queued": stats["queued"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawl/direct")
async def crawl_direct(request: DirectCrawlRequest):
    """Crawl a URL synchronously and return extracted content immediately"""
    try:
        result = await crawler.crawl_direct(request.url)
        # Also run a quick pipeline step to chunk & embed immediately
        await pipeline_manager.step_pipeline()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue")
async def get_queue(status: Optional[str] = None, limit: int = 50):
    """List queued targets and their status"""
    try:
        items = await db.get_queue_items(status=status, limit=limit)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/clear")
@router.delete("/queue")
async def clear_queue():
    """Purge all queue entries"""
    try:
        count = await db.clear_queue()
        return {"success": True, "purged_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_content_get(
    q: str = Query("", description="Query string"),
    limit: int = Query(10, description="Max results"),
    domain: Optional[str] = Query(None, description="Domain filter")
):
    """Execute Hybrid Semantic Search (GET)"""
    try:
        results = await db.search_content(q, limit=limit, domain=domain)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_content_post(request: SearchRequest):
    """Execute Hybrid Semantic Search (POST)"""
    try:
        results = await db.search_content(
            query=request.query,
            limit=request.limit,
            domain=request.domain
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/answer")
async def query_and_answer(request: AnswerRequest):
    """
    Extractive QA & Reasoning Engine (No-LLM).
    Returns synthesized answer with source citations `[1]`, `[2]`.
    """
    try:
        result = await db.query_and_answer(request.query, limit=request.limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pages")
async def get_pages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    domain: Optional[str] = Query(None)
):
    """Get paginated indexed pages"""
    try:
        pages = await db.get_pages(skip=skip, limit=limit, domain=domain)
        return pages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pages/{page_id}")
async def get_page_details(page_id: int):
    """Get full details of an indexed page and its chunks"""
    try:
        page = await db.get_page_by_id(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        return page
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/pages/{page_id}")
async def delete_page(page_id: int):
    """Delete an indexed page and all its chunks/vectors"""
    try:
        success = await db.delete_page(page_id)
        if not success:
            raise HTTPException(status_code=404, detail="Page not found")
        return {"success": True, "message": f"Page {page_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-page")
async def add_page(request: AddPageRequest):
    """Manually add or inject a document into the Data Vault"""
    try:
        page_id, is_new = await db.save_page(request.model_dump())
        await pipeline_manager.step_pipeline()
        return {
            "success": True,
            "page_id": page_id,
            "is_new": is_new,
            "message": "Page added and scheduled for embedding"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/run")
async def run_pipeline_step():
    """Trigger an immediate processing step for crawler, chunker, and embedding workers"""
    try:
        stats = await pipeline_manager.step_pipeline()
        return {"success": True, "step_activity": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains")
async def get_domains():
    """Get domain directory & statistics"""
    try:
        return await db.get_domains()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_data(format: str = Query("json", pattern="^(json|csv)$")):
    """Export all indexed data in JSON or CSV format"""
    try:
        pages = await db.get_pages(skip=0, limit=5000)
        if format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["id", "url", "domain", "title", "content", "hash", "crawl_time"])
            writer.writeheader()
            for p in pages:
                writer.writerow({
                    "id": p.get("id"),
                    "url": p.get("url"),
                    "domain": p.get("domain"),
                    "title": p.get("title"),
                    "content": p.get("content"),
                    "hash": p.get("hash"),
                    "crawl_time": p.get("crawl_time")
                })
            return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=scrapai_export.csv"})
        return pages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_database():
    """Purge all pages, chunks, embeddings, and queue (Admin)"""
    try:
        success = await db.reset_all()
        return {"success": success, "message": "Database successfully purged."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
